#!/usr/bin/env python3
"""Cross-family held-out J-space outcome run.

PRIMARY (gating): the best MID-BAND site's held-out confab clean_tighten (G1
floor) and known-correct not_well_formed_correct cost (G2 cap), scored on the
REUSED doubt-snap held-out split. SECONDARY (descriptive, non-gating): the
frozen late-reference arm -- doubt-snap's own late-site direction/gate reused
verbatim -- and the best-mid-band-minus-late deltas, reported for contrast with
doubt-snap's resolved late-site null.

REFRAMED 2026-07-23 (sign-time revision): the old relative G1/G2/G3 contrast
(best mid-band beats late by >=10pp, etc.) is replaced by absolute mid-band
gates read from each family's `primary_gate` block. The late arm gates NOTHING;
if its dose is unresolved (doubt-snap selected no late-site dose for any family
-- open question #2), the late arm is SKIPPED and the primary is unaffected.

Ported from `j-space-layer-contrast-replication-qwen3-4b/run_contrast.py` and
`j-space-midband-write-sweep-qwen3-4b/pipeline.py`, generalized to `--family`.
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
    FAMILY_SLUGS, layer_dir_name, load_family,
    midband_hs_indices as family_midband_hs_indices,
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


def load_midband_selected_doses(family: str) -> dict[str, float]:
    """Mid-band per-layer FIT-calibrated doses (calibrate_dose.py output). The
    late arm's dose is NOT here (it is reused-frozen / open question, resolved
    separately via --late-dose)."""
    path = HERE / "analysis-committed" / family / "dose_calibration_summary.json"
    data = json.loads(path.read_text())
    selected = {str(k): float(v) for k, v in data["selected_doses"].items()}
    if not data.get("all_layers_have_usable_dose"):
        raise ValueError(f"[{family}] calibration summary says not all mid-band layers have usable doses")
    return selected


def resolve_late_dose(family: str, cli_late_dose: float | None) -> float | None:
    """Late-arm dose resolution (OPEN QUESTION #2 -- doubt-snap selected no
    late-site dose for any family). Priority: explicit --late-dose, else the
    family YAML `reuse.doubt_snap.late_site.resolved_late_dose` if the lead set
    one at sign, else None (late arm skipped -- the primary does not depend on
    it). This function never invents a dose."""
    if cli_late_dose is not None:
        return float(cli_late_dose)
    ls = (load_family(family).get("reuse", {}).get("doubt_snap", {}) or {}).get("late_site", {}) or {}
    resolved = ls.get("resolved_late_dose")
    return float(resolved) if resolved is not None else None


def run_layers(
    family: str,
    rows: list[dict],
    hs_index_to_dose: dict[int, float],
    *,
    mode: str,
    fresh: bool = False,
) -> dict[str, dict]:
    """Run each requested layer's dosed pass for one family, checkpointing per
    row. `hs_index_to_dose` maps an hs_index (mid-band candidate or the late
    reference) to its dose; the late arm is included only if a dose was
    resolved for it (see resolve_late_dose)."""
    RunLog, _RunLogError = ml.load_run_log_class()
    model, tokenizer, _hidden_size, _n_layers = ml.load_model_and_tokenizer(family)
    try:
        layer_results: dict[str, dict] = {}
        for hs_index, dose in hs_index_to_dose.items():
            layer_name = layer_dir_name(hs_index)
            print(f"[contrast:{family}] layer={layer_name} dose={dose}", flush=True)
            gate_rows = pl.compute_gate_decisions(family, rows, hs_index)
            log_path = HERE / "analysis" / family / "runlog" / mode / f"{layer_name}.jsonl"
            run_log = RunLog(
                log_path,
                run_config={
                    "experiment": "j-space-cross-family-layer-contrast",
                    "family": family, "mode": mode, "layer": layer_name,
                    "hs_index": hs_index, "dose_target": dose,
                },
                fresh=fresh,
            )
            try:
                rec = pl.run_layer(family, model, tokenizer, hs_index, gate_rows, dose, run_log=run_log)
            finally:
                run_log.close()
            rec["dose_target"] = dose
            layer_results[layer_name] = rec
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()
    return layer_results


def _passes_floor(rate_block: dict, floor: dict) -> bool:
    return bool(
        rate_block["rate"] >= floor["rate"]
        and rate_block["wilson_ci_95"][0] > floor["wilson_lower_ci"]
    )


def _passes_cap(rate_block: dict, cap: dict) -> bool:
    return bool(
        rate_block["rate"] <= cap["rate"]
        and rate_block["wilson_ci_95"][1] < cap["wilson_upper_ci"]
    )


def evaluate_primary(family: str, layer_results: dict[str, dict]) -> dict:
    """ABSOLUTE mid-band actuation gates (G1/G2) plus the descriptive late arm.

    Best mid-band = highest held-out confab clean_tighten, ties broken by lower
    known-correct cost. G1/G2 thresholds come from the family YAML primary_gate
    block. The late arm (if it ran) is reported descriptively; it gates nothing.
    """
    cfg = load_family(family)
    pg = cfg["primary_gate"]
    g1_floor = pg["g1_midband_clean_tighten_floor"]
    g2_cap = pg["g2_midband_known_correct_cost_cap"]

    late_hs = family_late_reference_hs(cfg)
    late_name = layer_dir_name(late_hs)
    mid_names = [n for n in layer_results if n != late_name]
    if not mid_names:
        raise ValueError(f"[{family}] no mid-band layer results to evaluate primary on")

    best_mid_name = max(
        mid_names,
        key=lambda name: (layer_results[name]["confab_tighten"]["rate"],
                          -layer_results[name]["known_correct_cost_control"]["rate"]),
    )
    best_mid = layer_results[best_mid_name]
    g1_pass = _passes_floor(best_mid["confab_tighten"], g1_floor)
    g2_pass = _passes_cap(best_mid["known_correct_cost_control"], g2_cap)

    out = {
        "family": family,
        "best_mid_layer": best_mid_name,
        "g1_floor_used": g1_floor,
        "g2_cap_used": g2_cap,
        "best_mid_confab_clean_tighten": best_mid["confab_tighten"],
        "best_mid_known_correct_cost": best_mid["known_correct_cost_control"],
        "g1_midband_actuation_floor_pass": g1_pass,
        "g2_midband_selectivity_cap_pass": g2_pass,
        "primary_pass": bool(g1_pass and g2_pass),
        "late_reference_layer": late_name,
    }

    # Secondary descriptive: only if the late arm actually ran.
    if late_name in layer_results:
        late = layer_results[late_name]
        out["secondary_late_reference"] = {
            "gating": "none",
            "late_confab_clean_tighten": late["confab_tighten"],
            "late_known_correct_cost": late["known_correct_cost_control"],
            "best_mid_minus_late_tighten_delta": (
                best_mid["confab_tighten"]["rate"] - late["confab_tighten"]["rate"]
            ),
            "best_mid_minus_late_cost_delta": (
                best_mid["known_correct_cost_control"]["rate"]
                - late["known_correct_cost_control"]["rate"]
            ),
        }
    else:
        out["secondary_late_reference"] = {
            "gating": "none",
            "status": "SKIPPED -- late-arm dose unresolved (open question #2); "
                      "the primary does not depend on the late arm.",
        }
    return out


def g0_smoke_pass(layer_results: dict[str, dict]) -> bool:
    for rec in layer_results.values():
        if rec["frac_readback_within_tol"] != 1.0:
            return False
        if rec["collapse_rate_on_dosed"] != 0.0:
            return False
    return True


def _layer_dose_map(family: str, late_dose: float | None) -> dict[int, float]:
    """Mid-band candidates (always) + the late reference (only if a late dose
    is resolved)."""
    cfg = load_family(family)
    selected = load_midband_selected_doses(family)
    dose_map: dict[int, float] = {}
    for hs_index in family_midband_hs_indices(cfg):
        dose_map[hs_index] = selected[layer_dir_name(hs_index)]
    if late_dose is not None:
        dose_map[family_late_reference_hs(cfg)] = late_dose
    return dose_map


def write_summary(family: str, name: str, summary: dict, commit_public: bool) -> None:
    analysis = HERE / "analysis" / family
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / name).write_text(json.dumps(summary, indent=2))
    if commit_public:
        committed = HERE / "analysis-committed" / family
        committed.mkdir(parents=True, exist_ok=True)
        (committed / name).write_text(json.dumps(summary, indent=2))


def run_smoke(family: str, n_rows: int, late_dose: float | None, *, fresh: bool = False) -> dict:
    dose_map = _layer_dose_map(family, late_dose)
    rows = selected_rows(family, n_rows)
    layer_results = run_layers(family, rows, dose_map, mode="smoke", fresh=fresh)
    summary = {
        "family": family, "mode": "smoke", "layer_doses": {layer_dir_name(k): v for k, v in dose_map.items()},
        "late_arm_included": late_dose is not None,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "g0_smoke_pass": g0_smoke_pass(layer_results),
    }
    write_summary(family, "smoke_summary.json", summary, commit_public=False)
    print(json.dumps(summary, indent=2))
    return summary


def run_full(family: str, late_dose: float | None, *, fresh: bool = False) -> dict:
    dose_map = _layer_dose_map(family, late_dose)
    rows = selected_rows(family, None)
    rng = pyrandom.Random(20260708)
    rng.shuffle(rows)
    layer_results = run_layers(family, rows, dose_map, mode="full", fresh=fresh)
    primary = evaluate_primary(family, layer_results)
    summary = {
        "family": family, "mode": "full",
        "layer_doses": {layer_dir_name(k): v for k, v in dose_map.items()},
        "late_arm_included": late_dose is not None,
        "pool_counts": pool_counts(family), "n_rows": len(rows), "layers": layer_results,
        "primary": primary,
        "primary_pass": bool(g0_smoke_pass(layer_results) and primary["primary_pass"]),
    }
    write_summary(family, "full_summary.json", summary, commit_public=True)
    print(json.dumps(summary, indent=2))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, choices=FAMILY_SLUGS)
    parser.add_argument("--mode", choices=["smoke", "full"], required=True)
    parser.add_argument("--n-rows", type=int, default=8, help="smoke mode only")
    parser.add_argument(
        "--late-dose", type=float, default=None,
        help="Resolve the SECONDARY late-reference arm's dose (open question #2: "
             "doubt-snap selected no late-site dose). If omitted and the family "
             "YAML has no resolved_late_dose, the late arm is SKIPPED and only "
             "the primary (mid-band) gates are evaluated.",
    )
    parser.add_argument("--i-know-this-is-the-cross-family-run", action="store_true")
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--resume", dest="fresh", action="store_false", default=False,
        help="Resume from each layer's existing run log, skipping already-done rows (default).",
    )
    resume_group.add_argument(
        "--fresh", dest="fresh", action="store_true",
        help="Discard each layer's existing run log for this family/mode and start over.",
    )
    args = parser.parse_args(argv)

    late_dose = resolve_late_dose(args.family, args.late_dose)

    if args.mode == "smoke":
        return 0 if run_smoke(args.family, args.n_rows, late_dose, fresh=args.fresh)["g0_smoke_pass"] else 4

    if not args.i_know_this_is_the_cross_family_run:
        print(
            "[contrast] full mode is the signed cross-family outcome run; refusing "
            "without --i-know-this-is-the-cross-family-run",
            file=sys.stderr,
        )
        return 2
    run_full(args.family, late_dose, fresh=args.fresh)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
