#!/usr/bin/env python3
"""Roll up the four families' `full_summary.json` outcomes into the
cross-family verdict.

LOCKED cross-family success rule (see AMENDMENT.md "Gates", transcribed
verbatim): CROSS-FAMILY SUCCESS = G1 AND G2 pass in >=3 of 4 run families.
A family that failed G0 (recorded NOT-RUN) is excluded from the denominator
and the bar becomes ">=3 of the families that ran"; if fewer than 3 families
ran at all, the experiment is INCONCLUSIVE, not a pass.

FALSIFIER: <=1 family passes G1+G2 => the mid-band advantage is Qwen-specific
or an artifact. 2 of 4 => mixed, no claim promoted.

This script reads each family's `analysis-committed/<family>/full_summary.json`
if present (a family with no full_summary.json is treated as NOT-RUN, not a
silent zero) and writes `analysis-committed/cross_family_rollup.json`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from family_config import RUN_ORDER  # noqa: E402


def load_family_result(family: str) -> dict | None:
    path = HERE / "analysis-committed" / family / "full_summary.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text())


def run(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)

    per_family = {}
    for family in RUN_ORDER:
        result = load_family_result(family)
        if result is None:
            per_family[family] = {"status": "not_run"}
            continue
        contrast = result["layer_contrast"]
        g1 = contrast["g1_midband_superiority_pass"]
        g2 = contrast["g2_no_cost_regression_pass"]
        g3 = contrast["g3_late_reference_viable_pass"]
        per_family[family] = {
            "status": "run", "g0_smoke_pass": result["layers"] is not None,
            "g1_midband_superiority_pass": g1, "g2_no_cost_regression_pass": g2,
            "g3_late_reference_viable_pass": g3,
            "g1_and_g2_pass": bool(g1 and g2),
            "best_mid_layer": contrast["best_mid_layer"],
            "late_reference_layer": contrast["late_reference_layer"],
            "tighten_delta_best_mid_minus_late": contrast["tighten_delta_best_mid_minus_late"],
            "cost_delta_best_mid_minus_late": contrast["cost_delta_best_mid_minus_late"],
        }

    ran = [f for f in RUN_ORDER if per_family[f]["status"] == "run"]
    passed = [f for f in ran if per_family[f]["g1_and_g2_pass"]]
    n_ran, n_pass = len(ran), len(passed)

    if n_ran < 3:
        verdict = "inconclusive"
        summary = (
            f"Only {n_ran}/4 families ran; per the locked design, fewer than 3 "
            "run families is inconclusive, not a pass or a falsifier."
        )
    elif n_pass >= 3:
        verdict = "success"
        summary = (
            f"CROSS-FAMILY SUCCESS: {n_pass}/{n_ran} run families passed G1+G2 "
            f"(bar: >=3 of {n_ran} run families)."
        )
    elif n_pass <= 1:
        verdict = "falsifier"
        summary = (
            f"FALSIFIER: only {n_pass}/{n_ran} run families passed G1+G2. The "
            "mid-band advantage is Qwen-specific or an artifact."
        )
    else:
        verdict = "mixed_no_claim"
        summary = (
            f"MIXED, NO CLAIM: {n_pass}/{n_ran} run families passed G1+G2 "
            "(between the falsifier and success bars)."
        )

    rollup = {
        "cross_family_success_rule": ">=3 of 4 run families pass G1 AND G2",
        "falsifier_rule": "<=1 of 4 run families pass G1 AND G2 (Qwen-specific/artifact)",
        "mixed_rule": "exactly 2 of 4 run families pass G1 AND G2 (no claim promoted)",
        "inconclusive_rule": "fewer than 3 of 4 families ran at all",
        "n_families_run": n_ran, "n_families_passed_g1_and_g2": n_pass,
        "per_family": per_family, "verdict": verdict, "summary": summary,
    }
    out_path = HERE / "analysis-committed" / "cross_family_rollup.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rollup, indent=2))
    print(json.dumps(rollup, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
