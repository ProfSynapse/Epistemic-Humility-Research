#!/usr/bin/env python3
"""Cross-family held-out J-space layer contrast: best mid-band site vs late
reference site, gated snap at calibrated doses, per family.

Ported from `j-space-layer-contrast-replication-qwen3-4b/run_contrast.py`
and `j-space-midband-write-sweep-qwen3-4b/pipeline.py`, generalized to a
`--family` flag. Reuses this experiment's own `pipeline.py`
(compute_gate_decisions / run_layer / stratified_subset), which is itself
the family-aware port of the predecessor's identically-named functions.

G3's late-reference viability floor is read from the family's own
`g3_late_reference_floor` (LOCKED at 0.40 rate / 0.30 Wilson-lower for every
family per the locked design -- lower than Qwen3-4B's own predecessor floor
of 0.60/0.50, since instruct families may differ; see AMENDMENT.md "Gates"
and LAUNCH-PLAN.md for why this is flagged to the lead rather than
re-derived here).
"""

from __future__ import annotations

import argparse
import gc
import json
import random as pyrandom
import sys
from pathlib import Path

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import (  # noqa: E402
    FAMILY_SLUGS, layer_dir_name, load_family, hs_indices as family_hs_indices,
    late_reference_hs as family_late_reference_hs,
)
import model_lib as ml  # noqa: E402
import pipeline as pl  # noqa: E402


def pool_counts(family: str) -> dict:
    return {
        "confab_held_out": len(pl.load_rows(family, "confab", "held_out")),
        "known_correct_answered_held_out": len(
            pl.load_rows(family, "known_correct_answered", "held_out")
        ),
    }


def selected_rows(family: str, n_rows: int | None) -> list[dict]:
    confab = pl.load_rows(family, "confab", "held_out")
    known = pl.load_rows(family, "known_correct_answered", "held_out")
    if n_rows is None:
        return confab + known
    n_confab = n_rows // 2
    n_known = n_rows - n_confab
    return pl.stratified_subset(confab, n_confab) + pl.stratified_subset(known, n_known)


def load_selected_doses(family: str) -> dict[str, float]:
    path = HERE / "analysis-committed" / family / "dose_calibration_summary.json"
    data = json.loads(path.read_text())
    selected = {str(k): float(v) for k, v in data["selected_doses"].items()}
    if not data.get("all_layers_have_usable_dose"):
        raise ValueError(f"[{family}] calibration summary says not all layers have usable doses")
    return selected


def run_layers(family: str, rows: list[dict], selected_doses: dict[str, float]) -> dict[str, dict]:
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    try:
        layer_results: dict[str, dict] = {}
        for hs_index in family_hs_indices(load_family(family)):
            layer_name = layer_dir_name(hs_index)
            dose = selected_doses[layer_name]
            print(f"[contrast:{family}] layer={layer_name} dose={dose}", flush=True)
            gate_rows = pl.compute_gate_decisions(family, rows, hs_index)
            rec = pl.run_layer(family, model, tokenizer, hs_index, gate_rows, dose)
            rec["dose_target"] = dose
            layer_results[layer_name] = rec
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return layer_results


def evaluate_layer_contrast(family: str, layer_results: dict[str, dict]) -> dict:
    cfg = load_family(family)
    late_hs = family_late_reference_hs(cfg)
    late_name = layer_dir_name(late_hs)
    late = layer_results[late_name]
    mid_names = [n for n in layer_results if n != late_name]
    best_mid_name = max(
        mid_names,
        key=lambda name: (layer_results[name]["confab_tighten"]["rate"],
                          -layer_results[name]["known_correct_cost_control"]["rate"]),
    )
    best_mid = layer_results[best_mid_name]
    tighten_delta = best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
    cost_delta = (
        best_mid["known_correct_cost_control"]["rate"]
        - late["known_correct_cost_control"]["rate"]
    )
    late_ci_lo = late["confab_tighten"]["wilson_ci_95"][0]
    floor = cfg["g3_late_reference_floor"]
    return {
        "family": family, "best_mid_layer": best_mid_name, "late_reference_layer": late_name,
        "tighten_delta_best_mid_minus_late": tighten_delta,
        "cost_delta_best_mid_minus_late": cost_delta,
        "g1_midband_superiority_pass": tighten_delta >= 0.10,
        "g2_no_cost_regression_pass": cost_delta <= 0.02,
        "g3_late_reference_viable_pass": (
            late["confab_tighten"]["rate"] >= floor["clean_tighten_rate_floor"]
            and late_ci_lo > floor["wilson_lower_ci_floor"]
        ),
        "g3_floor_used": floor,
    }


def g0_smoke_pass(layer_results: dict[str, dict]) -> bool:
    for rec in layer_results.values():
        if rec["frac_readback_within_tol"] != 1.0:
            return False
        if rec["collapse_rate_on_dosed"] != 0.0:
            return False
    return True


def write_summary(family: str, name: str, summary: dict, commit_public: bool) -> None:
    analysis = HERE / "analysis" / family
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / name).write_text(json.dumps(summary, indent=2))
    if commit_public:
        committed = HERE / "analysis-committed" / family
        committed.mkdir(parents=True, exist_ok=True)
        (committed / name).write_text(json.dumps(summary, indent=2))


def run_smoke(family: str, n_rows: int) -> dict:
    selected_doses = load_selected_doses(family)
    rows = selected_rows(family, n_rows)
    layer_results = run_layers(family, rows, selected_doses)
    summary = {
        "family": family, "mode": "smoke", "selected_doses": selected_doses,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "g0_smoke_pass": g0_smoke_pass(layer_results),
    }
    write_summary(family, "smoke_summary.json", summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_full(family: str) -> dict:
    selected_doses = load_selected_doses(family)
    rows = selected_rows(family, None)
    rng = pyrandom.Random(20260708)
    rng.shuffle(rows)
    layer_results = run_layers(family, rows, selected_doses)
    contrast = evaluate_layer_contrast(family, layer_results)
    summary = {
        "family": family, "mode": "full", "selected_doses": selected_doses,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "layer_contrast": contrast,
        "overall_pass": bool(
            g0_smoke_pass(layer_results)
            and contrast["g1_midband_superiority_pass"]
            and contrast["g2_no_cost_regression_pass"]
            and contrast["g3_late_reference_viable_pass"]
        ),
    }
    write_summary(family, "full_summary.json", summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument("--i-know-this-is-the-cross-family-run", action="store_true")
    args = parser.parse_args(argv)

    if args.mode == "smoke":
        return 0 if run_smoke(args.family, args.n_rows)["g0_smoke_pass"] else 4

    if not args.i_know_this_is_the_cross_family_run:
        print(
            "[contrast] full mode is the signed cross-family outcome run; refusing "
            "without --i-know-this-is-the-cross-family-run",
            file=sys.stderr,
        )
        return 2
    run_full(args.family)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
