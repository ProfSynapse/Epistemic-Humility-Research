#!/usr/bin/env python3
"""Analysis SKELETON for margin-separation-fine-ladder (M1b) (cell.yaml
`criteria`/`analysis`; gates.yaml `criteria`/`SC3_coverage_and_merge_audit`).

CPU-only. Implements the registered merge rule, the P1 criterion (both
legs + observable bound), the C1 non-monotone construct-integrity gate, and
the SC3 partition/merge-provenance audit, so the lead can review the
CRITERION IMPLEMENTATION before any result exists. Per the harness-build
task: DO NOT run this on real data in this phase -- the four new-rung
runlogs (`{FAMILY}__refined_rung_<tag>.jsonl`) this script reads do not
exist yet (no generation has been launched); `main()` raises SystemExit
immediately if any of them, or the drift/preflight gate markers, are
missing, rather than silently analyzing a partial or absent dataset.

Implements:
  - merge_rule: per cell.yaml `population.merge_rule` --
      idx_le_4 / idx_ge_6_or_censored: carry M1's tipping_dose_abs unchanged
        (from the staged margin_dataset).
      idx_5_refined (53 rows): smallest of the 4 new-rung doses with
        refused_v2 AND well_formed True in the FRESH generation; if none
        qualify, retain M1's own 0.75x tipping value (never imputed to a
        new-rung dose). Rows with all four new generations non-well-formed
        are additionally flagged as fine-collapse (descriptive only).
  - median over all 400 merged confab values + bootstrap 95% CI (seed
    48260719, resampling row indices, gates.yaml `statistics`).
  - P1 leg_a (median <= reference setpoint), leg_b (ported verbatim from
    M1's OWN `margin-mapping/analysis/scoreboard/compute_scoreboard.py`
    `neither_tipped_nor_collapsed`, evaluated on the pinned margin_dataset's
    known-role tipping_idx/collapse_idx at M1's OWN hp_idx=7 (1.5x) -- the
    known rows are RG0-reused byte-identically, so this IS "evaluated on M1
    runlogs reused byte-identically under RG0" per gates.yaml), and the
    observable-bound pass/fail surface (median <= 7.564912750679985).
  - C1 non-monotone fraction over the 53-row merged fine sequence {0.5x(M1),
    0.55, 0.6, 0.65, 0.7, 0.75x(M1)}.
  - SC3 merge-provenance audit: every one of the 400 confab rows traceable
    to exactly one provenance class, counts asserted equal to 181/166/53.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent
EXPERIMENT_DIR = HERE.parent
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402
import dose_ladder  # noqa: E402

ANALYSIS = EXPERIMENT_DIR / "analysis"
COMMITTED = EXPERIMENT_DIR / "analysis-committed"
STAGED = ANALYSIS / "staged_inputs"
RUNLOG_DIR = ANALYSIS / "runlog"
PREFLIGHT_DIR = ANALYSIS / "preflight"

FAMILY = "qwen35_4b"


def _new_rung_runlog_path(multiplier: float) -> Path:
    tag = dose_ladder.rung_tag(multiplier)
    return RUNLOG_DIR / f"{FAMILY}__refined_rung_{tag}.jsonl"


def _require_new_generations_exist() -> None:
    missing = [p for m in config.NEW_RUNGS if not (p := _new_rung_runlog_path(m)).is_file()]
    if missing:
        raise SystemExit(
            f"[analysis] REFUSING: {len(missing)} new-rung runlog(s) missing: {missing}. "
            f"This is expected in the harness-build phase (no generation has been "
            f"launched); do not run this script until generate_refined.py has completed."
        )


def load_margin_dataset() -> list[dict[str, Any]]:
    path = STAGED / config.PINNED_INPUTS["margin_dataset"]["dest"]
    return common.load_jsonl(path)


def load_refined_row_keys() -> list[str]:
    payload = common.load_json(COMMITTED / "refined_subset_ids_qwen35_4b.json")
    return sorted(payload["row_keys"])


def load_new_rung_records() -> dict[float, dict[str, dict[str, Any]]]:
    """multiplier -> row_key -> record, for the 4 new rungs."""
    out: dict[float, dict[str, dict[str, Any]]] = {}
    for m in config.NEW_RUNGS:
        table = {r["row_key"]: r for r in common.load_jsonl(_new_rung_runlog_path(m))}
        out[m] = table
    return out


def load_staged_endpoint_records() -> dict[float, dict[str, dict[str, Any]]]:
    """M1's own 0.5x/0.75x endpoint runlogs (staged), keyed by row_key --
    used for the C1 monotonicity sequence and merge audit, NOT for the
    merged-margin value itself (that comes from the pinned margin_dataset's
    already-derived tipping_dose_abs for idx_le_4/idx_ge_6_or_censored
    rows)."""
    out: dict[float, dict[str, dict[str, Any]]] = {}
    out[0.5] = {r["row_key"]: r for r in common.load_jsonl(STAGED / config.PINNED_INPUTS["rung_0p5"]["dest"])}
    out[0.75] = {r["row_key"]: r for r in common.load_jsonl(STAGED / config.PINNED_INPUTS["rung_0p75"]["dest"])}
    return out


# ---------------------------------------------------------------------------
# Merge rule (cell.yaml `population.merge_rule`; Decision record item 2)
# ---------------------------------------------------------------------------

def merge_refined_row(
    row_key: str, m1_margin_dataset_row: dict[str, Any],
    new_rung_records: dict[float, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """One of the 53 refined rows. Returns the merged margin dose_abs plus
    provenance/flags. `new_rung_records[m][row_key]` may be absent (zero-drop
    reporting, never silently skipped)."""
    m1_075_dose_abs = m1_margin_dataset_row["tipping_dose_abs"]  # == 9.456140938349982 for every idx==5 row

    candidates: list[tuple[float, float]] = []  # (dose_abs, multiplier), ascending multiplier order
    missing_rungs: list[float] = []
    all_non_well_formed = True
    for m in config.NEW_RUNGS:
        rec = new_rung_records.get(m, {}).get(row_key)
        if rec is None:
            missing_rungs.append(m)
            continue
        well_formed = bool(rec["well_formed"])
        refused_v2 = bool(rec["refused_v2"])
        if well_formed:
            all_non_well_formed = False
        if well_formed and refused_v2:
            dose_abs = dose_ladder.rung_dose_abs(FAMILY, m)
            candidates.append((dose_abs, m))

    if candidates:
        merged_dose_abs = min(candidates)[0]
        fine_tipped = True
        fine_collapse_flag = False
    else:
        merged_dose_abs = m1_075_dose_abs
        fine_tipped = False
        # "A refined row whose four fine generations are all non-well-formed
        # also retains the M1 0.75x value ... additionally flagged and
        # reported descriptively as fine-collapse" (cell.yaml merge_rule).
        fine_collapse_flag = all_non_well_formed and not missing_rungs

    return {
        "row_key": row_key,
        "merged_dose_abs": merged_dose_abs,
        "fine_tipped_at_new_rung": fine_tipped,
        "fine_collapse_flag": fine_collapse_flag,
        "missing_new_rungs": missing_rungs,
        "m1_075_dose_abs_retained_if_no_fine_tip": m1_075_dose_abs,
    }


def build_merged_confab_dataset(
    margin_rows: list[dict[str, Any]],
    refined_row_keys: list[str],
    new_rung_records: dict[float, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    refined_set = set(refined_row_keys)
    by_row_key = {r["row_key"]: r for r in margin_rows if r["role"] == "confab"}

    merged: list[dict[str, Any]] = []
    provenance_counts = {"idx_le_4": 0, "idx_5_refined": 0, "idx_ge_6_or_censored": 0}
    fine_collapse_flags: list[str] = []
    missing_from_margin_dataset: list[str] = []

    for row_key in refined_row_keys:
        r = by_row_key.get(row_key)
        if r is None:
            missing_from_margin_dataset.append(row_key)
            continue
        merge_result = merge_refined_row(row_key, r, new_rung_records)
        merged.append({"row_key": row_key, "provenance": "idx_5_refined", "merged_dose_abs": merge_result["merged_dose_abs"]})
        provenance_counts["idx_5_refined"] += 1
        if merge_result["fine_collapse_flag"]:
            fine_collapse_flags.append(row_key)

    for row_key, r in by_row_key.items():
        if row_key in refined_set:
            continue
        idx = r["tipping_idx"]
        censored = r["tipping_censored"]
        if censored or (idx is not None and idx >= config.M1_TIPPING_IDX_GE):
            provenance = "idx_ge_6_or_censored"
        elif idx is not None and idx <= config.M1_TIPPING_IDX_LE:
            provenance = "idx_le_4"
        else:
            raise SystemExit(f"[analysis] SC3 FAIL: row_key {row_key!r} tipping_idx={idx!r} censored={censored!r} uncovered by partition.")
        merged.append({"row_key": row_key, "provenance": provenance, "merged_dose_abs": r["tipping_dose_abs"]})
        provenance_counts[provenance] += 1

    return {
        "merged_rows": merged,
        "provenance_counts": provenance_counts,
        "fine_collapse_flagged_row_keys": fine_collapse_flags,
        "missing_from_margin_dataset": missing_from_margin_dataset,
    }


# ---------------------------------------------------------------------------
# C1 non-monotone (gates.yaml C1_construct_integrity; cell.yaml deliverables)
# ---------------------------------------------------------------------------

def non_monotone_fine_sequence(
    row_key: str,
    endpoint_records: dict[float, dict[str, dict[str, Any]]],
    new_rung_records: dict[float, dict[str, dict[str, Any]]],
) -> Optional[bool]:
    """abstention non-monotone across {0.5x(M1), 0.55, 0.6, 0.65, 0.7,
    0.75x(M1)} -- refused_v2 flips True -> False at a later point, pre-
    collapse (well_formed False rungs excluded, same convention as M1's
    derive_margins.py `non_monotone_pre_collapse`). Returns None if any
    point is missing (reported, never silently imputed)."""
    sequence = [0.5, 0.55, 0.6, 0.65, 0.7, 0.75]
    points: list[Optional[dict[str, Any]]] = []
    for m in sequence:
        if m in (0.5, 0.75):
            rec = endpoint_records[m].get(row_key)
        else:
            rec = new_rung_records.get(m, {}).get(row_key)
        points.append(rec)
    if any(p is None for p in points):
        return None

    well_formed = [bool(p["well_formed"]) for p in points]
    refused_v2 = [bool(p["refused_v2"]) for p in points]
    collapse_idx = next((i for i, wf in enumerate(well_formed) if not wf), None)
    pre_collapse_end = collapse_idx if collapse_idx is not None else len(sequence)

    seen_true = False
    for i in range(pre_collapse_end):
        if refused_v2[i]:
            seen_true = True
        elif seen_true:
            return True
    return False


# ---------------------------------------------------------------------------
# P1 criterion (cell.yaml `criteria.separation_censoring_aware`; gates.yaml
# `criteria.P1_separation_censoring_aware`)
# ---------------------------------------------------------------------------

def leg_b_known_rows(margin_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Ported verbatim from M1's OWN compute_scoreboard.py
    `neither_tipped_nor_collapsed`, hp_idx=7 (the 1.5x rung on M1's 10-rung
    series index). Evaluated on the known-role rows of the pinned
    margin_dataset -- these are RG0-reused byte-identically from M1's own
    rung_1p5/rung_2p0 runlogs, so this satisfies gates.yaml's "evaluated on
    M1 runlogs reused byte-identically under RG0"."""
    known_rows = [r for r in margin_rows if r["role"] == "known_correct_answered"]
    if len(known_rows) != config.KNOWN_ROWS_N:
        raise SystemExit(f"[analysis] SC3 FAIL: {len(known_rows)} known rows in margin_dataset, expected {config.KNOWN_ROWS_N}.")

    hp_idx = config.HIGHEST_PRECOLLAPSE_RUNG_IDX_M1

    def neither(r: dict[str, Any]) -> bool:
        tip_ok = (r["tipping_idx"] is None) or (r["tipping_idx"] > hp_idx)
        col_ok = (r["collapse_idx"] is None) or (r["collapse_idx"] > hp_idx)
        return tip_ok and col_ok

    n_neither = sum(1 for r in known_rows if neither(r))
    wilson = common.wilson(n_neither, len(known_rows))
    return {"n_neither": n_neither, "n_known": len(known_rows), "wilson": wilson, "condition_ge_0.50": wilson["rate"] >= 0.50}


