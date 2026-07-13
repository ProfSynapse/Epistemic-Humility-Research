#!/usr/bin/env python3
"""Amendment Q — pre-flight engine-faithfulness smoke (lab-notebook, NOT verdict-bearing).

Before training the aux_head, confirm that a live forward over the frozen merged
grpo-v2 base reproduces the cached extraction representation O/P used — i.e. that
we can read the SAME L35 answerability axis the offline probe read (KUQ in-dist
5-fold CV AUROC ~0.964, per Amendment P).

The open question (surfaced while wiring the engine): the extraction's
`final_prompt_token` rule renders with `add_generation_prompt=True`, so the prompt
ends at `...<|im_start|>assistant\\n<think>\\n\\n</think>\\n\\n`; the engine's SFT
preprocessing renders prompt-only rows with `add_generation_prompt=False`, ending
at the user turn's `<|im_end|>\\n`. These are DIFFERENT tokens. This smoke measures
CV-AUROC at both candidate tokens against the cached ground truth to decide which
token position faithfully reproduces the axis.

Outputs three numbers per source:
  (0) cached extraction L35 vectors           -> ground truth (~0.964 expected)
  (i) live forward, add_generation_prompt=True, last real token (gen-prompt token)
  (ii) live forward, add_generation_prompt=False, last real token (end-of-user)
plus cosine/MSE of (i),(ii) vs cached, to confirm bit-level reproduction.

CPU/GPU: loads the 4B base; runs on cuda if available. Reuses the engine's
`reduce_hidden_states` for the token reduction (the real engine reduce path).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from safetensors.torch import load_file
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from path_compat import repo_root  # noqa: E402

REPO = repo_root()
# engine reduce path (the real one the trainer uses)
sys.path.insert(0, str(REPO / "synaptic-tuner" / "Trainers" / "sft" / "src"))
from aux_head import reduce_hidden_states  # noqa: E402

SYS_PROMPT = "You are a helpful assistant. Answer the question concisely."
LAYER = 35
KUQ_DIR = (
    REPO
    / "experiment/phase1/probe/qwen3-4b-clean-sft-grpo-v2-seed1-kuq"
    / "hidden_states_kuq_clean_sft_grpo_v2_full/extraction__cfdf25500cf3"
)
BASE = (
    REPO
    / "scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full"
    / "20260624_095831/Qwen3-4B-clean-sft-grpo-v2/merged-16bit"
)


def cv_auroc(X: np.ndarray, y: np.ndarray, seed: int = 20260629) -> float:
    p = np.full(len(y), np.nan)
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    for tr, te in skf.split(X, y):
        sc = StandardScaler().fit(X[tr])
        clf = LogisticRegression(C=1.0, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
        p[te] = clf.predict_proba(sc.transform(X[te]))[:, 1]
    return float(roc_auc_score(y, p))


def load_cached(ext_dir: Path, source: str = "h_lora"):
    rows = [json.loads(l) for l in (ext_dir / "rows.jsonl").open(encoding="utf-8") if l.strip()]
    X, y, keep = [], [], []
    lname = f"L{LAYER}"
    for r in rows:
        label = str(r.get("label", "")).lower()
        if label not in ("known", "unknown"):
            continue
        safe = str(r["probe_pool_row_key"]).replace("::", "__").replace("|", "_")
        shard = ext_dir / f"{safe}__{source}.safetensors"
        if not shard.exists():
            continue
        t = load_file(str(shard))
        X.append(np.asarray(t[lname], dtype=np.float64))
        y.append(1 if label == "known" else 0)
        keep.append(r)
    return np.vstack(X), np.asarray(y, dtype=int), keep


@torch.no_grad()
def forward_vectors(rows, tok, model, add_gen_prompt: bool, batch_size: int = 16):
    vecs = []
    device = next(model.parameters()).device
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        texts = [
            tok.apply_chat_template(
                [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": r["question"]}],
                tokenize=False,
                add_generation_prompt=add_gen_prompt,
                enable_thinking=False,
            )
            for r in batch
        ]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(device)
        out = model(**enc, output_hidden_states=True)
        h = out.hidden_states[LAYER]  # [B, seq, hidden]
        reduced = reduce_hidden_states(h.float(), enc["attention_mask"], token_position="last")
        vecs.append(reduced.cpu().numpy().astype(np.float64))
        print(f"  forward {min(i + batch_size, len(rows))}/{len(rows)}", end="\r", flush=True)
    print()
    return np.vstack(vecs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="cap rows for a quick check (0 = all)")
    ap.add_argument("--source", default="h_lora", choices=["h_base", "h_lora"])
    a = ap.parse_args()

    print(f"[smoke] cached ground-truth source={a.source}, layer L{LAYER}")
    Xc, y, rows = load_cached(KUQ_DIR, a.source)
    if a.limit:
        Xc, y, rows = Xc[: a.limit], y[: a.limit], rows[: a.limit]
    print(f"[smoke] n={len(y)} (known={int((y==1).sum())}, unknown={int((y==0).sum())})")
    auroc_cached = cv_auroc(Xc, y)
    print(f"[smoke] (0) cached extraction CV AUROC = {auroc_cached:.4f}  (expect ~0.964)")

    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"[smoke] loading base {BASE.name} ...")
    tok = AutoTokenizer.from_pretrained(str(BASE))
    tok.padding_side = "right"
    model = AutoModelForCausalLM.from_pretrained(
        str(BASE), torch_dtype=torch.bfloat16, device_map="cuda" if torch.cuda.is_available() else "cpu"
    ).eval()

    print("[smoke] (i) forward add_generation_prompt=True (gen-prompt token) ...")
    Xi = forward_vectors(rows, tok, model, add_gen_prompt=True)
    auroc_i = cv_auroc(Xi, y)

    print("[smoke] (ii) forward add_generation_prompt=False (end-of-user token) ...")
    Xii = forward_vectors(rows, tok, model, add_gen_prompt=False)
    auroc_ii = cv_auroc(Xii, y)

    def cos_mse(A, B):
        an = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-8)
        bn = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-8)
        return float((an * bn).sum(1).mean()), float(((A - B) ** 2).mean())

    cos_i, mse_i = cos_mse(Xi, Xc)
    cos_ii, mse_ii = cos_mse(Xii, Xc)

    print("\n==================== SMOKE RESULT ====================")
    print(f"(0)  cached extraction L35 CV AUROC      = {auroc_cached:.4f}")
    print(f"(i)  live add_gen_prompt=True  CV AUROC  = {auroc_i:.4f}  | cos_vs_cached={cos_i:.4f} mse={mse_i:.3f}")
    print(f"(ii) live add_gen_prompt=False CV AUROC  = {auroc_ii:.4f}  | cos_vs_cached={cos_ii:.4f} mse={mse_ii:.3f}")
    print("======================================================")
    print("Decision: the token whose live AUROC ~matches (0) and cos_vs_cached~1.0 is the")
    print("faithful one to train the head on. If (i) matches and (ii) does not, the engine")
    print("needs a generation-prompt-aware token position (Phase-B-relevant finding).")


if __name__ == "__main__":
    main()
