#!/usr/bin/env python3
"""Amendment R — Phase B pre-flight engine smoke (lab-notebook, NOT verdict-bearing).

The novel risk Phase B introduces over Amendment Q: Q validated the answerability
axis at the *generation-prompt* token on **prompt-only** rows (cos 0.9998 to the
cached extraction, CV AUROC ~0.9645). Phase B instead reads `token_position=
"end_of_prompt"` on **prompt+completion** SFT rows, recovering the boundary from the
labels -100 mask via the engine's `prompt_end_indices`. The open question: does that
labels-derived boundary land on the SAME faithful token (Q's `</think>` position,
cos ~1.0) or on the weak end-of-user token (cos ~0.54)?

This smoke routes real rows through the EXACT trainer preprocessing
(`prepare_sft_dataset`, assistant_only masking, aux_target threading), forwards the
merged grpo-v2 base, and reduces at `end_of_prompt` with the engine's real reduce
path. It reports, vs the cached extraction ground truth:

  (0)  cached extraction L35 h_lora            -> ground truth (~0.964 expected)
  (A)  end_of_prompt on prompt+completion rows -> CV AUROC, cos/mse vs cached,
       and the DECODED boundary token (diagnostic: which token did it land on?)
  (B)  "last" (completion-end) on the same rows -> contrast; shows why end_of_prompt
       is needed (post-answer state should be a different, weaker axis)

It also exercises the aux_target threading (`aux_target_field="aux_target"`) so the
target-plumbing path is smoke-covered end to end.

GREEN decision: (A) CV AUROC ~matches (0) and cos_vs_cached ~1.0 -> Phase B reads the
faithful token; proceed. If (A) is weak, that is a plumbing finding to FIX before the
scored A0/A1/A2 run (faithfulness clause: do not burn the falsifier on a token bug).

CPU/GPU: loads the 4B base; uses cuda if available.
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
SFT_SRC = REPO / "synaptic-tuner" / "Trainers" / "sft" / "src"
TUNER_ROOT = REPO / "synaptic-tuner"  # `shared` package lives at the submodule root
sys.path.insert(0, str(SFT_SRC))
sys.path.insert(0, str(TUNER_ROOT))  # for `shared.sft_preprocessing`
from aux_head import prompt_end_indices, reduce_hidden_states  # noqa: E402
from preprocessing import prepare_sft_dataset  # noqa: E402

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
# Phase-B-style completions. Content is irrelevant to the end_of_prompt extraction
# (it sits BEFORE the completion); we only need a real assistant turn so the row is
# prompt+completion and the labels mask creates a genuine boundary.
COMPLETION_KNOWN = "The answer is well established."
COMPLETION_UNKNOWN = "I don't know."


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


def build_dataset(rows):
    from datasets import Dataset

    recs = []
    for r in rows:
        known = str(r.get("label", "")).lower() == "known"
        recs.append(
            {
                "messages": [
                    {"role": "system", "content": SYS_PROMPT},
                    {"role": "user", "content": r["question"]},
                    {"role": "assistant", "content": COMPLETION_KNOWN if known else COMPLETION_UNKNOWN},
                ],
                "aux_target": 1.0 if known else 0.0,
            }
        )
    return Dataset.from_list(recs)


def pad_batch(batch, pad_id, device):
    maxlen = max(len(b["input_ids"]) for b in batch)
    ids, attn, labels = [], [], []
    for b in batch:
        n = len(b["input_ids"])
        pad = maxlen - n
        ids.append(list(b["input_ids"]) + [pad_id] * pad)
        attn.append(list(b["attention_mask"]) + [0] * pad)
        labels.append(list(b["labels"]) + [-100] * pad)  # right-pad to match engine reduce
    return (
        torch.tensor(ids, device=device),
        torch.tensor(attn, device=device),
        torch.tensor(labels, device=device),
    )


@torch.no_grad()
def forward_reduce(prepared, tok, model, batch_size: int = 16):
    """Return (end_of_prompt_vecs, last_vecs, boundary_token_strings)."""
    device = next(model.parameters()).device
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    eop_vecs, last_vecs, boundary_toks = [], [], []
    n = len(prepared)
    for i in range(0, n, batch_size):
        batch = [prepared[j] for j in range(i, min(i + batch_size, n))]
        ids, attn, labels = pad_batch(batch, pad_id, device)
        out = model(input_ids=ids, attention_mask=attn, output_hidden_states=True)
        h = out.hidden_states[LAYER].float()  # [B, seq, hidden]
        peidx = prompt_end_indices(labels, attn)
        eop = reduce_hidden_states(h, attn, token_position="end_of_prompt", prompt_end_idx=peidx)
        last = reduce_hidden_states(h, attn, token_position="last")
        eop_vecs.append(eop.cpu().numpy().astype(np.float64))
        last_vecs.append(last.cpu().numpy().astype(np.float64))
        for row_i in range(ids.size(0)):
            boundary_toks.append(tok.decode([int(ids[row_i, int(peidx[row_i])])]))
        print(f"  forward {min(i + batch_size, n)}/{n}", end="\r", flush=True)
    print()
    return np.vstack(eop_vecs), np.vstack(last_vecs), boundary_toks


def cos_mse(A, B):
    an = A / (np.linalg.norm(A, axis=1, keepdims=True) + 1e-8)
    bn = B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-8)
    return float((an * bn).sum(1).mean()), float(((A - B) ** 2).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400, help="cap rows for speed (0 = all 1000)")
    ap.add_argument("--source", default="h_lora", choices=["h_base", "h_lora"])
    ap.add_argument("--max-seq-length", type=int, default=2048)
    ap.add_argument(
        "--prompt-render",
        default="full_conversation",
        choices=["full_conversation", "prompt_completion"],
        help="Engine render mode threaded into prepare_sft_dataset. "
        "prompt_completion (PR #120) makes end_of_prompt land on the faithful "
        "gen-prompt token; full_conversation is the original cos-0.55 path.",
    )
    ap.add_argument(
        "--enable-thinking",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Forwarded as chat_template_kwargs.enable_thinking. MUST be False to "
        "match the cached extraction (manifest enable_thinking=false) and the "
        "A0/A1/A2 recipes; True lands end_of_prompt one anchor early (false RED).",
    )
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

    # MUST match the cached extraction's render (manifest: enable_thinking=false) AND
    # the A0/A1/A2 recipes (chat_template_kwargs.enable_thinking: false). With Qwen3,
    # enable_thinking=False injects an empty "<think>\n\n</think>\n\n" block into the
    # add_generation_prompt render, so end_of_prompt lands on the '\n\n' AFTER </think>
    # — the cached final_prompt_token. Omitting this (template default thinking=ON)
    # lands one anchor early on the post-"assistant" '\n' and reads a DIFFERENT axis.
    ctk = {"enable_thinking": a.enable_thinking}
    print(
        f"[smoke] preprocessing rows through prepare_sft_dataset "
        f"(prompt_render={a.prompt_render}, chat_template_kwargs={ctk}) ..."
    )
    ds = build_dataset(rows)
    prepared = prepare_sft_dataset(
        ds,
        tokenizer=tok,
        max_seq_length=a.max_seq_length,
        loss_mask_mode="assistant_only",
        aux_target_field="aux_target",
        prompt_render=a.prompt_render,
        chat_template_kwargs=ctk,
    )
    # sanity: target threading survived
    tgt = np.asarray([prepared[i]["aux_target"] for i in range(len(prepared))], dtype=float)
    assert set(np.unique(tgt)) <= {0.0, 1.0} and np.allclose(tgt, y), "aux_target threading mismatch"
    print(f"[smoke] aux_target threaded OK (matches known/unknown labels, n={len(tgt)})")

    print("[smoke] (A) end_of_prompt + (B) last, live forward ...")
    Xa, Xb, btoks = forward_reduce(prepared, tok, model)
    auroc_a = cv_auroc(Xa, y)
    auroc_b = cv_auroc(Xb, y)
    cos_a, mse_a = cos_mse(Xa, Xc)
    cos_b, mse_b = cos_mse(Xb, Xc)

    # boundary-token diagnostic
    from collections import Counter

    btok_counts = Counter(repr(t) for t in btoks).most_common(5)

    print("\n==================== PHASE B SMOKE RESULT ====================")
    print(f"(0)  cached extraction L35 CV AUROC          = {auroc_cached:.4f}")
    print(f"(A)  end_of_prompt CV AUROC                  = {auroc_a:.4f}  | cos_vs_cached={cos_a:.4f} mse={mse_a:.3f}")
    print(f"(B)  last (completion-end) CV AUROC          = {auroc_b:.4f}  | cos_vs_cached={cos_b:.4f} mse={mse_b:.3f}")
    print(f"     boundary token landed on (top 5)        = {btok_counts}")
    print("==============================================================")
    faithful = (auroc_a >= auroc_cached - 0.03) and (cos_a >= 0.95)
    if faithful:
        print("VERDICT: GREEN — end_of_prompt reproduces the Q axis on prompt+completion rows.")
        print("Phase B reads the faithful token; the scored A0/A1/A2 run is unblocked on this gate.")
    else:
        print("VERDICT: NOT GREEN — end_of_prompt does NOT reproduce the axis.")
        print("This is a plumbing finding to FIX before the scored run (per the faithfulness clause).")
        print("Inspect the boundary token above: if it is an end-of-user token, the assistant_only")
        print("mask is excluding the generation-prompt/think span from the completion.")

    out = {
        "n": len(y),
        "source": a.source,
        "prompt_render": a.prompt_render,
        "enable_thinking": a.enable_thinking,
        "auroc_cached": auroc_cached,
        "auroc_end_of_prompt": auroc_a,
        "auroc_last": auroc_b,
        "cos_eop_vs_cached": cos_a,
        "cos_last_vs_cached": cos_b,
        "boundary_token_top5": btok_counts,
        "faithful_green": bool(faithful),
    }
    outdir = REPO / "scratch" / "amendment_r"
    outdir.mkdir(parents=True, exist_ok=True)
    outpath = outdir / f"phase_b_smoke_{a.source}_{a.prompt_render}.json"
    outpath.write_text(json.dumps(out, indent=2))
    print(f"[smoke] wrote {outpath}")


if __name__ == "__main__":
    main()