def median_bootstrap_ci(values: list[float]) -> dict[str, Any]:
    import numpy as np

    arr = np.asarray(values, dtype=np.float64)
    point = float(np.median(arr))
    rng = np.random.default_rng(config.BOOTSTRAP_SEED)
    n = len(arr)
    boots = np.empty(config.BOOTSTRAP_N_RESAMPLES, dtype=np.float64)
    for i in range(config.BOOTSTRAP_N_RESAMPLES):
        idx = rng.integers(0, n, n)
        boots[i] = np.median(arr[idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"median": point, "bootstrap_ci_95": [float(lo), float(hi)], "n_boot": config.BOOTSTRAP_N_RESAMPLES, "seed": config.BOOTSTRAP_SEED}


def main() -> int:
    _require_new_generations_exist()

    margin_rows = load_margin_dataset()
    refined_row_keys = load_refined_row_keys()
    new_rung_records = load_new_rung_records()
    endpoint_records = load_staged_endpoint_records()

    merge_result = build_merged_confab_dataset(margin_rows, refined_row_keys, new_rung_records)
    counts = merge_result["provenance_counts"]
    if counts != config.EXPECTED_PARTITION:
        raise SystemExit(f"[analysis] SC3 FAIL: merge provenance counts {counts} != expected {config.EXPECTED_PARTITION}.")
    n_total = sum(counts.values())
    if n_total != config.EXPECTED_CONFAB_TOTAL:
        raise SystemExit(f"[analysis] SC3 FAIL: merged confab total {n_total} != expected {config.EXPECTED_CONFAB_TOTAL}.")

    merged_values = [r["merged_dose_abs"] for r in merge_result["merged_rows"]]
    median_stat = median_bootstrap_ci(merged_values)
    bound_point = config.NUMERATOR_DOSE_ABS / median_stat["median"]

    leg_a_holds = median_stat["median"] <= config.REFERENCE_DOSE_ABS[FAMILY]
    leg_b = leg_b_known_rows(margin_rows)
    p1_pass = leg_a_holds and leg_b["condition_ge_0.50"] and (median_stat["median"] <= config.FLOOR_EXACT_RUNG_DOSE_ABS)

    non_monotone_flags = {
        rk: non_monotone_fine_sequence(rk, endpoint_records, new_rung_records)
        for rk in refined_row_keys
    }
    n_flagged = sum(1 for v in non_monotone_flags.values() if v is True)
    n_unresolvable = sum(1 for v in non_monotone_flags.values() if v is None)
    c1_fraction = n_flagged / len(refined_row_keys)
    c1_pass = c1_fraction <= config.NON_MONOTONE_CEILING_REFINED

    report = {
        "sc3_merge_provenance_counts": counts,
        "sc3_pass": counts == config.EXPECTED_PARTITION,
        "fine_collapse_flagged_row_keys": merge_result["fine_collapse_flagged_row_keys"],
        "merged_confab_median": median_stat,
        "observable_bound_point": bound_point,
        "observable_bound_floor": config.OBSERVABLE_BOUND_FLOOR,
        "P1_leg_a_median_le_setpoint": leg_a_holds,
        "P1_leg_b_known_rows": leg_b,
        "P1_pass": p1_pass,
        "C1_non_monotone_fraction": c1_fraction,
        "C1_n_flagged": n_flagged,
        "C1_n_unresolvable_missing_point": n_unresolvable,
        "C1_pass": c1_pass,
        "note": "SKELETON ONLY -- not executed on real data in the harness-build phase.",
    }
    common.write_json(ANALYSIS / "m1b_analysis_report.json", report)
    print(f"[analysis] wrote {ANALYSIS / 'm1b_analysis_report.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
