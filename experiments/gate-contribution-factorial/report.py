#!/usr/bin/env python3
"""Final report assembler for gate-contribution-factorial (AMENDMENT.md
"Deliverable"; gates.yaml P1/P2/P3/S1 + falsifiers).

Ported (logic, generalized to the 5-arm x 2-population x K-seed shape) from
`placebo-seed-distribution-census/report.py`. Implements the REGISTERED
FINAL RATE RULE (cell.yaml / AMENDMENT.md "Behavioral readout"): per row,
`refused_final = detector_v2_refused OR adjudicated_abstention`. Detector-
refused rows are final by rule and NEVER entered the grading pool
(`build_pool.py` routes non-baseline detector-refused rows to clear-positive
decoys, and drops baseline detector-refused rows entirely since they need no
adjudication either) -- so each arm's refused_final map is the MERGE of the
runlog detector flag (`refused_v2` True -> `refused_final` True) with the
blinded adjudication output (`analysis/adjudication_applied.jsonl`) for the
detector-non-refused rows. `merge_refused_final` below is written to the
CORRECTED rule from the start (census's own history: its first draft joined
over the adjudication output ALONE, silently dropping every detector-
refused row as "missing" -- a defect found post-unblind and fixed; that
history is exactly why this port implements the merge, not a naive join,
on the first pass).

Computes, per family: P1 (true_gate__c_hat benefit/cost), P2 (Gap_Sel for
the c_hat leg via a paired bootstrap, and for the random leg via a
bootstrap over the K=5 per-seed medians), P3 (cost_protection for the c_hat
leg via a paired bootstrap, and the random leg descriptively), S1 (direction
specificity vs the census K=15 null). Writes ONLY aggregates (counts,
rates, CIs, verdicts -- no row_key/text) to the COMMITTED
`analysis-committed/factorial_report.json`.

sc3_paired_population_and_coverage is enforced structurally:
`intersect_and_align` computes rates/gaps only over row_keys PRESENT in
every array being paired, and reports the dropped/missing counts alongside
-- never folding a missing row into a rate or gap.

This module's own correctness is exercised on synthetic fixtures by
`test_report_smoke.py`; it does not itself run any generation or grading
and can be invoked once `adjudication_applied.jsonl` exists.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import config  # noqa: E402
import criterion  # noqa: E402
import row_pool  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


# ---------------------------------------------------------------------------
# Runlog / adjudication loading and the registered final-rate merge
# ---------------------------------------------------------------------------

def runlog_tag(family: str, arm: str, seed: Optional[int] = None) -> str:
    """Byte-identical to the tag convention `build_pool.load_family_rows`
    and `run_factorial.py` use to name their RunLog files."""
    if arm == "baseline":
        return f"{family}__baseline_reused"
    if arm == "true_gate_c_hat":
        return f"{family}__true_gate_c_hat_reused"
    if arm == "permuted_gate_c_hat":
        return f"{family}__permuted_gate_c_hat_final"
    if arm == "true_gate_random":
        return f"{family}__true_gate_random__seed{seed}_final"
    if arm == "permuted_gate_random":
        return f"{family}__permuted_gate_random__seed{seed}_final"
    raise ValueError(f"unknown arm {arm!r}")


def load_runlog_by_key(analysis_dir: Path, family: str, arm: str, seed: Optional[int] = None) -> dict[str, dict[str, Any]]:
    path = analysis_dir / "runlog" / f"{runlog_tag(family, arm, seed)}.jsonl"
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def load_applied_rows(analysis_dir: Path) -> list[dict[str, Any]]:
    return common.load_jsonl(analysis_dir / "adjudication_applied.jsonl")


def index_adjudicated(applied_rows: list[dict[str, Any]], family: str, arm: str, seed: Optional[int] = None) -> dict[str, dict[str, Any]]:
    return {
        r["row_key"]: r for r in applied_rows
        if r["cell"] == family and r["arm"] == arm and r.get("seed") == seed
    }


def merge_refused_final(runlog_by_key: dict[str, dict[str, Any]],
                        adjudicated_by_key: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The registered final rate rule, per row: refused_final =
    detector_v2_refused OR adjudicated_abstention.

    A runlog row with refused_v2 True is refused_final True by rule (it
    never entered the grading pool). A detector-non-refused row takes its
    blinded adjudication value; if it has none (absent from the applied
    output -- e.g. its shard was voided, or grading is still pending), it is
    left OUT of the returned map, so it counts as missing in any paired
    join, never as either value."""
    out: dict[str, dict[str, Any]] = {}
    for rk, lr in runlog_by_key.items():
        if lr.get("refused_v2"):
            out[rk] = {"row_key": rk, "refused_final": True, "detector_refused": True}
        else:
            adj = adjudicated_by_key.get(rk)
            if adj is not None and adj.get("refused_final") is not None:
                out[rk] = {"row_key": rk, "refused_final": bool(adj["refused_final"]), "detector_refused": False}
    return out


