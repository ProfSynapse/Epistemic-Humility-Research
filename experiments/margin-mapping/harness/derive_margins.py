#!/usr/bin/env python3
"""Per-row margin derivation for margin-mapping (M1).

Scope: qwen35_4b ONLY (mistral7b_v03 is VOID_INSTRUMENT_LOSS per the
2026-07-17 PI-directed scope reduction, NOTEBOOK.md "hs16 forensics" entry;
this script refuses to run for mistral7b_v03).

CPU-only aggregation over EXISTING artifacts. The 11 runlog files
(`analysis/runlog/qwen35_4b__baseline_reused.jsonl` +
`analysis/runlog/qwen35_4b__rung_<tag>.jsonl` x 10) were already graded
inline at generation time (`steer_lib.run_rows` calls `gen_lib.grade_row`,
which runs `detector_v2` -- see gen_lib.py/detector_v2.py, read in full
before writing this). This script performs NO new grading and loads NO
model; it only reads the `well_formed`/`refused_v2` fields already present
per row per rung and derives the cell.yaml `deliverables`.

Deliverables (cell.yaml lines 73-76):
  tipping_dose        smallest ladder dose (dose_abs; the dose-0 baseline
                       counts as the first point, cell.yaml `ladder.
                       dose_zero_rung`) with well_formed AND refused_v2
                       True. Right-censored at the top rung (4.0x) if never
                       observed within the ladder -- never imputed.
  collapse_dose        smallest ladder dose with well_formed False.
                       Right-censored likewise.
  monotonicity_flag    refused_v2 flips True -> False at a LATER rung
                       strictly before this row's collapse_dose (post-
                       collapse reversals are excluded by construction,
                       gates.yaml C1_construct_integrity). The row's margin
                       is still the FIRST tipping dose (unaffected by this
                       flag) per cell.yaml.

SC3 reporting (gates.yaml SC3_coverage) is written as RAW COUNTS / CLASS
LISTS only: censored-row counts per role and the non-monotone row_key list
per role. This script does NOT compute any criterion/scoreboard quantity
(median margins, the P1 observable-bound ratio, setpoint placement, or
retrodiction) -- those compare the raw deliverables against gates.yaml
floors and are reserved for lead adjudication per standing instruction.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import dose_ladder  # noqa: E402

ANALYSIS = HERE.parent / "analysis"
RUNLOG_DIR = ANALYSIS / "runlog"
OUT_DIR = ANALYSIS / "margin_dataset"
COMMITTED = HERE.parent / "analysis-committed"

FAMILY = "qwen35_4b"  # locked scope; mistral7b_v03 is out of scope (see module docstring)

# Ladder points in ascending dose order: dose-0 baseline, then the 10
# registered multipliers (cell.yaml `ladder.multipliers`, config.py
# LADDER_MULTIPLIERS). (multiplier, rung_tag, source_filename)
def _ladder_points() -> list[tuple[float, str, str]]:
    points = [(0.0, "baseline", "qwen35_4b__baseline_reused.jsonl")]
    for m in config.LADDER_MULTIPLIERS:
        tag = dose_ladder.rung_tag(m)
        points.append((m, tag, f"qwen35_4b__rung_{tag}.jsonl"))
    return points


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_population_row_keys() -> dict[str, str]:
    """row_key -> role, from the SC0-committed subsample manifest (the
    registered qwen population: 400 confab subsample + 360 known full)."""
    manifest = json.loads((COMMITTED / "subsample_ids_qwen35_4b.json").read_text())
    assert manifest["family"] == FAMILY
    out: dict[str, str] = {}
    for rk in manifest["confab_subsample"]["row_keys"]:
        out[rk] = "confab"
    for rk in manifest["known_full"]["row_keys"]:
        out[rk] = "known_correct_answered"
    expected_confab = manifest["confab_subsample"]["n_drawn"]
    expected_known = manifest["known_full"]["n"]
    assert len(out) == expected_confab + expected_known, (
        f"population row_key count mismatch: {len(out)} != "
        f"{expected_confab + expected_known}"
    )
    return out


def load_rung_records(filename: str) -> dict[str, dict[str, Any]]:
    path = RUNLOG_DIR / filename
    out: dict[str, dict[str, Any]] = {}
    for r in common.load_jsonl(path):
        rk = r["row_key"]
        if rk in out:
            raise SystemExit(f"derive_margins FAIL: duplicate row_key {rk!r} in {path}")
        out[rk] = r
    return out


def derive_row(row_key: str, role: str, series: list[tuple[float, Optional[dict[str, Any]]]]) -> dict[str, Any]:
    """`series` is the ladder-ordered [(dose_abs, record_or_None), ...] for one
    row_key. A None record means the row was missing at that rung (zero-drop
    violation; recorded, never silently skipped)."""
    n = len(series)
    well_formed = [bool(rec["well_formed"]) if rec is not None else None for _, rec in series]
    refused_v2 = [bool(rec["refused_v2"]) if rec is not None else None for _, rec in series]
    missing_idx = [i for i, (_, rec) in enumerate(series) if rec is None]

    top_dose = series[-1][0]

    collapse_idx: Optional[int] = None
    for i in range(n):
        if well_formed[i] is False:
            collapse_idx = i
            break
    collapse_censored = collapse_idx is None
    collapse_dose = series[collapse_idx][0] if collapse_idx is not None else top_dose

    tipping_idx: Optional[int] = None
    for i in range(n):
        if well_formed[i] is True and refused_v2[i] is True:
            tipping_idx = i
            break
    tipping_censored = tipping_idx is None
    tipping_dose = series[tipping_idx][0] if tipping_idx is not None else top_dose

    # Pre-collapse regime: rungs strictly before collapse_idx, or the whole
    # ladder if the row never collapses (gates.yaml C1: "post-collapse
    # reversals are collapse artifacts and are excluded by construction").
    pre_collapse_end = collapse_idx if collapse_idx is not None else n
    pre_collapse_refused = [refused_v2[i] for i in range(pre_collapse_end) if refused_v2[i] is not None]
    non_monotone = False
    seen_true = False
    for v in pre_collapse_refused:
        if v is True:
            seen_true = True
        elif v is False and seen_true:
            non_monotone = True
            break

    return {
        "row_key": row_key,
        "role": role,
        "well_formed": well_formed,
        "refused_v2": refused_v2,
        "missing_rung_indices": missing_idx,
        "tipping_dose_abs": tipping_dose,
        "tipping_idx": tipping_idx,
        "tipping_censored": tipping_censored,
        "collapse_dose_abs": collapse_dose,
        "collapse_idx": collapse_idx,
        "collapse_censored": collapse_censored,
        "non_monotone_pre_collapse": non_monotone,
    }


def main() -> int:
    points = _ladder_points()
    doses = [m * config.REFERENCE_DOSE_ABS[FAMILY] if m > 0 else 0.0 for m, _, _ in points]

    population = load_population_row_keys()

    rung_tables: list[dict[str, dict[str, Any]]] = []
    file_hashes: dict[str, str] = {}
    for (m, tag, filename), dose in zip(points, doses):
        path = RUNLOG_DIR / filename
        if not path.exists():
            raise SystemExit(f"derive_margins FAIL: missing source file {path}")
        table = load_rung_records(filename)
        rung_tables.append(table)
        file_hashes[filename] = _sha256_of_file(path)
        if len(table) != len(population):
            print(
                f"WARNING rung {tag}: {len(table)} rows in file vs "
                f"{len(population)} in registered population",
                file=sys.stderr,
            )

    zero_drop_report: dict[str, list[str]] = {}
    rows_out: list[dict[str, Any]] = []
    for row_key, role in population.items():
        series: list[tuple[float, Optional[dict[str, Any]]]] = []
        for dose, table in zip(doses, rung_tables):
            series.append((dose, table.get(row_key)))
        missing_files = [points[i][2] for i, (_, rec) in enumerate(series) if rec is None]
        if missing_files:
            zero_drop_report[row_key] = missing_files
        rows_out.append(derive_row(row_key, role, series))

    # unexpected row_keys present in a rung file but absent from the
    # registered population (also a zero-drop-class integrity concern).
    unexpected_by_rung: dict[str, list[str]] = {}
    for (m, tag, filename), table in zip(points, rung_tables):
        extra = sorted(set(table.keys()) - set(population.keys()))
        if extra:
            unexpected_by_rung[filename] = extra

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows_path = OUT_DIR / "qwen35_4b_margin_rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for r in rows_out:
            fh.write(json.dumps(r, sort_keys=True) + "\n")

    def _counts_by_role(pred) -> dict[str, int]:
        out = {"confab": 0, "known_correct_answered": 0}
        for r in rows_out:
            if pred(r):
                out[r["role"]] += 1
        return out

    def _keys_by_role(pred) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {"confab": [], "known_correct_answered": []}
        for r in rows_out:
            if pred(r):
                out[r["role"]].append(r["row_key"])
        return out

    role_totals = {
        "confab": sum(1 for r in rows_out if r["role"] == "confab"),
        "known_correct_answered": sum(1 for r in rows_out if r["role"] == "known_correct_answered"),
    }

    summary = {
        "family": FAMILY,
        "n_rows": len(rows_out),
        "role_totals": role_totals,
        "ladder_doses_abs": doses,
        "ladder_points": [{"multiplier": m, "tag": tag, "filename": fn} for m, tag, fn in points],
        "sc3_zero_drop": {
            "n_rows_with_any_missing_rung": len(zero_drop_report),
            "missing_by_row": zero_drop_report,
            "unexpected_row_keys_by_rung_file": unexpected_by_rung,
        },
        "sc3b_censored_counts_raw": {
            "tipping_censored": _counts_by_role(lambda r: r["tipping_censored"]),
            "collapse_censored": _counts_by_role(lambda r: r["collapse_censored"]),
        },
        "sc3c_non_monotone_raw": {
            "counts": _counts_by_role(lambda r: r["non_monotone_pre_collapse"]),
            "row_keys": _keys_by_role(lambda r: r["non_monotone_pre_collapse"]),
        },
        "note": (
            "RAW counts/classes only (gates.yaml SC3_coverage integrity "
            "reporting). No criterion/scoreboard quantity (median margins, "
            "P1 observable-bound ratio, setpoint placement, retrodiction) "
            "is computed here; those floors are lead-adjudicated."
        ),
    }
    summary_path = OUT_DIR / "qwen35_4b_margin_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    manifest = {
        "family": FAMILY,
        "source_runlog_sha256": file_hashes,
        "margin_rows_sha256": _sha256_of_file(rows_path),
        "margin_rows_path": str(rows_path),
        "margin_summary_sha256": _sha256_of_file(summary_path),
        "margin_summary_path": str(summary_path),
        "n_population_rows": len(population),
    }
    (OUT_DIR / "provenance_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
