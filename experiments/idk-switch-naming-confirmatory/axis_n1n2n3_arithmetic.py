#!/usr/bin/env python3
"""N1/N2/N3 name-earning quantity arithmetic for idk-switch-naming-confirmatory.

Reads ONLY (a) `screen_flags/<arm>.jsonl` (pipeline.py's `screen` stage
output: row_key, arm, and three booleans -- f5_degenerate, f4_explicit_idk,
screened_in -- NO text) and (b) `isnc_axis_payload.jsonl`
(apply_judge_grades.py's `apply-full-pool` output: row_key, arm, form_label
for core/non-decoy rows only -- NO text). No raw generation text, no
row_key-to-text mapping, ever touches this module, matching
`form-judge-axis-g-rescore/axis_g_arithmetic.py`'s own data-minimization
discipline (source sha256
ee252321f6880748ffbfbd1f5596492c86b34c934282c0a66c873829401612e7, matching
that file's own pin; read in full before writing this) even though this
script additionally needs ROW-LEVEL (not just aggregate) alignment across
arms for the N1/N3 paired bootstrap -- see `screen_flags` in pipeline.py's
`cmd_screen` docstring comment for why that file exists.

Reports the three registered quantities WITHOUT pass/fail adjudication (per
the harness-build binding invariant: "Do NOT set numeric gate floors
anywhere"). AMENDMENT.md "Gates":

  N1 (IDK): "the F4 explicit-IDK rate at 1.0x exceeds the fresh a_baseline
  F4 rate by a margin whose CI excludes a floor set at sign (exploratory
  reference: 0.04 to 0.67; the floor will be set far below that reference
  but above noise)." Computed as F4-rate(a_dose_1) - F4-rate(a_baseline),
  Wilson CI per arm's own rate PLUS a paired bootstrap CI on the difference
  (see stats_lib.py module docstring for why paired, not two-sample).

  N2 (switch, no graded intermediate): "the judged F2+F3 hedged share among
  non-degenerate rows does not rise above the fresh baseline share by 0.10
  or more at ANY dosed arm". AMBIGUITY FLAGGED FOR SIGN (see harness-build
  report): the AMENDMENT does not say whether "any dosed arm" includes the
  random_direction placebo arm (a_placebo_1) or only the c_hat-dosed arms
  (a_dose_0p5, a_dose_1). This script computes the share at ALL THREE
  non-baseline arms and reports each against the +0.10-over-baseline
  comparison; it does not silently pick a subset. The naming battery's own
  registered rule (which this N2 explicitly reuses "as an upper bound", per
  AMENDMENT.md) evaluated ONLY the three intermediate c_hat doses
  (0.25x/0.5x/0.75x) and separately reported the placebo arms "as
  direction-specificity context" (form-judge AMENDMENT.md "Axis-G rescore"),
  which weakly favors excluding a_placebo_1 from the N2 comparison itself --
  but this cell's reduced ladder has no intermediate c_hat dose between
  a_baseline and a_dose_1 other than a_dose_0p5, so that precedent does not
  map cleanly. Reported, not resolved.

  N3 (direction specificity): "the placebo arm's F4 rate stays within a
  registered band of the fresh baseline rate." Computed as
  F4-rate(a_placebo_1) - F4-rate(a_baseline), same CI treatment as N1.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import stats_lib

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"

DEFAULT_SCREEN_FLAGS_DIR = ANALYSIS / "screen_flags"
DEFAULT_SCREEN_COUNTS = ANALYSIS / "screen_counts.json"
DEFAULT_PAYLOAD_FILE = ANALYSIS / "isnc_axis_payload.jsonl"

BASELINE_ARM = "a_baseline"
DOSED_ARMS = ("a_dose_0p5", "a_dose_1", "a_placebo_1")   # see module docstring "AMBIGUITY FLAGGED FOR SIGN" for N2
N1_DOSE_ARM = "a_dose_1"
N3_PLACEBO_ARM = "a_placebo_1"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_screen_flags(screen_flags_dir: Path) -> dict[str, dict[str, dict[str, bool]]]:
    """Returns {arm: {row_key: {f5_degenerate, f4_explicit_idk, screened_in}}}."""
    out: dict[str, dict[str, dict[str, bool]]] = {}
    for path in sorted(screen_flags_dir.glob("*.jsonl")) if screen_flags_dir.is_dir() else []:
        arm = path.stem
        by_row: dict[str, dict[str, bool]] = {}
        for row in load_jsonl(path):
            by_row[row["row_key"]] = {
                "f5_degenerate": bool(row["f5_degenerate"]),
                "f4_explicit_idk": bool(row["f4_explicit_idk"]),
                "screened_in": bool(row["screened_in"]),
            }
        out[arm] = by_row
    return out


def n1_or_n3_rate_diff(flags_by_arm: dict[str, dict[str, dict[str, bool]]], arm_a: str, arm_b: str, bootstrap_seed: int) -> dict[str, Any]:
    """rate(f4_explicit_idk on arm_b) - rate(f4_explicit_idk on arm_a),
    over the row_key intersection (both arms dose the SAME 400 P_CONFAB
    rows, so the intersection should equal both arms' full row set; a
    non-trivial symmetric difference is reported as a coverage problem, not
    silently dropped)."""
    rows_a = flags_by_arm.get(arm_a, {})
    rows_b = flags_by_arm.get(arm_b, {})
    common = sorted(set(rows_a) & set(rows_b))
    missing_a = sorted(set(rows_b) - set(rows_a))
    missing_b = sorted(set(rows_a) - set(rows_b))

    flags_a = [rows_a[rk]["f4_explicit_idk"] for rk in common]
    flags_b = [rows_b[rk]["f4_explicit_idk"] for rk in common]

    wilson_a = stats_lib.rate_wilson(flags_a)
    wilson_b = stats_lib.rate_wilson(flags_b)
    boot = stats_lib.bootstrap_paired_diff_ci(flags_a, flags_b, seed=bootstrap_seed) if common else None

    return {
        "arm_a": arm_a, "arm_b": arm_b,
        "n_common_row_keys": len(common),
        "n_missing_from_a": len(missing_a), "n_missing_from_b": len(missing_b),
        "rate_a": wilson_a, "rate_b": wilson_b,
        "point_diff_b_minus_a": (wilson_b["rate"] - wilson_a["rate"]) if common else None,
        "bootstrap_diff_ci": boot,
    }


def n2_f2f3_shares(flags_by_arm: dict[str, dict[str, dict[str, bool]]], payload_rows: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts: dict[str, Counter] = {}
    for row in payload_rows:
        label_counts.setdefault(row["arm"], Counter())[row["form_label"]] += 1

    per_arm: dict[str, Any] = {}
    for arm in (BASELINE_ARM,) + DOSED_ARMS:
        arm_flags = flags_by_arm.get(arm, {})
        n_f5 = sum(1 for v in arm_flags.values() if v["f5_degenerate"])
        n_f4 = sum(1 for v in arm_flags.values() if v["f4_explicit_idk"])
        n_screened_in = sum(1 for v in arm_flags.values() if v["screened_in"])
        counts = label_counts.get(arm, Counter())
        n_f1, n_f2, n_f3 = counts.get("F1", 0), counts.get("F2", 0), counts.get("F3", 0)
        n_graded_total = n_f1 + n_f2 + n_f3
        non_degenerate = n_f1 + n_f2 + n_f3 + n_f4
        mismatch = n_graded_total != n_screened_in
        share = ((n_f2 + n_f3) / non_degenerate) if non_degenerate else None
        per_arm[arm] = {
            "n_f1": n_f1, "n_f2": n_f2, "n_f3": n_f3, "n_f4_explicit_idk": n_f4, "n_f5_degenerate": n_f5,
            "n_screened_in_expected": n_screened_in, "n_graded_total": n_graded_total,
            "screened_vs_graded_mismatch": mismatch,
            "n_non_degenerate": non_degenerate, "f2_f3_share": share,
        }

    baseline_share = per_arm[BASELINE_ARM]["f2_f3_share"]
    per_dose: dict[str, Any] = {}
    for arm in DOSED_ARMS:
        share = per_arm[arm]["f2_f3_share"]
        if share is None or baseline_share is None:
            per_dose[arm] = {"share": share, "rises_0p10_or_more_over_baseline": None}
            continue
        delta = share - baseline_share
        per_dose[arm] = {"share": share, "delta_over_baseline": delta, "rises_0p10_or_more_over_baseline": delta >= 0.10}

    return {"baseline_share": baseline_share, "per_arm": per_arm, "per_dosed_arm": per_dose}


def cmd_run(args: argparse.Namespace) -> int:
    screen_flags_dir = Path(args.screen_flags_dir) if args.screen_flags_dir else DEFAULT_SCREEN_FLAGS_DIR
    payload_path = Path(args.payload_file) if args.payload_file else DEFAULT_PAYLOAD_FILE

    flags_by_arm = load_screen_flags(screen_flags_dir)
    payload_rows = load_jsonl(payload_path)

    n1 = n1_or_n3_rate_diff(flags_by_arm, BASELINE_ARM, N1_DOSE_ARM, bootstrap_seed=args.bootstrap_seed)
    n2 = n2_f2f3_shares(flags_by_arm, payload_rows)
    n3 = n1_or_n3_rate_diff(flags_by_arm, BASELINE_ARM, N3_PLACEBO_ARM, bootstrap_seed=args.bootstrap_seed + 1)

    report = {
        "cell": "idk_switch_naming_confirmatory",
        "screen_flags_source": str(screen_flags_dir), "payload_source": str(payload_path),
        "n1_idk_endpoint_jump": n1,
        "n2_no_graded_intermediate": n2,
        "n3_direction_specificity": n3,
        "note": "Quantities and CIs only -- no pass/fail. Floors are REGISTERED_AT_SIGN in AMENDMENT.md Gates / cell.yaml.",
    }
    print(json.dumps(report, indent=2, default=str), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--screen-flags-dir", default=None, help=f"default: {DEFAULT_SCREEN_FLAGS_DIR}")
    ap.add_argument("--payload-file", default=None, help=f"default: {DEFAULT_PAYLOAD_FILE}")
    ap.add_argument("--bootstrap-seed", type=int, default=0, help="seed for the N1/N3 paired bootstrap (a stats seed, unrelated to the generation sampling seed)")
    ap.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