def load_arm_merged(analysis_dir: Path, applied_rows: list[dict[str, Any]], family: str, arm: str,
                     seed: Optional[int] = None) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    """Returns (merged_by_key, runlog_by_key) -- the latter kept around so
    callers can pull row-level fields (`well_formed`, `role`) that live only
    on the runlog record, not the adjudication/merge output."""
    runlog_by_key = load_runlog_by_key(analysis_dir, family, arm, seed)
    adjudicated_by_key = index_adjudicated(applied_rows, family, arm, seed)
    merged_by_key = merge_refused_final(runlog_by_key, adjudicated_by_key)
    return merged_by_key, runlog_by_key


# ---------------------------------------------------------------------------
# Population rates (sc3 paired coverage)
# ---------------------------------------------------------------------------

def rate_over_keys(merged_by_key: dict[str, dict[str, Any]], row_keys: list[str]) -> dict[str, Any]:
    present = [rk for rk in row_keys if rk in merged_by_key]
    missing = len(row_keys) - len(present)
    successes = sum(1 for rk in present if merged_by_key[rk]["refused_final"])
    rate = common.wilson(successes, len(present))
    rate["n_expected"] = len(row_keys)
    rate["n_missing"] = missing
    return rate


def well_formed_rate_over_keys(runlog_by_key: dict[str, dict[str, Any]], row_keys: list[str]) -> dict[str, Any]:
    """`well_formed` (JSON-parse well-formedness) lives on the runlog record
    directly and applies regardless of refusal/adjudication status, so this
    reads straight from the runlog, over EVERY row in `row_keys` present in
    the runlog (not filtered to non-detector-refused)."""
    present = [rk for rk in row_keys if rk in runlog_by_key]
    missing = len(row_keys) - len(present)
    successes = sum(1 for rk in present if bool(runlog_by_key[rk].get("well_formed")))
    rate = common.wilson(successes, len(present))
    rate["n_expected"] = len(row_keys)
    rate["n_missing"] = missing
    return rate


def intersect_and_align(maps: dict[str, dict[str, dict[str, Any]]], row_keys: list[str]) -> tuple[dict[str, np.ndarray], list[str], dict[str, Any]]:
    """Paired join: only row_keys present in EVERY map in `maps` (and in
    `row_keys`) are used, sorted for determinism. Returns (arrays, ordered
    row_keys used, diagnostics of what was dropped from each side)."""
    present_sets = {name: set(m.keys()) for name, m in maps.items()}
    common_keys = set(row_keys)
    for s in present_sets.values():
        common_keys &= s
    ordered = sorted(common_keys)
    diagnostics = {
        "n_row_keys_requested": len(row_keys),
        "n_paired": len(ordered),
        "n_dropped_per_map": {name: len(set(row_keys) - present_sets[name]) for name in maps},
    }
    arrays = {name: np.asarray([bool(maps[name][rk]["refused_final"]) for rk in ordered], dtype=bool) for name in maps}
    return arrays, ordered, diagnostics


# ---------------------------------------------------------------------------
# P2 / P3 statistic functions (paired bootstrap over aligned boolean arrays)
# ---------------------------------------------------------------------------

