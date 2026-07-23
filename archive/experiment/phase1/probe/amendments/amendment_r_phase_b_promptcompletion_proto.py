#!/usr/bin/env python3
"""Amendment R — Phase B prompt/completion tokenization PROTOTYPE (lab-notebook).

The smoke + offset diag showed the engine's `end_of_prompt` (derived from the
full-conversation render's labels mask) reads cos 0.55 / AUROC 0.85 — NOT the
validated answerability axis (0.964) — because the full-conversation assistant-turn
render diverges from `add_generation_prompt=True` at the `</think>` newlines, so the
faithful gen-prompt token has no clean position in the row.

This prototype tests the proposed FIX: tokenize SFT rows prompt/completion-style ---
    input_ids = render(messages_without_assistant, add_generation_prompt=True)
                ++ completion_ids ++ <|im_end|>
    labels    = [-100] * len(prompt) ++ completion_ids ++ <|im_end|>
--- so the prompt segment ends EXACTLY at the gen-prompt token and the engine's
`end_of_prompt` (= last prompt token, via the same `prompt_end_indices` helper) lands
on it. By causal-attention prefix identity this should reproduce cos ~1.0 / AUROC
~0.96. A fixed, label-independent completion is used for every row (zero leakage; the
read is BEFORE the completion anyway).

If GREEN, the builder addendum prescribes prompt/completion tokenization as the
faithful Phase-B preprocessing mode.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

from path_compat import repo_root  # noqa: E402

REPO = repo_root()
sys.path.insert(0, str(REPO / "synaptic-tuner" / "Trainers" / "sft" / "src"))
sys.path.insert(0, str(REPO / "synaptic-tuner"))
from aux_head import prompt_end_indices, reduce_hidden_states  # noqa: E402

from amendment_r_phase_b_smoke import (  # noqa: E402
    BASE, KUQ_DIR, LAYER, SYS_PROMPT, cos_mse, cv_auroc, load_cached,
)

FIXED_COMPLETION = "Yes."  # label-independent; the read is before the completion


def build_prompt_completion_rows(rows, tok):
    """prompt(add_generation_prompt=True) ++ fixed completion ++ <|im_end|>."""
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    comp_ids = tok.encode(FIXED_COMPLETION, add_special_tokens=False) + [im_end]
    out = []
    for r in rows:
        prompt_text = tok.apply_chat_template(
            [{"role": "system", "content": SYS_PROMPT}, {"role": "user", "content": r["question"]}],
            tokenize=False, add_generation_prompt=True, enable_thinking=False,
        )
        prompt_ids = tok.encode(prompt_text, add_special_tokens=False)
        ids = list(prompt_ids) + list(comp_ids)
        labels = [-100] * len(prompt_ids) + list(comp_ids)
        out.append({"input_ids": ids, "attention_mask": [1] * len(ids), "labels": labels,
                    "prompt_len": len(prompt_ids)})
    return out


def pad_batch(batch, pad_id, device):
    maxlen = max(len(b["input_ids"]) for b in batch)
    ids, attn, labels = [], [], []
    for b in batch:
        pad = maxlen - len(b["input_ids"])
        ids.append(b["input_ids"] + [pad_id] * pad)
        attn.append(b["attention_mask"] + [0] * pad)
        labels.append(b["labels"] + [-100] * pad)
    return (torch.tensor(ids, device=device), torch.tensor(attn, device=device),
            torch.tensor(labels, device=device))


@torch.no_grad()
def forward_eop(prepared, tok, model, batch_size=16):
    device = next(model.parameters()).device
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    vecs, boundary_ok = [], 0
    n = len(prepared)
    for i in range(0, n, batch_size):
        batch = prepared[i : i + batch_size]
        ids, attn, labels = pad_batch(batch, pad_id, device)
        h = model(input_ids=ids, attention_mask=attn, output_hidden_states=True).hidden_states[LAYER].float()
        peidx = prompt_end_indices(labels, attn)
        # verify the engine boundary == last prompt token (prompt_len - 1)
        for k, b in enumerate(batch):
            boundary_ok += int(int(peidx[k]) == b["prompt_len"] - 1)
        eop = reduce_hidden_states(h, attn, token_position="end_of_prompt", prompt_end_idx=peidx)
        vecs.append(eop.cpu().numpy().astype(np.float64))
        print(f"  {min(i + batch_size, n)}/{n}", end="\r", flush=True)
    print()
    return np.vstack(vecs), boundary_ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--source", default="h_lora")
    a = ap.parse_args()

    Xc, y, rows = load_cached(KUQ_DIR, a.source)
    if a.limit:
        Xc, y, rows = Xc[: a.limit], y[: a.limit], rows[: a.limit]
    print(f"[proto] n={len(y)}  cached CV AUROC = {cv_auroc(Xc, y):.4f}")

    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(BASE)); tok.padding_side = "right"
    model = AutoModelForCausalLM.from_pretrained(
        str(BASE), dtype=torch.bfloat16, device_map="cuda" if torch.cuda.is_available() else "cpu"
    ).eval()

    prepared = build_prompt_completion_rows(rows, tok)
    X, boundary_ok = forward_eop(prepared, tok, model)
    auroc = cv_auroc(X, y)
    cos, mse = cos_mse(X, Xc)

    print("\n============ PROMPT/COMPLETION PROTOTYPE RESULT ============")
    print(f"end_of_prompt boundary == last prompt token : {boundary_ok}/{len(prepared)} rows")
    print(f"end_of_prompt CV AUROC                       : {auroc:.4f}  (cached {cv_auroc(Xc, y):.4f})")
    print(f"cos_vs_cached                                : {cos:.4f}   mse={mse:.3f}")
    print("============================================================")
    green = (auroc >= cv_auroc(Xc, y) - 0.03) and (cos >= 0.95)
    print("VERDICT:", "GREEN — prompt/completion tokenization makes end_of_prompt faithful."
          if green else "NOT GREEN — investigate further.")


if __name__ == "__main__":
    main()
