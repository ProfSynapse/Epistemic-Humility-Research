#!/usr/bin/env python3
"""GPU equivalence cell for batched final-position + per-element-alpha steering.

===========================================================================
!!! DO NOT RUN WITHOUT EXPLICIT USER LAUNCH APPROVAL !!!

This script LOADS THE REAL CHECKPOINT ONTO THE GPU and runs forward passes.
It must NOT be executed as part of any CPU task, CI run, or automated sweep.
A signed Tier-2 amendment (Amendment AK Stage 2) plus explicit user approval
naming the checkpoint and GPU lane is required before launch. The GPU on this
box may be occupied by a training arm; confirm it is free first.

Prepared for TODO item 11 (batched steering engine parity) as the GPU half's
runner. The CPU half is proven by
tests/test_arm_b_batched_parity.py — this cell confirms the same equivalence
holds on the real model's true layer geometry and real padding.
===========================================================================

What it checks
--------------
On a handful of real prompts, at the direction's `best_layer`, it compares the
NEW batched SteeringHook edit against a one-prompt-at-a-time reference:

  (A) BATCHED: tokenize all prompts together (padded), one forward, hook in
      position="final" with a per-row attention mask and a per-row alpha
      vector -> capture the edited layer output at each row's last real token.

  (B) UNBATCHED: tokenize each prompt alone (no padding), one forward per
      prompt, hook in position="final" (single row) with that row's scalar
      alpha -> capture the edited layer output at the last token.

It reports the max abs divergence between the steered hidden states from (A)
and (B) at each row's final real token. Padding/masking correctness means the
batched final-position edit lands on the same token content the unbatched pass
edits, so divergence should be at the model's own batched-vs-unbatched numeric
floor (typically < ~1e-2 in bf16, far below any steering magnitude).

It also spot-checks per-element alpha by giving each row a distinct alpha and
verifying the batched edit reproduces each row's unbatched scalar-alpha edit.

Usage (ONLY after approval)
---------------------------
  python gpu_equivalence_cell.py \
      --model <checkpoint> \
      --direction directions/<tag>/direction_gate.json \
      --device cuda --dtype bfloat16
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

STEERING_DIR = Path(__file__).resolve().parent
if str(STEERING_DIR) not in sys.path:
    sys.path.insert(0, str(STEERING_DIR))

from confidence_steer import (  # noqa: E402
    SteeringHook,
    get_decoder_layer,
    load_direction,
    load_model_and_tokenizer,
)
from steering_common import SYSTEM_PROMPT, build_initial_messages  # noqa: E402

# A few fixed probe prompts (answerable + unknowable mix). Kept tiny on purpose.
DEFAULT_QUESTIONS = [
    "What is the capital of France?",
    "Who wrote the novel Pride and Prejudice?",
    "What will the closing price of a randomly chosen stock be next Tuesday?",
    "What is the chemical symbol for gold?",
    "How many moons does the planet Mars have?",
]


class _Capture:
    """Forward hook that records the (already steered) layer output tensor."""

    def __init__(self) -> None:
        self.hidden = None

    def __call__(self, module, inp, output):
        h = output[0] if isinstance(output, tuple) else output
        self.hidden = h.detach().float().cpu()
        return output


def _render(tokenizer, question: str) -> str:
    return tokenizer.apply_chat_template(
        build_initial_messages(question, SYSTEM_PROMPT),
        tokenize=False, add_generation_prompt=True, enable_thinking=False)


def _last_real_indices(attn):
    import torch
    am = attn.to(torch.bool)
    seq = am.shape[1]
    last_from_right = torch.argmax(torch.flip(am.to(torch.int64), dims=[1]),
                                   dim=1)
    return (seq - 1) - last_from_right


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--direction", required=True, type=Path)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--alpha-base", type=float, default=4.0)
    ap.add_argument("--i-know-this-runs-on-gpu", action="store_true",
                    help="Required acknowledgement that this loads a model on "
                         "the GPU. Refuses to run without it.")
    a = ap.parse_args(argv)

    if not a.i_know_this_runs_on_gpu:
        print("REFUSING TO RUN: this cell loads the real checkpoint on the "
              "GPU. Pass --i-know-this-runs-on-gpu only under explicit user "
              "launch approval (see the module docstring).", flush=True)
        return 2

    import torch

    d_np, meta = load_direction(a.direction)
    layer_idx = meta["best_layer"]
    print(f"[gpu-equiv] direction layer={layer_idx} model={a.model}", flush=True)

    model, tokenizer = load_model_and_tokenizer(a.model, device=a.device)
    device = next(model.parameters()).device
    d = torch.from_numpy(d_np).to(device)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    questions = DEFAULT_QUESTIONS
    prompts = [_render(tokenizer, q) for q in questions]
    # Per-row alphas: distinct so per-element broadcasting is exercised.
    alphas = [a.alpha_base * (1.0 + 0.25 * i) for i in range(len(prompts))]

    layer = get_decoder_layer(model, layer_idx)

    # ---- (A) BATCHED: one padded forward, position="final", per-row alpha ----
    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    attn = enc["attention_mask"]
    final_idx = _last_real_indices(attn)
    steer = SteeringHook(d=d, alpha=alphas, position="final",
                         attention_mask=attn)
    cap = _Capture()
    h_steer = layer.register_forward_hook(steer)
    h_cap = layer.register_forward_hook(cap)   # runs AFTER steer (edited output)
    with torch.no_grad():
        model(**enc)
    h_steer.remove()
    h_cap.remove()
    batched_final = torch.stack([cap.hidden[b, final_idx[b].item(), :]
                                 for b in range(len(prompts))])

    # ---- (B) UNBATCHED: one forward per prompt, scalar alpha, last token ----
    unbatched_final = []
    for i, prompt in enumerate(prompts):
        enc1 = tokenizer(prompt, return_tensors="pt").to(device)
        steer1 = SteeringHook(d=d, alpha=float(alphas[i]), position="final",
                              attention_mask=enc1["attention_mask"])
        cap1 = _Capture()
        hs = layer.register_forward_hook(steer1)
        hc = layer.register_forward_hook(cap1)
        with torch.no_grad():
            model(**enc1)
        hs.remove()
        hc.remove()
        last = _last_real_indices(enc1["attention_mask"])[0].item()
        unbatched_final.append(cap1.hidden[0, last, :])
    unbatched_final = torch.stack(unbatched_final)

    diff = (batched_final - unbatched_final).abs()
    per_row = diff.amax(dim=1).numpy()
    max_abs = float(diff.max().item())
    print("[gpu-equiv] per-row max abs divergence at final real token:",
          np.round(per_row, 6).tolist(), flush=True)
    print(f"[gpu-equiv] OVERALL max abs divergence = {max_abs:.6e}", flush=True)
    print("[gpu-equiv] (expected: model's batched-vs-unbatched numeric floor, "
          "orders of magnitude below the steering magnitude)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