def _sel_abs_stat(confab_arm: np.ndarray, confab_baseline: np.ndarray,
                   known_arm: np.ndarray, known_baseline: np.ndarray) -> float:
    return abs(float(np.mean(confab_arm)) - float(np.mean(confab_baseline))) - \
        abs(float(np.mean(known_arm)) - float(np.mean(known_baseline)))


def gap_sel_c_hat_stat_fn(confab_baseline: np.ndarray, confab_true: np.ndarray, confab_permuted: np.ndarray,
                          known_baseline: np.ndarray, known_true: np.ndarray, known_permuted: np.ndarray) -> float:
    sel_true = _sel_abs_stat(confab_true, confab_baseline, known_true, known_baseline)
    sel_permuted = _sel_abs_stat(confab_permuted, confab_baseline, known_permuted, known_baseline)
    return sel_true - sel_permuted


def cost_protection_stat_fn(known_true: np.ndarray, known_permuted: np.ndarray) -> float:
    return float(np.mean(known_permuted)) - float(np.mean(known_true))


def point_sel_abs(arm_arr: np.ndarray, baseline_arr: np.ndarray, known_arm_arr: np.ndarray, known_baseline_arr: np.ndarray) -> float:
    return _sel_abs_stat(arm_arr, baseline_arr, known_arm_arr, known_baseline_arr)


# ---------------------------------------------------------------------------
# Per-family report
# ---------------------------------------------------------------------------

