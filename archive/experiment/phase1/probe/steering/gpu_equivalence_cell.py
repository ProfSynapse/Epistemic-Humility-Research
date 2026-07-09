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
On a handful of real prompts, at the direction's `best_layer`, it verifies that
the NEW batched SteeringHook applies EXACTLY ``alpha_i * d`` at each row's true
last non-pad token. The key is that we compare the STEERING DELTA (steered minus
unsteered), not the absolute steered hidden states:

  For each of the batched (A) and unbatched (B) passes we run the layer TWICE at
  the direction's best_layer -- once with the SteeringHook, once without -- and
  take the difference at each row's final real token. That difference is the
  edit the hook applied and NOTHING else: the model's own forward numerics
  cancel out. We then check two things:

    delta_batched   ~= alpha_i * d      (the hook did exactly what it promised)
    delta_batched   ~= delta_unbatched  (batched == one-prompt-at-a-time)

Why the delta and not the absolute hidden state
-----------------------------------------------
A padded batched forward and an unpadded single-prompt forward are NOT
bit-identical in bf16, even with correct masking: the attention softmax runs
over a longer (padded) key set, RoPE position offsets differ, and float
reduction order changes. At a deep layer of a multi-billion-parameter model the
residual-stream magnitude is large (O(10-100)), so this legitimate
batched-vs-unbatched numeric noise is INTEGER-scale in bf16 -- it has nothing to
do with the steering edit and would swamp any absolute-hidden-state comparison
(the r1 run of this cell mis-fired exactly this way: it compared absolute steered
states and reported 1-6 units of "divergence" that were entirely the model's
bf16 batched-vs-unbatched noise, not a steering bug). Subtracting the unsteered
pass removes that shared noise and isolates the hook's edit, so the floor can
stay tight (~1e-2) and actually mean something.

Usage (ONLY after approval)
---------------------------
  python gpu_equivalence_cell.py \
      --model <checkpoint> \
      --direction directions/<tag>/direction_gate.json \
      --device cuda --dtype bfloat16
