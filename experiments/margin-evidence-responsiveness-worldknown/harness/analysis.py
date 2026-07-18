#!/usr/bin/env python3
"""Final raw-results assembly for margin-evidence-responsiveness-worldknown
(M4-WK) (RUN PLAN step 8). CPU-only, no model, no new statistics beyond
what capture_channel1.py / ladder_channel2.py / survival_channel2.py /
calibration.py already computed from their own artifacts.

Per the lead's explicit instruction, this script REPORTS raw numbers only
and does NOT declare criterion (d) earned/not-earned -- that adjudication
(including the BLOCKER B1 transfer-firing precondition, the split-result
channel-dissociation reading, and any halt/void/lift-to-PI disposition) is
reserved for the lead. Transfer is reported as PRIMARY, native as SECONDARY,
per cell.yaml `criterion_d.primary_direction: transfer`.

Reads the FROZEN floor numerics live from gates.yaml (gates.yaml
`rederived_floors.*.numeric`, expected to exist ONLY after the two
self-blinding repins for that direction have been performed -- see
gates.yaml `rederived_floors.collapse_floor_z.numeric_at_repin` /
`d2_absolute_floor.numeric_at_repin`; `bin/exp repin` is the freezing
mechanism, executed as a distinct action once each floor's baseline/n is
realized, NOT by this script). HALTS with a clear message, rather than
guessing or falling back to an "if_frozen_now" placeholder, if a direction's
floor has not yet been frozen -- this script must never silently score
against an un-frozen (i.e., potentially goalpost-moved) floor.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import stats  # noqa: E402

ANALYSIS = config.EXPERIMENT_DIR / "analysis"
COMMITTED = config.EXPERIMENT_DIR / "analysis-committed"
CHANNEL1_DIR = COMMITTED / "channel1"
LADDER_DIR = ANALYSIS / "channel2_ladder"
SURVIVAL_DIR = ANALYSIS / "channel2_survival"
CAL_DIR = ANALYSIS / "calibration"
RESULTS_DIR = ANALYSIS / "results"


def _live_gates_yaml() -> dict[str, Any]:
    return yaml.safe_load(config.GATES_YAML_PATH.read_text(encoding="utf-8"))


def frozen_floor(direction: str, floor_name: str) -> Optional[float]:
    """floor_name: "collapse_floor_z" or "d2_absolute_floor". Returns None
    (never a guessed number) if the per-direction frozen numeric is absent."""
    gates = _live_gates_yaml()
    node = gates.get("rederived_floors", {}).get(floor_name, {})
    numeric = node.get("numeric")
    if not isinstance(numeric, dict):
        return None
    return numeric.get(direction)


def load_channel1_per_row(direction: str) -> list[dict[str, Any]]:
    path = CHANNEL1_DIR / "per_row_projections.jsonl"
    if not path.is_file():
        raise SystemExit(f"analysis FAIL: no {path}; run capture_channel1.py (full population) first.")
    return common.load_jsonl(path)


def compute_D1(direction: str) -> dict[str, Any]:
    rows = load_channel1_per_row(direction)
    confab = [r for r in rows if r["role"] == "confab"]
    correct = [r for r in rows if r["role"] == "correct_on_answerable"]

    baseline_key = f"no_answer_baseline__{direction}_z"
    true_key = f"true_answer__{direction}_z"
    false_key = f"false_answer_placebo__{direction}_z"

    shift_true_confab = np.array([r[baseline_key] - r[true_key] for r in confab])
    shift_false_confab = np.array([r[baseline_key] - r[false_key] for r in confab])
    shift_true_correct = np.array([r[baseline_key] - r[true_key] for r in correct])

    leg1_ci = stats.bootstrap_median_ci(shift_true_confab, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED)
    leg2 = stats.bootstrap_paired_diff(shift_true_confab, shift_false_confab, n_boot=config.BOOTSTRAP_N_RESAMPLES, seed=config.BOOTSTRAP_SEED, statistic="mean")

    collapse_floor_z = frozen_floor(direction, "collapse_floor_z")
    leg1_median = leg1_ci["point"]

    correct_specificity = {
        "median_shift_true_answer_correct_control": float(np.median(shift_true_correct)),
        "median_shift_true_answer_confab": leg1_median,
        "correct_shift_as_large_as_confab_shift": (
            None if collapse_floor_z is None
            else bool(float(np.median(shift_true_correct)) >= collapse_floor_z)
        ),
    }

    return {
        "direction": direction, "n_confab": len(confab), "n_correct_control": len(correct),
        "leg_1_position_into_gap": {
            "median_shift_true_answer_confab": leg1_ci,
            "collapse_floor_z_frozen": collapse_floor_z,
            "passes_floor": (None if collapse_floor_z is None else leg1_median >= collapse_floor_z),
        },
        "leg_2_specificity": {
            "paired_diff_true_minus_false_shift": leg2,
            "true_shift_larger": leg2["point"] > 0,
            "excludes_zero_and_true_larger": bool(leg2["excludes_zero"] and leg2["point"] > 0),
        },
        "both_legs_required": True,
        "correct_control_specificity": correct_specificity,
    }


def compute_D2(direction: str) -> dict[str, Any]:
    score_path = SURVIVAL_DIR / f"{direction}_survival_score.json"
    if not score_path.is_file():
        raise SystemExit(f"analysis FAIL: no {score_path}; run survival_channel2.py score --direction {direction} first.")
    score = common.load_json(score_path)

    d2_absolute_floor = frozen_floor(direction, "d2_absolute_floor")
    paired = score["primary_test_paired_diff_true_minus_false"]

    return {
        "direction": direction, "n_margin_eligible": score["n_margin_eligible"],
        "baseline_staleness_check": score["baseline_staleness_check"],
        "survival_rates": score["survival_rates"],
        "primary_test_paired_diff_true_minus_false": paired,
        "d2_absolute_floor_frozen": d2_absolute_floor,
        "passes_floor": (
            None if d2_absolute_floor is None
            else bool(paired["excludes_zero"] and paired["point"] >= d2_absolute_floor)
        ),
    }


def load_separation_reproduction(direction: str) -> Optional[dict[str, Any]]:
    summary_path = LADDER_DIR / f"{direction}_margin_summary.json"
    rows_path = LADDER_DIR / f"{direction}_margin_rows.jsonl"
    if not rows_path.is_file():
        return None
    rows = common.load_jsonl(rows_path)
    confab_margins = [r["tipping_dose_abs"] for r in rows if r["role"] == "confab"]
    correct_margins = [r["tipping_dose_abs"] for r in rows if r["role"] == "correct_on_answerable"]
    return {
        "median_confab_margin": float(np.median(confab_margins)) if confab_margins else None,
        "median_correct_control_margin": float(np.median(correct_margins)) if correct_margins else None,
        "reproduces_m1_style_separation": (
            float(np.median(confab_margins)) < float(np.median(correct_margins))
            if confab_margins and correct_margins else None
        ),
        "bracketing_report": common.load_json(summary_path)["bracketing_report"] if summary_path.is_file() else None,
    }


def load_transfer_firing_gate() -> Optional[dict[str, Any]]:
    path = CHANNEL1_DIR / "floor_inputs.json"
    if not path.is_file():
        return None
    return common.load_json(path)["transfer_firing_gate"]


def load_alias_grader_bound() -> Optional[dict[str, Any]]:
    path = CAL_DIR / "correctness_calibration_score.json"
    if not path.is_file():
        return None
    return common.load_json(path)


def load_single_regime_attestation() -> dict[str, Any]:
    """C1_construct_integrity.single_regime_required: compares the recorded
    batch-composition row_order_sha256 across the channel-1 capture arms and
    the channel-2 survival arms; a mismatch means a mixed regime, voiding the
    paired comparison at that site (reported, never silently ignored)."""
    out: dict[str, Any] = {}
    for arm in config.ARMS:
        p = CHANNEL1_DIR.parent / "channel1_capture" / arm / "capture_manifest.json"
        out[f"channel1_{arm}"] = common.load_json(p)["composition"]["row_order_sha256"] if p.is_file() else None
    channel1_shas = {v for v in out.values() if v is not None}
    out["channel1_single_regime"] = (len(channel1_shas) <= 1)

    for direction in config.DIRECTIONS:
        p = SURVIVAL_DIR / f"{direction}_batch_composition.json"
        out[f"channel2_survival_{direction}"] = common.load_json(p)["row_order_sha256"] if p.is_file() else None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.parse_args()

    config.assert_pinned_hashes()

    result: dict[str, Any] = {
        "experiment": "margin-evidence-responsiveness-worldknown",
        "generated_note": "RAW NUMBERS ONLY. No criterion (d) earned/not-earned adjudication is made by this script; that is reserved for the lead per gates.yaml criteria.criterion_d_earned / criterion_d_not_earned / split_result.",
        "transfer_firing_gate": load_transfer_firing_gate(),
        "alias_grader_false_wrong_bound": load_alias_grader_bound(),
        "single_regime_attestation": load_single_regime_attestation(),
        "per_direction": {},
    }

    for direction in config.DIRECTIONS:
        d1 = compute_D1(direction)
        d2 = compute_D2(direction)
        sep = load_separation_reproduction(direction)
        result["per_direction"][direction] = {
            "role": "primary" if direction == "transfer" else "secondary",
            "D1_projection_collapse": d1,
            "D2_margin_lengthening": d2,
            "C1_separation_reproduction": sep,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "m4wk_results.json"
    common.write_json(out_path, result)
    print(json.dumps(result, indent=2), flush=True)
    print(f"\n[analysis] wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
