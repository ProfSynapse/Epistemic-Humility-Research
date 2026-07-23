#!/usr/bin/env python3
"""Roll up the families' `full_summary.json` outcomes into the cross-family
verdict.

Cross-family success rule (see AMENDMENT.md "Gates", REFRAMED 2026-07-23):
CROSS-FAMILY SUCCESS = the PRIMARY (absolute mid-band G1 AND G2) passes in >=3
of the families that run past G0. A family that failed G0 (recorded NOT-RUN)
is excluded from the denominator; if fewer than 3 families ran at all, the
experiment is INCONCLUSIVE, not a pass.

FALSIFIER: the PRIMARY passes in <=1 of the run families => mid-band actuation
is Qwen-lineage-specific or an artifact. Exactly 2 => MIXED, no claim promoted.

The primary is ABSOLUTE mid-band actuation; the late-reference arm is a
non-gating descriptive comparator and never enters this roll-up.

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
        primary = result["primary"]
        g1 = primary["g1_midband_actuation_floor_pass"]
        g2 = primary["g2_midband_selectivity_cap_pass"]
        per_family[family] = {
            "status": "run", "g0_smoke_pass": result["layers"] is not None,
            "g1_midband_actuation_floor_pass": g1,
            "g2_midband_selectivity_cap_pass": g2,
            "primary_pass": bool(g1 and g2),
            "best_mid_layer": primary["best_mid_layer"],
            "best_mid_confab_clean_tighten": primary["best_mid_confab_clean_tighten"]["rate"],
            "best_mid_known_correct_cost": primary["best_mid_known_correct_cost"]["rate"],
            "late_reference_layer": primary["late_reference_layer"],
            "secondary_late_reference": primary.get("secondary_late_reference"),
        }

    ran = [f for f in RUN_ORDER if per_family[f]["status"] == "run"]
    passed = [f for f in ran if per_family[f]["primary_pass"]]
    n_ran, n_pass = len(ran), len(passed)

    if n_ran < 3:
        verdict = "inconclusive"
        summary = (
            f"Only {n_ran} families ran; per the design, fewer than 3 run "
            "families is inconclusive, not a pass or a falsifier."
        )
    elif n_pass >= 3:
        verdict = "success"
        summary = (
            f"CROSS-FAMILY SUCCESS: {n_pass}/{n_ran} run families cleared the "
            f"primary (mid-band G1+G2) (bar: >=3 of {n_ran} run families)."
        )
    elif n_pass <= 1:
        verdict = "falsifier"
        summary = (
            f"FALSIFIER: only {n_pass}/{n_ran} run families cleared the primary. "
            "Mid-band actuation is Qwen-lineage-specific or an artifact."
        )
    else:
        verdict = "mixed_no_claim"
        summary = (
            f"MIXED, NO CLAIM: {n_pass}/{n_ran} run families cleared the primary "
            "(between the falsifier and success bars)."
        )

    rollup = {
        "cross_family_success_rule": ">=3 of the run families clear the primary (mid-band G1 AND G2)",
        "falsifier_rule": "<=1 of the run families clear the primary (Qwen-lineage-specific/artifact)",
        "mixed_rule": "exactly 2 of the run families clear the primary (no claim promoted)",
        "inconclusive_rule": "fewer than 3 families ran at all",
        "n_families_run": n_ran, "n_families_passed_primary": n_pass,
        "per_family": per_family, "verdict": verdict, "summary": summary,
    }
    out_path = HERE / "analysis-committed" / "cross_family_rollup.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rollup, indent=2))
    print(json.dumps(rollup, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
