#!/usr/bin/env python3
"""Amendment AA — Arm A orchestration: activation-steering cells AA-1..AA-4.

SPEC: experiments/causal-confidence-steering/AMENDMENT.md (Tier-2,
DRAFT — NOT signed). NO GPU cell may launch until the amendment is signed AND
the user gives explicit launch approval naming the exact cells and lane.

IMPORT-TIME IS GPU-FREE. Model loading happens only inside main()'s guarded
path (never under --dry-run). The cell loop (run_arm_a_cell) takes injected
callables so it is fully unit-testable on CPU with synthetic fixtures.

Protocol per item (Amendment AA unified protocol, all cells):
  1. initial answer pass
  2. revision pass ("Double-check your answer above. If you are not confident
     it is correct, say so or revise it.")
  position=anchor -> the SteeringHook is active during the INITIAL pass only
                     (prefill call, last prompt token = the pre-answer anchor);
  position=end    -> active during the REVISION pass only (every generated
                     token of the post-answer stream).
  alpha is proportional to measured uncertainty (confidence_steer.py
  compute_proportional_alpha over the direction's calibration stats) when a
  probe score is available; the alpha=0 control is always included.

All outcomes are graded on the FINAL post-revision output (gate = abstention
on unknown; dial = appropriate-revision discrimination), with initial-pass
grading recorded so P(revise|wrong) - P(revise|correct) is computable.
Output: one JSON per cell (per-item records + per-alpha summaries + paired
bootstrap 95% CIs vs the alpha=0 control).

Example (Stage 1, AA-1 — DO NOT run without signed amendment + launch approval):
  python run_arm_a.py \
      --model unsloth/Qwen3.5-4B \
      --direction experiments/common/artifacts/two_signal_probe_directions/qwen3.5-4b/direction_gate.json \
      --position anchor --alpha-sweep=-4,-2,-1,0,1,2,4 \
      --eval-pool gate --n-unknown 300 --n-known 300 \
      --gate-rows <selfaware rows.jsonl> \
      --seed 20260701 --device cuda --out results/aa1_gate_anchor.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Optional

from path_compat import datasets_dir as _default_datasets_dir
from steering_common import (
    N_BOOT_DEFAULT,
    SYSTEM_PROMPT,
    GenerationHookController,
    adequacy_check,
    base_cell_payload,
    build_eval_pool,
    build_initial_messages,
    build_revision_messages,
    compare_conditions,
    compute_proportional_alpha,
    load_direction,
    make_flat_record,
    parse_alpha_list,
    summarize_condition,
    write_cell_json,
)


# ---------------------------------------------------------------------------
# Cell loop (pure orchestration — injected callables, unit-testable on CPU)
# ---------------------------------------------------------------------------

def run_arm_a_cell(
    items: list[dict],
    alpha_values: list[float],
    position: str,
    controller: GenerationHookController,
    generate_fn: Callable[[dict, Optional[str], str], str],
    score_fn: Optional[Callable[[dict], float]] = None,
    calibration: Optional[dict] = None,
) -> dict[float, list[dict]]:
    """Run the two-pass protocol for every item at every alpha.

    Parameters
    ----------
    items        : eval pool (row_key, question, source, aliases_norm)
    alpha_values : sweep values; 0.0 (the control) is added if missing
    position     : 'anchor' (steer initial pass) | 'end' (steer revision pass)
    controller   : GenerationHookController (or a test double with begin_pass)
    generate_fn  : (item, initial_answer_or_None, pass_name) -> generated text;
                   pass_name in {'initial','revision'}. The callable owns
                   prompt rendering + decoding (model-bound in main(); a fake
                   in unit tests).
    score_fn     : optional (item) -> probe P(positive); with `calibration`,
                   drives per-item proportional alpha.
    calibration  : the direction JSON's calibration block.

    Returns
    -------
    {alpha: [flat_record, ...]} — records aligned by item order across alphas.
    """
    if position not in ("anchor", "end"):
        raise ValueError(f"position must be 'anchor' or 'end', got {position!r}")
    alphas = list(dict.fromkeys(alpha_values))  # dedupe, keep order
    if 0.0 not in alphas:
        alphas = [0.0] + alphas

    results: dict[float, list[dict]] = {}
    for alpha in alphas:
        records: list[dict] = []
        for item in items:
            score = None
            alpha_eff = alpha
            if alpha != 0.0 and score_fn is not None and calibration is not None:
                score = float(score_fn(item))
                alpha_eff = compute_proportional_alpha(alpha, score, calibration)

            # Initial pass: hook active only for position='anchor'.
            if position == "anchor" and alpha_eff != 0.0:
                controller.begin_pass("anchor", alpha_eff)
            else:
                controller.begin_pass("off", 0.0)
            initial_text = generate_fn(item, None, "initial")

            # Revision pass: hook active only for position='end'.
            if position == "end" and alpha_eff != 0.0:
                controller.begin_pass("gen_stream", alpha_eff)
            else:
                controller.begin_pass("off", 0.0)
            final_text = generate_fn(item, initial_text, "revision")

            records.append(make_flat_record(
                item, initial_text, final_text,
                extra={
                    "alpha": alpha,
                    "alpha_effective": alpha_eff,
                    "probe_score": score,
                },
            ))
        results[alpha] = records
    return results


def summarize_arm_a(
    results: dict[float, list[dict]],
    n_boot: int = N_BOOT_DEFAULT,
    seed: int = 20260701,
) -> dict:
    """Per-alpha metric summaries + paired bootstrap contrasts vs alpha=0."""
    if 0.0 not in results:
        raise ValueError("summarize_arm_a requires the alpha=0 control condition")
    control = results[0.0]
    summary: dict = {
        "per_alpha": {},
        "vs_control": {},
        "adequacy": adequacy_check(control),
    }
    for alpha in sorted(results):
        summary["per_alpha"][str(alpha)] = summarize_condition(results[alpha])
        if alpha != 0.0:
            summary["vs_control"][str(alpha)] = compare_conditions(
                results[alpha], control, n_boot=n_boot, seed=seed)
    return summary


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True,
                    help="Model name/path (HF hub or local)")
    ap.add_argument("--direction", required=True, type=Path,
                    help="direction_<signal>.json from persist_probe_direction.py")
    ap.add_argument("--position", choices=["anchor", "end"], required=True,
                    help="anchor = steer initial pass; end = steer revision pass")
    sweep = ap.add_mutually_exclusive_group(required=True)
    sweep.add_argument("--alpha-sweep", type=str, default=None,
                       help="comma list (use the '=' form for negative values, "
                            "e.g. --alpha-sweep=-4,-2,-1,0,1,2,4) (AA-1 / AA-3)")
    sweep.add_argument("--alpha", type=float, default=None,
                       help="single alpha* for the off-position cells "
                            "(AA-2 / AA-4); the alpha=0 control still runs")
    ap.add_argument("--eval-pool", choices=["gate", "dial"], required=True)
    ap.add_argument("--n-unknown", type=int, default=300)
    ap.add_argument("--n-known", type=int, default=300)
    ap.add_argument("--n-answerable", type=int, default=500)
    ap.add_argument("--pool-file", type=Path, default=None,
                    help="JSONL pool override (CPU dry-run / tests)")
    ap.add_argument("--gate-rows", type=Path, default=None,
                    help="SelfAware frozen rows.jsonl (gate pool source)")
    ap.add_argument("--datasets-root", type=Path,
                    default=_default_datasets_dir(),
                    help="root for the PopQA/TriviaQA dial pool")
    ap.add_argument("--cell", default=None, help="cell tag, e.g. AA-1 (provenance)")
    ap.add_argument("--seed", type=int, default=20260701)
    ap.add_argument("--n-boot", type=int, default=N_BOOT_DEFAULT)
    ap.add_argument("--max-new-tokens-initial", type=int, default=128)
    ap.add_argument("--max-new-tokens-revision", type=int, default=96)
    ap.add_argument("--greedy", action="store_true",
                    help="greedy decode (default: sampled, per Amendment SR)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true",
                    help="CPU-only: load direction, build pool, print the cell "
                         "plan; no model load, no generation")
    return ap.parse_args(argv)


def _resolve_alphas(a: argparse.Namespace) -> list[float]:
    if a.alpha_sweep is not None:
        return parse_alpha_list(a.alpha_sweep)
    return [0.0, float(a.alpha)]


def main(argv=None) -> int:
    a = parse_args(argv)
    d_np, meta = load_direction(a.direction)
    alphas = _resolve_alphas(a)
    if 0.0 not in alphas:
        alphas = [0.0] + alphas

    items = build_eval_pool(
        eval_pool=a.eval_pool,
        n_unknown=a.n_unknown,
        n_known=a.n_known,
        n_answerable=a.n_answerable,
        seed=a.seed,
        pool_file=a.pool_file,
        datasets_root=a.datasets_root,
        gate_rows=a.gate_rows,
    )

    plan = {
        "arm": "A",
        "cell": a.cell,
        "signal": meta.get("signal"),
        "position": a.position,
        "model": a.model,
        "direction": str(a.direction),
        "direction_layer": meta.get("best_layer"),
        "eval_pool": a.eval_pool,
        "n_items": len(items),
        "alpha_values": alphas,
        "seed": a.seed,
        "decode": ("greedy" if a.greedy
                   else f"sampled(temp={a.temperature},top_p={a.top_p})"),
        "max_new_tokens": {"initial": a.max_new_tokens_initial,
                           "revision": a.max_new_tokens_revision},
        "n_generations": len(items) * len(alphas) * 2,
        "out": str(a.out),
    }
    print("[run_arm_a] cell plan:\n" + json.dumps(plan, indent=2), flush=True)
    if a.dry_run:
        print("[run_arm_a] dry-run: direction + pool OK; no model loaded.",
              flush=True)
        return 0

    # ------------------------------------------------------------------
    # GPU path (signed amendment + explicit user launch approval required)
    # ------------------------------------------------------------------
    import numpy as np
    import torch
    import transformers as _tf

    from steering_common import probe_score_from_hidden
    from confidence_steer import (
        SteeringHook, get_decoder_layer, load_model_and_tokenizer,
    )
    from backends import render_probe_prompt

    _tf.set_seed(a.seed)
    torch.manual_seed(a.seed)

    print(f"[run_arm_a] loading model {a.model} ...", flush=True)
    model, tokenizer = load_model_and_tokenizer(a.model, device=a.device)
    layer_idx = meta["best_layer"]
    hook = SteeringHook(d=torch.from_numpy(d_np), alpha=0.0, position="anchor")
    controller = GenerationHookController(hook)
    layer = get_decoder_layer(model, layer_idx)
    handle = layer.register_forward_hook(controller)
    print(f"[run_arm_a] controller registered at layer {layer_idx}", flush=True)

    device = next(model.parameters()).device
    calibration = meta.get("calibration")

    def _render(messages: list[dict]) -> str:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=False)

    def _generate(prompt: str, max_new: int) -> str:
        enc = tokenizer(prompt, return_tensors="pt").to(device)
        gen_kw = dict(max_new_tokens=max_new, num_beams=1,
                      pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id)
        if a.greedy:
            gen_kw.update(do_sample=False)
        else:
            gen_kw.update(do_sample=True, temperature=a.temperature, top_p=a.top_p)
        with torch.no_grad():
            out = model.generate(**enc, **gen_kw)
        return tokenizer.decode(out[0][enc["input_ids"].shape[1]:],
                                skip_special_tokens=True).strip()

    def generate_fn(item: dict, initial_answer: Optional[str], pass_name: str) -> str:
        if pass_name == "initial":
            messages = build_initial_messages(item["question"], SYSTEM_PROMPT)
            max_new = a.max_new_tokens_initial
        else:
            messages = build_revision_messages(
                item["question"], initial_answer or "", SYSTEM_PROMPT)
            max_new = a.max_new_tokens_revision
        return _generate(_render(messages), max_new)

    def score_fn(item: dict) -> float:
        """Pre-answer anchor read at the direction's layer (proportional alpha)."""
        rendered, _mode = render_probe_prompt(
            tokenizer, SYSTEM_PROMPT, item["question"], enable_thinking=False)
        enc = tokenizer(rendered, return_tensors="pt").to(device)
        controller.begin_pass("off", 0.0)  # never steer the scoring read
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True, use_cache=False)
        h = out.hidden_states[layer_idx][0, -1, :].float().cpu().numpy()
        return probe_score_from_hidden(h, np.asarray(d_np))

    results = run_arm_a_cell(
        items=items,
        alpha_values=alphas,
        position=a.position,
        controller=controller,
        generate_fn=generate_fn,
        score_fn=score_fn,
        calibration=calibration,
    )
    handle.remove()

    summary = summarize_arm_a(results, n_boot=a.n_boot, seed=a.seed)
    payload = base_cell_payload(
        arm="A", cell=a.cell, signal=meta.get("signal", "?"),
        position=a.position, model=a.model, direction_meta=meta,
        eval_pool=a.eval_pool, seed=a.seed, n_items=len(items),
        config_extra=plan,
    )
    payload["items"] = {str(alpha): recs for alpha, recs in results.items()}
    payload["summary"] = summary
    out = write_cell_json(a.out, payload)
    print(f"[run_arm_a] wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
