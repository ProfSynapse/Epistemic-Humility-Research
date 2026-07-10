#!/usr/bin/env python3
"""Amendment R — Phase B token-position OFFSET diagnostic (lab-notebook).

The Phase B smoke found the engine's `end_of_prompt` (token before the first
unmasked completion token) reads cos 0.55 / AUROC 0.89 vs the cached faithful axis
(0.964) — it lands one-or-more tokens short of the generation-anchor token Q
validated. This pins the exact offset so the fix is unambiguous.

For a subset of KUQ rows, run the SAME full-sequence preprocessing forward and read
L35 at boundary+{0,1,2,3}; ALSO run a prompt-only `add_generation_prompt=True`
forward and read its last token (Q's faithful gen-prompt token). Report cos-to-cached
+ CV AUROC for each. The position whose cos ~1.0 / AUROC ~0.964 is the target; its
offset from `boundary` is the fix the engine/data rendering must apply.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

from path_compat import repo_root  # noqa: E402

REPO = repo_root()
sys.path.insert(0, str(REPO / "synaptic-tuner" / "Trainers" / "sft" / "src"))
sys.path.insert(0, str(REPO / "synaptic-tuner"))
from aux_head import prompt_end_indices  # noqa: E402
from preprocessing import prepare_sft_dataset  # noqa: E402

# reuse the smoke's loaders/constants
from amendment_r_phase_b_smoke import (  # noqa: E402
    BASE,
    LAYER,
    SYS_PROMPT,
    build_dataset,
    cos_mse,
    cv_auroc,
    load_cached,
    pad_batch,
    KUQ_DIR,
)


@torch.no_grad()
def diag(prepared, rows, tok, model, batch_size=16):
    device = next(model.parameters()).device
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    offsets = [0, 1, 2, 3]
    off_vecs = {o: [] for o in offsets}
    gen_vecs = []
    n = len(prepared)
    for i in range(0, n, batch_size):
        batch = [prepared[j] for j in range(i, min(i + batch_size, n))]
        ids, attn, labels = pad_batch(batch, pad_id, device)
        h = model(input_ids=ids, attention_mask=attn, output_hidden_states=True).hidden_states[LAYER].float()
        peidx = prompt_end_indices(labels, attn)
        last_real = (attn.long().sum(1) - 1).clamp_min(0)
        ar = torch.arange(ids.size(0), device=device)
        for o in offsets:
            idx = (peidx + o).clamp_max(last_real)
            off_vecs[o].append(h[ar, idx].cpu().numpy().astype(np.float64))
        # prompt-only gen-prompt token (Q faithful) for the same questions
        qbatch = rows[i : i + batch_size]
        texts = [
            tok.apply_chat_template(
                [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": r["question"]}],
                tokenize=False, add_generation_prompt=True, enable_thinking=False,
            )
            for r in qbatch
        ]
        enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(device)
        hg = model(**enc, output_hidden_states=True).hidden_states[LAYER].float()
        gl = (enc["attention_mask"].long().sum(1) - 1).clamp_min(0)
        gen_vecs.append(hg[torch.arange(hg.size(0), device=device), gl].cpu().numpy().astype(np.float64))
        print(f"  {min(i + batch_size, n)}/{n}", end="\r", flush=True)
    print()
    return {o: np.vstack(v) for o, v in off_vecs.items()}, np.vstack(gen_vecs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--source", default="h_lora")
    a = ap.parse_args()

    Xc, y, rows = load_cached(KUQ_DIR, a.source)
    if a.limit:
        Xc, y, rows = Xc[: a.limit], y[: a.limit], rows[: a.limit]
    print(f"[diag] n={len(y)}  cached CV AUROC = {cv_auroc(Xc, y):.4f}")

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(BASE)); tok.padding_side = "right"
    model = AutoModelForCausalLM.from_pretrained(
        str(BASE), dtype=torch.bfloat16, device_map="cuda" if torch.cuda.is_available() else "cpu"
    ).eval()

    ds = build_dataset(rows)
    prepared = prepare_sft_dataset(ds, tokenizer=tok, max_seq_length=2048,
                                   loss_mask_mode="assistant_only", aux_target_field="aux_target")
    off_vecs, gen = diag(prepared, rows, tok, model)

    print("\n==================== OFFSET DIAGNOSTIC ====================")
    for o in sorted(off_vecs):
        cos, mse = cos_mse(off_vecs[o], Xc)
        print(f"end_of_prompt + {o} : CV AUROC={cv_auroc(off_vecs[o], y):.4f}  cos_vs_cached={cos:.4f}  mse={mse:.2f}")
    cosg, mseg = cos_mse(gen, Xc)
    print(f"gen-prompt token   : CV AUROC={cv_auroc(gen, y):.4f}  cos_vs_cached={cosg:.4f}  mse={mseg:.2f}  (Q faithful, expect ~0.96/~1.0)")
    print("===========================================================")
    print("FIX = the smallest offset whose cos~1.0 matches the gen-prompt token.")


if __name__ == "__main__":
    main()
