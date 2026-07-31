#!/usr/bin/env python3
"""Axis-G share arithmetic for form-judge-axis-g-rescore.

Reads ONLY graded labels (`apply_judge_grades.py apply-full-pool` output:
analysis/form_judge_full_pool_applied.jsonl, `{row_key, arm, form_label}`)
plus screen counts (`screen_rows.py` output: analysis/screen_counts.json,
ID-free per-arm F5/F4/screened_in totals). No raw text, no row_key-to-text
mapping, ever touches this module.

AMENDMENT.md "Axis-G rescore": "Axis G is then adjudicated: GRADED if the
combined F2+F3 share among non-degenerate rows exceeds 0.15 at one or more
intermediate doses (0.25x, 0.5x, 0.75x) AND exceeds the a_baseline share by
at least 0.10, with the placebo sub-arms reported as direction-specificity
context; otherwise BINARY." Falsifier section adds a third named outcome:
"screen-dominated (fewer than 50 screened-in rows at every intermediate
dose), making the share arithmetic NOT-ADJUDICABLE."

0.15 / 0.10 / 50 are TRANSCRIBED UNCHANGED from the naming battery's own
registration (AMENDMENT.md: "the naming battery's registered axis-G
thresholds re-registered here unchanged"), not gates.yaml numeric floors
invented by this build -- this cell's gates.yaml is left as the unsigned
placeholder per the binding invariant that this harness build must not set
gate floors; these three constants are the AMENDMENT's own prose numbers,
not that file.

"Non-degenerate rows" (the share denominator) = every row that is not F5:
F1 + F2 + F3 (graded) + F4 (screen). Per-arm F1/F2/F3 counts come from the
graded full-pool labels; F4/F5 counts come from screen_counts.json. A
cross-check asserts n_screened_in (from the screen) equals n_F1+n_F2+n_F3
(from the grading) for every arm present in both inputs, since the judge
lane is defined to grade exactly the screened-in remainder and nothing else.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"

DEFAULT_SCREEN_COUNTS = ANALYSIS / "screen_counts.json"
DEFAULT_GRADED_FILE = ANALYSIS / "form_judge_full_pool_applied.jsonl"

INTERMEDIATE_DOSE_ARMS = ("a_dose_0p25", "a_dose_0p5", "a_dose_0p75")
BASELINE_ARM = "a_baseline"

F2F3_SHARE_FLOOR = 0.15
MIN_OVER_BASELINE = 0.10
MIN_SCREENED_IN_FOR_ADJUDICABLE = 50


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


def compute_per_arm_shares(screen_counts: dict[str, Any], graded_rows: list[dict[str, Any]]) -> dict[str, Any]:
    per_arm_screen = screen_counts["per_arm"]
    label_counts: dict[str, Counter] = {}
    for row in graded_rows:
        label_counts.setdefault(row["arm"], Counter())[row["form_label"]] += 1

    result: dict[str, Any] = {}
    for arm, screen in per_arm_screen.items():
        counts = label_counts.get(arm, Counter())
        n_f1, n_f2, n_f3 = counts.get("F1", 0), counts.get("F2", 0), counts.get("F3", 0)
        n_graded_total = n_f1 + n_f2 + n_f3
        n_screened_in = screen["n_screened_in"]
        n_f4 = screen["n_f4_explicit_idk"]
        n_f5 = screen["n_f5_degenerate"]
        non_degenerate = n_f1 + n_f2 + n_f3 + n_f4  # = screen n_total - n_f5, once grading covers all screened_in

        mismatch = (arm in label_counts or n_screened_in > 0) and n_graded_total != n_screened_in
        share = ((n_f2 + n_f3) / non_degenerate) if non_degenerate else None

        result[arm] = {
            "n_f1": n_f1, "n_f2": n_f2, "n_f3": n_f3, "n_f4_explicit_idk": n_f4, "n_f5_degenerate": n_f5,
            "n_screened_in_expected": n_screened_in, "n_graded_total": n_graded_total,
            "screened_vs_graded_mismatch": mismatch,
            "n_non_degenerate": non_degenerate, "f2_f3_share": share,
        }
    return result


def adjudicate_axis_g(per_arm: dict[str, Any]) -> dict[str, Any]:
    baseline = per_arm.get(BASELINE_ARM, {})
    baseline_share = baseline.get("f2_f3_share")

    intermediate_screened_in = [per_arm[a]["n_screened_in_expected"] for a in INTERMEDIATE_DOSE_ARMS if a in per_arm]
    if intermediate_screened_in and all(n < MIN_SCREENED_IN_FOR_ADJUDICABLE for n in intermediate_screened_in):
        return {
            "verdict": "NOT-ADJUDICABLE", "reason": "screen-dominated",
            "detail": f"fewer than {MIN_SCREENED_IN_FOR_ADJUDICABLE} screened-in rows at every intermediate dose",
            "intermediate_screened_in": dict(zip(INTERMEDIATE_DOSE_ARMS, intermediate_screened_in)),
            "baseline_share": baseline_share,
        }

    per_dose_check = {}
    graded_verdict = False
    for arm in INTERMEDIATE_DOSE_ARMS:
        if arm not in per_arm:
            continue
        share = per_arm[arm]["f2_f3_share"]
        if share is None or baseline_share is None:
            per_dose_check[arm] = {"share": share, "clears_floor": None, "clears_over_baseline": None}
            continue
        clears_floor = share > F2F3_SHARE_FLOOR
        clears_over_baseline = (share - baseline_share) >= MIN_OVER_BASELINE
        per_dose_check[arm] = {
            "share": share, "clears_floor": clears_floor, "clears_over_baseline": clears_over_baseline,
            "both_legs": clears_floor and clears_over_baseline,
        }
        if clears_floor and clears_over_baseline:
            graded_verdict = True

    return {
        "verdict": "GRADED" if graded_verdict else "BINARY",
        "baseline_share": baseline_share,
        "per_dose": per_dose_check,
        "share_floor": F2F3_SHARE_FLOOR, "min_over_baseline": MIN_OVER_BASELINE,
    }


def cmd_run(args: argparse.Namespace) -> int:
    screen_counts_path = Path(args.screen_counts) if args.screen_counts else DEFAULT_SCREEN_COUNTS
    graded_path = Path(args.graded_file) if args.graded_file else DEFAULT_GRADED_FILE

    screen_counts = json.loads(screen_counts_path.read_text(encoding="utf-8"))
    graded_rows = load_jsonl(graded_path)

    per_arm = compute_per_arm_shares(screen_counts, graded_rows)
    axis_g = adjudicate_axis_g(per_arm)

    report = {
        "cell": "form_judge_axis_g_rescore",
        "screen_counts_source": str(screen_counts_path), "graded_source": str(graded_path),
        "per_arm": per_arm, "axis_g": axis_g,
    }
    print(json.dumps(report, indent=2, default=str), flush=True)

    mismatches = [arm for arm, v in per_arm.items() if v["screened_vs_graded_mismatch"]]
    if mismatches:
        print(
            f"\n[axis_g_arithmetic] WARNING: screened-in vs graded-total mismatch for arms: "
            f"{mismatches}. The judge lane is expected to grade exactly the screened-in remainder; "
            f"a mismatch means either partial grading or a join error upstream.",
            flush=True,
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--screen-counts", default=None, help=f"default: {DEFAULT_SCREEN_COUNTS}")
    ap.add_argument("--graded-file", default=None, help=f"default: {DEFAULT_GRADED_FILE}")
    ap.set_defaults(func=cmd_run)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
