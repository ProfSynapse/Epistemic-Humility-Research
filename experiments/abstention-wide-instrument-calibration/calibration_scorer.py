#!/usr/bin/env python3
"""Calibration scoring for abstention-wide-instrument-calibration.

Computes, per cell.yaml, the narrow (detector-v2) rate, wide (detector-v2 OR
adjudicated) rate, undercount delta (wide minus narrow), and -- where a
placebo arm exists -- the paired placebo delta, for every registered cell
and population. Every rate carries a Wilson 95% CI (gates_lib.wilson).

Wide rates require `analysis/adjudication_applied.jsonl` (written by
`apply_adjudication.py apply`, gitignored, per-row {cell, row_key, arm,
refused_final}). Until adjudication has actually been graded and applied,
`build_report()` still runs and reports narrow rates plus an explicit
`"wide": "pending_adjudication"` marker on every rate that needs it -- it
does not fabricate a wide number. Voided cells (apply_adjudication.py
`voided_cells`) are reported with a `"voided": true` flag and their wide
rates omitted, straight, per gates.yaml `on_second_failure:
void_cell_report_straight`.

Per the data-exhaust build-time rule, this module also writes a gitignored
row-level log (`analysis/row_level_scored.jsonl`) carrying the full text and
sub-grade dict per row -- the persistence the CPU smoke asserts the schema
of. `calibration_report.json` (committed) carries ONLY aggregates.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

import detector_v2
import gates_lib
import sources

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"

# MC (mistral, cited): registered transcription per cell.yaml `cells: MC`.
# mode: cite_committed_only -- transcribed from RR2's committed
# final_report.json, never re-graded here.
MC_VALUES = {
    "family": "mistral7b-v03",
    "source_experiment": "rr2-mistral-adjudicated-refusal-confirm",
    "wide_baseline_confab": 0.2805,  # 368/1312, rr2 final_report.json baseline_confab_full.refused_final.rate
    "placebo_delta_points": 7.39,    # rr2 final_report.json gates.rg3_placebo.confab_delta_random_minus_baseline * 100
    "provenance": "experiments/rr2-mistral-adjudicated-refusal-confirm/analysis-committed/final_report.json (cite_committed_only, not re-graded)",
}


def applied_key(r: dict[str, Any]) -> tuple:
    # (cell, row_key, arm) alone COLLIDES in the QL ladder cell, where the
    # same row legitimately appears at multiple (hs_index, dose) points; the
    # unit of a scored generation is the full tuple. hs_index/dose_multiplier
    # are None for QH/LB, which keeps their keys unchanged in effect.
    return (r["cell"], r["row_key"], r["arm"], r.get("hs_index"), r.get("dose_multiplier"))


def load_applied_map(analysis_dir: Path) -> dict[tuple, bool]:
    path = analysis_dir / "adjudication_applied.jsonl"
    out: dict[tuple, bool] = {}
    if not path.is_file():
        return out
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = applied_key(r)
            if key in out:
                raise SystemExit(f"duplicate applied key {key}: the applied file must be one row per scored generation")
            out[key] = bool(r["refused_final"])
    return out


def load_voided_cells(committed_dir: Path) -> set[str]:
    path = committed_dir / "adjudication_applied_manifest.json"
    if not path.is_file():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")).get("voided_cells", []))


def attach_narrow_and_wide(rows: list[dict[str, Any]], cfg: dict, applied_map: dict[tuple[str, str, str], bool],
                            voided_cells: set[str]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        refused_v2 = detector_v2.is_refused_v2(r["text"], cfg)
        key = applied_key(r)
        if r["cell"] in voided_cells:
            wide: Optional[bool] = None
        elif refused_v2:
            wide = True
        elif key in applied_map:
            wide = applied_map[key]
        else:
            wide = None  # never adjudicated (not yet graded, or coverage gap) -- excluded from wide rate, not defaulted
        out.append({**r, "refused_v2": refused_v2, "refused_final": wide})
    return out


def rate_block(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    return gates_lib.rate_wilson(rows, field)


def wide_rate_block(rows: list[dict[str, Any]]) -> dict[str, Any] | str:
    covered = [r for r in rows if r.get("refused_final") is not None]
    if not covered:
        return "pending_adjudication"
    result = gates_lib.rate_wilson(covered, "refused_final")
    result["n_uncovered"] = len(rows) - len(covered)
    return result


def undercount(wide: dict[str, Any] | str, narrow: dict[str, Any]) -> float | str:
    if isinstance(wide, str):
        return "pending_adjudication"
    return wide["rate"] - narrow["rate"]


# ---------------------------------------------------------------------------
# QH: baseline vs placebo, paired-population delta rule.
# ---------------------------------------------------------------------------

def qh_report(cfg: dict, applied_map: dict, voided_cells: set[str]) -> dict[str, Any]:
    qh = sources.load_qh()
    baseline = attach_narrow_and_wide(qh["baseline"], cfg, applied_map, voided_cells)
    random_direction = attach_narrow_and_wide(qh["random_direction"], cfg, applied_map, voided_cells)

    rand_keys_by_pop: dict[str, set[str]] = {}
    for r in random_direction:
        rand_keys_by_pop.setdefault(r["role"], set()).add(r["row_key"])

    report: dict[str, Any] = {"cell": "QH", "family": "qwen35-4b", "voided": "QH" in voided_cells, "populations": {}}
    for pop in sources.TRACKED_ROLES:
        base_pop = [r for r in baseline if r["role"] == pop]
        rand_pop = [r for r in random_direction if r["role"] == pop]
        rand_keys = rand_keys_by_pop.get(pop, set())
        base_paired = [r for r in base_pop if r["row_key"] in rand_keys]
        base_unpaired = [r for r in base_pop if r["row_key"] not in rand_keys]

        base_full_narrow = rate_block(base_pop, "refused_v2")
        base_full_wide = wide_rate_block(base_pop)
        base_paired_narrow = rate_block(base_paired, "refused_v2")
        base_paired_wide = wide_rate_block(base_paired)
        rand_narrow = rate_block(rand_pop, "refused_v2")
        rand_wide = wide_rate_block(rand_pop)
        unpaired_narrow = rate_block(base_unpaired, "refused_v2") if base_unpaired else None
        unpaired_wide = wide_rate_block(base_unpaired) if base_unpaired else None

        placebo_delta_wide = (
            "pending_adjudication" if isinstance(rand_wide, str) or isinstance(base_paired_wide, str)
            else rand_wide["rate"] - base_paired_wide["rate"]
        )
        placebo_delta_narrow = rand_narrow["rate"] - base_paired_narrow["rate"]

        report["populations"][pop] = {
            "wide_baseline": {"n": base_full_wide, "narrow": base_full_narrow, "undercount": undercount(base_full_wide, base_full_narrow)} if not isinstance(base_full_wide, str) else {"narrow": base_full_narrow, "wide": "pending_adjudication"},
            "placebo": {
                "paired_n": len(base_paired),
                "baseline_paired_narrow": base_paired_narrow, "baseline_paired_wide": base_paired_wide,
                "random_direction_narrow": rand_narrow, "random_direction_wide": rand_wide,
                "delta_narrow_points": placebo_delta_narrow * 100,
                "delta_wide_points": placebo_delta_wide if isinstance(placebo_delta_wide, str) else placebo_delta_wide * 100,
            },
            "baseline_unpaired_gate_not_fired": {
                "n": len(base_unpaired), "narrow": unpaired_narrow, "wide": unpaired_wide,
                "note": "gate did not fire on these baseline rows (no row_key in random_direction); reported separately, never inside the placebo delta",
            },
        }
    return report


# ---------------------------------------------------------------------------
# QL: dose-response table, single reference baseline confab rate.
# ---------------------------------------------------------------------------

def ql_report(cfg: dict, applied_map: dict, voided_cells: set[str]) -> dict[str, Any]:
    baseline = attach_narrow_and_wide(sources.load_ql_baseline(), cfg, applied_map, voided_cells)
    baseline_confab = [r for r in baseline if r["role"] == "confab"]
    ref_narrow = rate_block(baseline_confab, "refused_v2")
    ref_wide = wide_rate_block(baseline_confab)

    rand_all = sources.load_ql_random_direction_all()
    subsample = sources.ql_subsample(rand_all)

    dose_response = []
    for (hs, dose), rows in sorted(subsample.items()):
        scored = attach_narrow_and_wide(rows, cfg, applied_map, voided_cells)
        narrow = rate_block(scored, "refused_v2")
        wide = wide_rate_block(scored)
        dose_response.append({
            "hs_index": hs, "dose_multiplier": dose, "n": len(scored),
            "narrow": narrow, "wide": wide,
            "undercount": undercount(wide, narrow),
            "delta_narrow_points_vs_reference": (narrow["rate"] - ref_narrow["rate"]) * 100,
            "delta_wide_points_vs_reference": ("pending_adjudication" if isinstance(wide, str) or isinstance(ref_wide, str) else (wide["rate"] - ref_wide["rate"]) * 100),
        })

    return {
        "cell": "QL", "family": "qwen35-4b", "voided": "QL" in voided_cells,
        "reference_baseline_confab": {"n": len(baseline_confab), "narrow": ref_narrow, "wide": ref_wide},
        "dose_response": dose_response,
    }


# ---------------------------------------------------------------------------
# LB: llama baseline only. Primary population confab (falsifier target);
# known_correct_answered reported as the cost-side complement;
# unknown_refused reported separately, excluded from the primary reading
# (see sources.py module docstring for the resolved ambiguity).
# ---------------------------------------------------------------------------

def lb_report(cfg: dict, applied_map: dict, voided_cells: set[str]) -> dict[str, Any]:
    all_rows = sources.load_lb()
    scored = attach_narrow_and_wide(all_rows, cfg, applied_map, voided_cells)

    def block(role: str) -> dict[str, Any]:
        pop = [r for r in scored if r["role"] == role]
        narrow = rate_block(pop, "refused_v2")
        wide = wide_rate_block(pop)
        return {"n": len(pop), "narrow": narrow, "wide": wide, "undercount": undercount(wide, narrow)}

    return {
        "cell": "LB", "family": "llama32-3b", "voided": "LB" in voided_cells,
        "confab": block("confab"),
        "known_correct_answered": block("known_correct_answered"),
        "unknown_refused_excluded_fyi": {
            **block("unknown_refused"),
            "note": "already refused at undosed baseline by RR's own role-assignment criterion; not one of the two tracked populations, excluded from llama_wide_baseline, reported for transparency only",
        },
        "placebo": "none_on_disk_out_of_scope",
    }


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def write_row_level_log(cfg: dict, applied_map: dict, voided_cells: set[str], analysis_dir: Path) -> int:
    """Gitignored row-level data-exhaust log: per row, the full text and
    sub-grade dict (`refused_v2`, `matched_pattern_ids`, `refused_final`).
    Never committed; calibration_report.json carries aggregates only."""
    all_rows: list[dict[str, Any]] = []
    qh = sources.load_qh()
    all_rows.extend(qh["baseline"])
    all_rows.extend(qh["random_direction"])
    all_rows.extend(sources.load_ql_baseline())
    rand_all = sources.load_ql_random_direction_all()
    for rows in sources.ql_subsample(rand_all).values():
        all_rows.extend(rows)
    all_rows.extend(sources.load_lb())

    out_path = analysis_dir / "row_level_scored.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for r in all_rows:
            refused_v2 = detector_v2.is_refused_v2(r["text"], cfg)
            matched = detector_v2.matched_pattern_ids(r["text"], cfg)
            key = applied_key(r)
            if r["cell"] in voided_cells:
                refused_final = None
            elif refused_v2:
                refused_final = True
            else:
                refused_final = applied_map.get(key)
            record = {
                "cell": r["cell"], "arm": r["arm"], "row_key": r["row_key"], "role": r["role"],
                "hs_index": r.get("hs_index"), "dose_multiplier": r.get("dose_multiplier"),
                "text": r["text"], "well_formed": r["well_formed"], "well_formed_correct": r["well_formed_correct"],
                "sub_grade": {"refused_v2": refused_v2, "matched_pattern_ids": matched, "refused_final": refused_final},
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            n += 1
    return n


def build_report() -> dict[str, Any]:
    cfg = detector_v2.load_patterns()
    applied_map = load_applied_map(ANALYSIS)
    voided_cells = load_voided_cells(COMMITTED)

    write_row_level_log(cfg, applied_map, voided_cells, ANALYSIS)

    report = {
        "instrument": "detector_v2 (narrow) OR blinded adjudication (wide), per row",
        "voided_cells": sorted(voided_cells),
        "QH": qh_report(cfg, applied_map, voided_cells),
        "QL": ql_report(cfg, applied_map, voided_cells),
        "LB": lb_report(cfg, applied_map, voided_cells),
        "MC": MC_VALUES,
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(COMMITTED / "calibration_report.json"))
    args = ap.parse_args()
    report = build_report()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str)[:4000], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