"""
from __future__ import annotations

import argparse
import math
import json
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
    ap.add_argument("--adapter", default=None,
                    help="Optional PEFT LoRA adapter repo/path applied on top of "
                         "--model (deployed clean-SFT->GRPO-v2 lineage).")
    ap.add_argument("--adapter-revision", default=None,
                    help="Pinned revision for --adapter.")
    ap.add_argument("--direction", required=True, type=Path)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--alpha-base", type=float, default=4.0)
    ap.add_argument("--floor", type=float, default=1e-2,
                    help="Legacy absolute fallback used only if the hidden-state "
                         "magnitude is degenerate (max|h| == 0). The operative "
                         "criterion is --ulp-budget.")
    ap.add_argument("--ulp-budget", type=float, default=4.0,
                    help="Max acceptable divergence in bf16 ULPs of the observed "
                         "final-token hidden magnitude (r3 re-dimensioning: an "
                         "absolute floor is unachievable in bf16 at real "
                         "residual magnitudes). main() returns nonzero above "
                         "this so a failed parity check is unmissable.")
    ap.add_argument("--result-json", type=Path, default=None,
                    help="Optional path to write a machine-readable result "
                         "(divergence, floor, pass/fail, provenance).")
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

    model, tokenizer = load_model_and_tokenizer(
        a.model, device=a.device,
        adapter=a.adapter, adapter_revision=a.adapter_revision)
    device = next(model.parameters()).device
    d = torch.from_numpy(d_np).to(device)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Right padding keeps each row's real-token positions (and thus RoPE offsets)
    # identical to the unpadded single-prompt pass, minimizing the model's own
    # batched-vs-unbatched numeric noise. The delta comparison below is robust to
    # either side, but right padding is the cleaner apples-to-apples capture.
    tokenizer.padding_side = "right"

    questions = DEFAULT_QUESTIONS
    prompts = [_render(tokenizer, q) for q in questions]
    # Per-row alphas: distinct so per-element broadcasting is exercised.
    alphas = [a.alpha_base * (1.0 + 0.25 * i) for i in range(len(prompts))]

    layer = get_decoder_layer(model, layer_idx)

    def _capture_final(enc, steer_hook):
        """Run one forward at best_layer; return final-real-token hidden per row.

        steer_hook=None -> unsteered baseline forward. Otherwise the SteeringHook
        runs first and the _Capture hook (registered after) records the EDITED
        layer output.
        """
        attn = enc["attention_mask"]
        final_idx = _last_real_indices(attn)
        cap = _Capture()
        handles = []
        if steer_hook is not None:
            handles.append(layer.register_forward_hook(steer_hook))
        handles.append(layer.register_forward_hook(cap))  # runs last -> edited
        with torch.no_grad():
            model(**enc)
        for h in handles:
            h.remove()
        return torch.stack([cap.hidden[b, final_idx[b].item(), :]
                            for b in range(attn.shape[0])])

    # ---- (A) BATCHED: one padded forward, position="final", per-row alpha ----
    # Compare the STEERING DELTA (steered - unsteered), which cancels the model's
    # forward numerics and isolates exactly the edit the hook applied.
    enc = tokenizer(prompts, return_tensors="pt", padding=True).to(device)
    attn = enc["attention_mask"]
    steer = SteeringHook(d=d, alpha=alphas, position="final",
                         attention_mask=attn)
    batched_steered = _capture_final(enc, steer)
    batched_base = _capture_final(enc, None)
    batched_delta = batched_steered - batched_base

    # ---- (B) UNBATCHED: one forward per prompt, scalar alpha, last token ----
    unbatched_delta = []
    for i, prompt in enumerate(prompts):
        enc1 = tokenizer(prompt, return_tensors="pt").to(device)
        steer1 = SteeringHook(d=d, alpha=float(alphas[i]), position="final",
                              attention_mask=enc1["attention_mask"])
        s1 = _capture_final(enc1, steer1)
        b1 = _capture_final(enc1, None)
        unbatched_delta.append((s1 - b1)[0])
    unbatched_delta = torch.stack(unbatched_delta)

    # ---- Expected analytic edit: row i shifted by exactly alpha_i * d ----
    d_cpu = d.detach().float().cpu()
    expected_delta = torch.stack([float(alphas[i]) * d_cpu
                                  for i in range(len(prompts))])

    # (1) Hook applied exactly alpha_i * d (batched path).
    err_expected = (batched_delta - expected_delta).abs()
    # (2) Batched delta == one-prompt-at-a-time delta.
    err_bvu = (batched_delta - unbatched_delta).abs()

    per_row_expected = err_expected.amax(dim=1).numpy()
    per_row_bvu = err_bvu.amax(dim=1).numpy()
    max_expected = float(err_expected.max().item())
    max_bvu = float(err_bvu.max().item())
    max_abs = max(max_expected, max_bvu)

    # ---- ULP-relative floor (r3 re-dimensioning, user-approved 2026-07-05) ----
    # An absolute floor cannot certify a bf16 edit: writing alpha*d into a
    # residual entry of magnitude ~2^k rounds at ULP = 2^(k-7), which at real
    # layer-34 magnitudes (O(100)) is 0.25-1.0, above any small absolute
    # constant for EVERY implementation, including a perfect one. The floor is
    # therefore dimensioned in ULPs of the observed final-token hidden
    # magnitude: both error legs must sit within --ulp-budget ULPs.
    max_h = float(torch.stack([batched_steered, batched_base])
                  .abs().max().item())
    if max_h > 0:
        ulp = 2.0 ** (math.floor(math.log2(max_h)) - 7)
        ulp_floor = a.ulp_budget * ulp
    else:
        ulp = None
        ulp_floor = a.floor
    passed = max_abs < ulp_floor
    print("[gpu-equiv] per-row |batched_delta - alpha_i*d| :",
          np.round(per_row_expected, 6).tolist(), flush=True)
    print("[gpu-equiv] per-row |batched_delta - unbatched_delta| :",
          np.round(per_row_bvu, 6).tolist(), flush=True)
    print(f"[gpu-equiv] OVERALL max abs divergence = {max_abs:.6e} "
          f"(vs-analytic={max_expected:.3e}, batched-vs-unbatched="
          f"{max_bvu:.3e})", flush=True)
    print(f"[gpu-equiv] max|h| at final tokens = {max_h:.1f}; bf16 ULP = "
          f"{ulp if ulp is not None else 'n/a'}; floor = {a.ulp_budget} x ULP "
          f"= {ulp_floor:.4f}  ->  {'PASS' if passed else 'FAIL'}", flush=True)

    if a.result_json is not None:
        result = {
            "cell": "gpu_equivalence_cell",
            "model": a.model,
            "adapter": a.adapter,
            "adapter_revision": a.adapter_revision,
            "direction": str(a.direction),
            "best_layer": int(layer_idx),
            "dtype": a.dtype,
            "alpha_base": a.alpha_base,
            "n_prompts": len(prompts),
            "per_row_abs_err_vs_analytic": [float(x) for x in per_row_expected],
            "per_row_abs_err_batched_vs_unbatched": [float(x) for x in per_row_bvu],
            "overall_max_abs_divergence": max_abs,
            "max_abs_err_vs_analytic": max_expected,
            "max_abs_err_batched_vs_unbatched": max_bvu,
            "comparison": "steering_delta (steered - unsteered), not absolute hidden state",
            "max_abs_hidden_at_final": max_h,
            "bf16_ulp_at_max_hidden": ulp,
            "ulp_budget": a.ulp_budget,
            "floor_effective": ulp_floor,
            "floor_criterion": "ulp_budget x bf16 ULP(max|h|) (r3 re-dimensioning; "
                               "absolute --floor is a degenerate-magnitude fallback)",
            "floor": a.floor,
            "passed": bool(passed),
        }
        a.result_json.parent.mkdir(parents=True, exist_ok=True)
        a.result_json.write_text(json.dumps(result, indent=2))
        print(f"[gpu-equiv] wrote result JSON -> {a.result_json}", flush=True)

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