def build_family_report(family: str, analysis_dir: Path, committed_dir: Path,
                        applied_rows: list[dict[str, Any]],
                        subsample_row_keys: list[str]) -> dict[str, Any]:
    confab_full = row_pool.heldout_row_keys_by_role(family)["confab"]
    known_full = row_pool.heldout_row_keys_by_role(family)["known_correct_answered"]

    merged: dict[str, dict[str, dict[str, Any]]] = {}
    runlogs: dict[str, dict[str, dict[str, Any]]] = {}
    for arm in ("baseline", "true_gate_c_hat", "permuted_gate_c_hat"):
        merged[arm], runlogs[arm] = load_arm_merged(analysis_dir, applied_rows, family, arm)

    per_seed_random: dict[int, dict[str, dict[str, dict[str, Any]]]] = {}
    for seed in common.accepted_random_seeds(family, committed_dir=committed_dir,
                                             k_expected=config.K_SEEDS_PER_FAMILY):
        tg_merged, tg_runlog = load_arm_merged(analysis_dir, applied_rows, family, "true_gate_random", seed)
        pg_merged, pg_runlog = load_arm_merged(analysis_dir, applied_rows, family, "permuted_gate_random", seed)
        per_seed_random[seed] = {
            "true_gate_random": {"merged": tg_merged, "runlog": tg_runlog},
            "permuted_gate_random": {"merged": pg_merged, "runlog": pg_runlog},
        }

    # ---- reported rates (Wilson) for every arm x population, full pools ----
    reported_rates: dict[str, Any] = {}
    for arm in ("baseline", "true_gate_c_hat", "permuted_gate_c_hat"):
        reported_rates[arm] = {
            "confab_abstention": rate_over_keys(merged[arm], confab_full),
            "known_false_refusal": rate_over_keys(merged[arm], known_full),
        }
    reported_rates["true_gate_c_hat"]["confab_well_formed"] = well_formed_rate_over_keys(runlogs["true_gate_c_hat"], confab_full)

    per_seed_reported: dict[int, Any] = {}
    for seed, arms in per_seed_random.items():
        per_seed_reported[seed] = {
            "true_gate_random": {
                "confab_abstention": rate_over_keys(arms["true_gate_random"]["merged"], subsample_row_keys),
                "known_false_refusal": rate_over_keys(arms["true_gate_random"]["merged"], known_full),
            },
            "permuted_gate_random": {
                "confab_abstention": rate_over_keys(arms["permuted_gate_random"]["merged"], subsample_row_keys),
                "known_false_refusal": rate_over_keys(arms["permuted_gate_random"]["merged"], known_full),
            },
        }

    # ---- P1: true_gate__c_hat benefit/cost ----
    p1 = criterion.p1_evaluate(
        reported_rates["true_gate_c_hat"]["confab_abstention"],
        reported_rates["true_gate_c_hat"]["confab_well_formed"],
        reported_rates["true_gate_c_hat"]["known_false_refusal"],
    )

    # ---- P2 c_hat leg: paired bootstrap Gap_Sel(c_hat) ----
    confab_maps = {"confab_baseline": merged["baseline"], "confab_true": merged["true_gate_c_hat"], "confab_permuted": merged["permuted_gate_c_hat"]}
    known_maps = {"known_baseline": merged["baseline"], "known_true": merged["true_gate_c_hat"], "known_permuted": merged["permuted_gate_c_hat"]}
    confab_arrays, confab_used, confab_diag = intersect_and_align(confab_maps, confab_full)
    known_arrays, known_used, known_diag = intersect_and_align(known_maps, known_full)
    p2_c_hat_diagnostics = {"confab": confab_diag, "known": known_diag}

    if confab_used and known_used:
        gap_c_hat_ci = common.bootstrap_ci(
            gap_sel_c_hat_stat_fn, {**confab_arrays, **known_arrays},
            pair_groups=[["confab_baseline", "confab_true", "confab_permuted"],
                         ["known_baseline", "known_true", "known_permuted"]],
        )
    else:
        gap_c_hat_ci = {"point": 0.0, "bootstrap_ci_95": [0.0, 0.0], "excludes_zero": False, "n_boot": 0, "seed": None,
                        "degenerate_empty_pairing": True}
    p2_c_hat_leg = criterion.p2_c_hat_evaluate(gap_c_hat_ci)

    # ---- P2 random leg: median over K of per-seed Gap_Sel(random_s) ----
    per_seed_gap_sel_random: list[dict[str, Any]] = []
    for seed, arms in per_seed_random.items():
        c_maps = {"confab_baseline_sub": merged["baseline"], "confab_true_s": arms["true_gate_random"]["merged"], "confab_permuted_s": arms["permuted_gate_random"]["merged"]}
        k_maps = {"known_baseline": merged["baseline"], "known_true_s": arms["true_gate_random"]["merged"], "known_permuted_s": arms["permuted_gate_random"]["merged"]}
        c_arrays, c_used, c_diag = intersect_and_align(c_maps, subsample_row_keys)
        k_arrays, k_used, k_diag = intersect_and_align(k_maps, known_full)
        if c_used and k_used:
            sel_true_s = point_sel_abs(c_arrays["confab_true_s"], c_arrays["confab_baseline_sub"], k_arrays["known_true_s"], k_arrays["known_baseline"])
            sel_permuted_s = point_sel_abs(c_arrays["confab_permuted_s"], c_arrays["confab_baseline_sub"], k_arrays["known_permuted_s"], k_arrays["known_baseline"])
            gap_s = sel_true_s - sel_permuted_s
        else:
            gap_s = None
        per_seed_gap_sel_random.append({
            "seed": seed, "gap_sel_random": gap_s,
            "diagnostics": {"confab": c_diag, "known": k_diag},
        })

    valid_gaps = [e["gap_sel_random"] for e in per_seed_gap_sel_random if e["gap_sel_random"] is not None]
    median_gap_random_ci = common.bootstrap_median_ci(valid_gaps) if valid_gaps else {"k": 0, "median": None, "bootstrap_ci_95": [None, None]}
    if median_gap_random_ci.get("median") is not None:
        p2_random_leg = criterion.p2_random_evaluate(median_gap_random_ci)
    else:
        p2_random_leg = {"gap_sel_random_median": None, "bootstrap_ci_95": [None, None], "passed": False,
                         "is_primary_falsifier_trigger": False, "incomplete": True}

    p2 = criterion.p2_evaluate(p2_c_hat_leg, p2_random_leg)

    # ---- P3 c_hat leg: paired bootstrap cost_protection ----
    if known_used:
        cost_protection_ci = common.bootstrap_ci(
            cost_protection_stat_fn, {"known_true": known_arrays["known_true"], "known_permuted": known_arrays["known_permuted"]},
            pair_groups=[["known_true", "known_permuted"]],
        )
    else:
        cost_protection_ci = {"point": 0.0, "bootstrap_ci_95": [0.0, 0.0], "excludes_zero": False, "n_boot": 0, "seed": None,
                              "degenerate_empty_pairing": True}
    p3_c_hat_leg = criterion.p3_c_hat_evaluate(cost_protection_ci)

    # ---- P3 random leg (descriptive): median over K of per-seed known-cost differentials ----
    per_seed_cost_protection_random: list[dict[str, Any]] = []
    for seed, arms in per_seed_random.items():
        k_maps = {"known_true_s": arms["true_gate_random"]["merged"], "known_permuted_s": arms["permuted_gate_random"]["merged"]}
        k_arrays, k_used, k_diag = intersect_and_align(k_maps, known_full)
        cp_s = float(np.mean(k_arrays["known_permuted_s"])) - float(np.mean(k_arrays["known_true_s"])) if k_used else None
        per_seed_cost_protection_random.append({"seed": seed, "cost_protection_random": cp_s, "diagnostics": k_diag})
    valid_cps = [e["cost_protection_random"] for e in per_seed_cost_protection_random if e["cost_protection_random"] is not None]
    median_cp_random_ci = common.bootstrap_median_ci(valid_cps) if valid_cps else {"k": 0, "median": None, "bootstrap_ci_95": [None, None]}
    p3_random_leg = criterion.p3_random_descriptive(median_cp_random_ci) if median_cp_random_ci.get("median") is not None else \
        {"cost_protection_random_median": None, "bootstrap_ci_95": [None, None], "gates": False, "incomplete": True}

    p3 = criterion.p3_evaluate(p3_c_hat_leg, p3_random_leg)

    # ---- S1: direction specificity ----
    gated_confab_lift_pts = reported_rates["true_gate_c_hat"]["confab_abstention"]["rate"] - reported_rates["baseline"]["confab_abstention"]["rate"]
    s1 = criterion.s1_evaluate(family, gated_confab_lift_pts)

    falsifier = criterion.falsifier_verdict(p1, p2, p3)

    return {
        "family": family,
        "reported_rates": reported_rates,
        "per_seed_reported": per_seed_reported,
        "p1": p1,
        "p2": {**p2, "c_hat_diagnostics": p2_c_hat_diagnostics, "per_seed_gap_sel_random": per_seed_gap_sel_random},
        "p3": {**p3, "per_seed_cost_protection_random": per_seed_cost_protection_random},
        "s1": s1,
        "falsifier": falsifier,
    }


def build_report(analysis_dir: Path, committed_dir: Path) -> dict[str, Any]:
    applied_rows = load_applied_rows(analysis_dir)
    subsample_manifest = common.load_json(committed_dir / "subsample_manifest.json")
    families_report = {}
    for family in config.FAMILIES:
        subsample_row_keys = subsample_manifest["families"][family]["row_keys"]
        families_report[family] = build_family_report(family, analysis_dir, committed_dir, applied_rows, subsample_row_keys)
    return {"config_sha_note": "see analysis-committed/staging_manifest.json for full provenance", "families": families_report}


def cmd_build(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    report = build_report(analysis_dir, committed_dir)
    common.write_json(committed_dir / "factorial_report.json", report)
    print(f"[report] wrote {committed_dir / 'factorial_report.json'}", flush=True)
    for family, fr in report["families"].items():
        print(f"  {family}: P1={fr['p1']['passed']} P2={fr['p2']['passed']} P3={fr['p3']['passed']} "
              f"S1={fr['s1']['passed']} gate_axis_falsified={fr['falsifier']['gate_axis_falsified']}", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--analysis-dir", default=None)
    ap.add_argument("--committed-dir", default=None)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
