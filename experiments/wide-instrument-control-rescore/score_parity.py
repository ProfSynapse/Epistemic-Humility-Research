#!/usr/bin/env python3
"""WG-G0 parity precondition (AMENDMENT.md "Gates"): for every regenerated
arm, the narrow-detector rate must match the committed
`analysis-committed/full_summary.json` rate of its source cell within +/-2.0
percentage points. Any arm outside tolerance stops the cell at
"regeneration-invalid"; Stage 1 does not run and no wide numbers are
reported.

Anchors are READ LIVE from each source cell's own committed
analysis-committed/full_summary.json (never re-typed here), so this script
cannot silently drift from the source cells' registered numbers.

Scope note (report this to the lead, not resolved here): AMENDMENT.md
Design says Stage 1 wide-rescoring is limited to "the hs23 and hs34 gated
arms and their controls" for the 4.6 cell, but `run_contrast.py --mode
full` (the committed entry point, unmodified) always regenerates all four
layers (hs23/hs26/hs29/hs34) -- there is no arm-subset flag. This script
checks WG-G0 parity across ALL FOUR regenerated 4.6 layers (the stronger,
more conservative reading: every arm the pipeline actually produced), while
Stage 1 (score_wide.py) itself only wide-rescores hs23/hs34 per the
Design's explicit scope.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import provenance as prov

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
DEFAULT_CELL_45_COMMITTED = REPO_ROOT / "experiments" / "doubt-gated-caution-tighten" / "analysis-committed" / "full_summary.json"
DEFAULT_CELL_46_COMMITTED = REPO_ROOT / "experiments" / "j-space-calibrated-layer-contrast-qwen3-4b" / "analysis-committed" / "full_summary.json"
DEFAULT_CELL_45_REGEN = HERE / "analysis" / "regenerated" / "cell_45_doubt_gated_caution_tighten" / "full_summary.json"
DEFAULT_CELL_46_REGEN = HERE / "analysis" / "regenerated" / "cell_46_j_space_calibrated_layer_contrast" / "full_summary.json"

TOLERANCE_PP = 2.0
METRICS = ["confab_tighten", "known_correct_cost_control"]


def _pp(rate: float) -> float:
    return rate * 100.0


def check_arm(arm_name: str, committed: dict[str, Any], regen: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"arm": arm_name, "metrics": {}, "pass": True}
    for metric in METRICS:
        c_rate = committed[metric]["rate"]
        r_rate = regen[metric]["rate"]
        diff_pp = _pp(r_rate) - _pp(c_rate)
        ok = abs(diff_pp) <= TOLERANCE_PP
        result["metrics"][metric] = {
            "committed_rate_pct": round(_pp(c_rate), 4),
            "regenerated_rate_pct": round(_pp(r_rate), 4),
            "diff_pp": round(diff_pp, 4),
            "tolerance_pp": TOLERANCE_PP,
            "pass": ok,
        }
        result["pass"] = result["pass"] and ok
    return result


def score_cell_45(committed_path: Path, regen_path: Path) -> list[dict[str, Any]]:
    committed = prov.load_json(committed_path)
    regen = prov.load_json(regen_path)
    arms = ["gated", "random_direction", "permuted_gate"]
    return [check_arm(arm, committed[arm], regen[arm]) for arm in arms]


def score_cell_46(committed_path: Path, regen_path: Path) -> list[dict[str, Any]]:
    committed = prov.load_json(committed_path)
    regen = prov.load_json(regen_path)
    layers = ["hs23", "hs26", "hs29", "hs34"]
    return [check_arm(layer, committed["layers"][layer], regen["layers"][layer]) for layer in layers]


def run(cell_45_committed: Path, cell_45_regen: Path, cell_46_committed: Path, cell_46_regen: Path,
        *, skip_45: bool = False, skip_46: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {"tolerance_pp": TOLERANCE_PP, "cells": {}}

    if not skip_45:
        arm_results_45 = score_cell_45(cell_45_committed, cell_45_regen)
        report["cells"]["doubt-gated-caution-tighten"] = {
            "committed_path": str(cell_45_committed), "regenerated_path": str(cell_45_regen),
            "arms": arm_results_45, "pass": all(a["pass"] for a in arm_results_45),
        }

    if not skip_46:
        arm_results_46 = score_cell_46(cell_46_committed, cell_46_regen)
        report["cells"]["j-space-calibrated-layer-contrast-qwen3-4b"] = {
            "committed_path": str(cell_46_committed), "regenerated_path": str(cell_46_regen),
            "arms": arm_results_46, "pass": all(a["pass"] for a in arm_results_46),
        }

    overall_pass = all(c["pass"] for c in report["cells"].values())
    report["overall_pass"] = overall_pass
    report["verdict"] = "parity_holds" if overall_pass else "regeneration-invalid"
    report["stage_1_authorized"] = overall_pass
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cell-45-committed", type=Path, default=DEFAULT_CELL_45_COMMITTED)
    ap.add_argument("--cell-45-regen", type=Path, default=DEFAULT_CELL_45_REGEN)
    ap.add_argument("--cell-46-committed", type=Path, default=DEFAULT_CELL_46_COMMITTED)
    ap.add_argument("--cell-46-regen", type=Path, default=DEFAULT_CELL_46_REGEN)
    ap.add_argument("--skip-45", action="store_true")
    ap.add_argument("--skip-46", action="store_true")
    ap.add_argument("--out", type=Path, default=HERE / "analysis" / "parity_report.json")
    args = ap.parse_args()

    report = run(
        args.cell_45_committed, args.cell_45_regen, args.cell_46_committed, args.cell_46_regen,
        skip_45=args.skip_45, skip_46=args.skip_46,
    )
    prov.write_json(args.out, report)
    print(json.dumps(report, indent=2))

    if not report["overall_pass"]:
        print(
            "\n[score_parity] WG-G0 FAILED: regeneration-invalid. Stage 1 does not run; "
            "no wide numbers are reported. This is a pre-stated hard stop, not a "
            "configuration to retune.",
            file=__import__("sys").stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
