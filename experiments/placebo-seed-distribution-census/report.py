#!/usr/bin/env python3
"""Final report assembler for placebo-seed-distribution-census
(AMENDMENT.md "Deliverable"; gates.yaml sc_criterion).

Implements the registered final rate rule (cell.yaml `write_law.final_rate_rule`;
AMENDMENT.md "Behavioral readout"): per row, refused_final = detector_v2_refused
OR adjudicated_abstention. Detector-refused rows are final by rule and never
entered the grading pool (build_pool.py routes dosed ones to clear-positive
decoys), so each arm's refused_final map is the MERGE of the runlog detector
flags (refused_v2 True -> refused_final True) with the blinded adjudication
output (`analysis/adjudication_applied.jsonl`, written by
`apply_adjudication.py cmd_apply` once every grading shard has passed CG1) for
the detector-non-refused rows. The original build of this module joined over
the adjudication output ALONE, silently dropping every detector-refused row
from the paired join as "missing" -- a defect against the signed rule, found
post-unblind from the n_missing anomaly and corrected to the registered rule
verbatim (see NOTEBOOK.md 2026-07-15).

Joins baseline vs each per-seed dosed arm over the fixed S subsample rows via
`paired_delta.paired_delta_pts`, evaluates the SURVIVES/RETIRED/INDETERMINATE
criterion per family (`criterion.evaluate_family_with_committed_sign` /
`evaluate_family_null_control`), and writes ONLY aggregates (counts, rates,
CIs, verdicts -- no row_key/text) to the COMMITTED
`analysis-committed/census_report.json`.

This module's own correctness is exercised on synthetic fixtures by
`test_census_smoke.py` (not shown there directly -- see
`test_report_smoke.py` for the dedicated synthetic run of `build_report`);
it does NOT itself run any generation or grading and can be invoked at any
scale (a smoke-sized S/K or the full S=300/K=15) once
`adjudication_applied.jsonl` exists for a family.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common  # noqa: E402
import config  # noqa: E402
import criterion  # noqa: E402
from paired_delta import paired_delta_pts  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"


def load_applied_rows(analysis_dir: Path) -> list[dict[str, Any]]:
    return common.load_jsonl(analysis_dir / "adjudication_applied.jsonl")


def index_by_key(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """arm == 'baseline' rows only, keyed by row_key."""
    return {r["row_key"]: r for r in rows if r["arm"] == "baseline"}


def index_by_seed_and_key(rows: list[dict[str, Any]]) -> dict[int, dict[str, dict[str, Any]]]:
    """arm == 'random_direction' rows only, keyed by seed then row_key."""
    out: dict[int, dict[str, dict[str, Any]]] = {}
    for r in rows:
        if r["arm"] != "random_direction":
            continue
        out.setdefault(r["seed"], {})[r["row_key"]] = r
    return out


def merge_refused_final(runlog_by_key: dict[str, dict[str, Any]],
                        adjudicated_by_key: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """The registered final rate rule, per row: refused_final =
    detector_v2_refused OR adjudicated_abstention.

    A runlog row with refused_v2 True is refused_final True by rule (it never
    entered the grading pool). A detector-non-refused row takes its blinded
    adjudication value; if it has none (absent from the applied output), it is
    left out of the returned map and so counts as missing in the paired join,
    never as either value."""
    out: dict[str, dict[str, Any]] = {}
    for rk, lr in runlog_by_key.items():
        if lr.get("refused_v2"):
            out[rk] = {"row_key": rk, "refused_final": True, "detector_refused": True}
        else:
            adj = adjudicated_by_key.get(rk)
            if adj is not None and adj.get("refused_final") is not None:
                out[rk] = {"row_key": rk, "refused_final": bool(adj["refused_final"]),
                           "detector_refused": False}
    return out


def load_runlog_by_key(analysis_dir: Path, family: str, arm: str, seed: Any = None) -> dict[str, dict[str, Any]]:
    if arm == "baseline":
        path = analysis_dir / "runlog" / f"{family}__baseline_reused.jsonl"
    else:
        path = analysis_dir / "runlog" / f"{family}__random_direction__seed{seed}.jsonl"
    return {r["row_key"]: r for r in common.load_jsonl(path)}


def build_family_report(family: str, applied_rows: list[dict[str, Any]], s_row_keys: list[str],
                        accepted_seeds: list[int], analysis_dir: Path) -> dict[str, Any]:
    adjudicated_baseline = index_by_key([r for r in applied_rows if r["cell"] == family])
    adjudicated_dosed = index_by_seed_and_key([r for r in applied_rows if r["cell"] == family])

    baseline_by_key = merge_refused_final(
        load_runlog_by_key(analysis_dir, family, "baseline"), adjudicated_baseline)

    per_seed: list[dict[str, Any]] = []
    deltas_pts: list[float] = []
    seeds_present = sorted(accepted_seeds)
    for seed in seeds_present:
        dosed_by_key = merge_refused_final(
            load_runlog_by_key(analysis_dir, family, "random_direction", seed),
            adjudicated_dosed.get(seed, {}))
        pd = paired_delta_pts(dosed_by_key, baseline_by_key, s_row_keys)
        n_det_dosed = sum(1 for rk in s_row_keys
                          if rk in dosed_by_key and dosed_by_key[rk]["detector_refused"])
        per_seed.append({"seed": seed, **pd, "n_detector_refused_dosed": n_det_dosed})
        deltas_pts.append(pd["delta_pts"])

    committed_sign = config.COMMITTED_SIGN[family]
    if committed_sign == "none":
        crit = criterion.evaluate_family_null_control(family, deltas_pts)
    else:
        crit = criterion.evaluate_family_with_committed_sign(family, committed_sign, deltas_pts)

    n_det_baseline = sum(1 for rk in s_row_keys
                         if rk in baseline_by_key and baseline_by_key[rk]["detector_refused"])
    return {
        "family": family,
        "committed_sign": committed_sign,
        "setpoint_dose_abs": config.SETPOINT_DOSE_ABS[family],
        "n_seeds_present": len(seeds_present),
        "n_seeds_registered": config.K_SEEDS_PER_FAMILY,
        "complete": len(seeds_present) == config.K_SEEDS_PER_FAMILY,
        "n_detector_refused_baseline": n_det_baseline,
        "per_seed": per_seed,
        "criterion": crit,
    }


def build_report(applied_rows: list[dict[str, Any]], subsample_manifest: dict[str, Any],
                 ledger_summary: dict[str, Any], analysis_dir: Path) -> dict[str, Any]:
    families_report = {}
    for family in config.FAMILIES:
        s_row_keys = subsample_manifest["families"][family]["row_keys"]
        accepted_seeds = ledger_summary["families"][family]["accepted_seeds"]
        families_report[family] = build_family_report(
            family, applied_rows, s_row_keys, accepted_seeds, analysis_dir)
    return {
        "subsample_permutation_seed": subsample_manifest.get("seed"),
        "families": families_report,
    }


def cmd_build(args: argparse.Namespace) -> int:
    analysis_dir = Path(args.analysis_dir) if args.analysis_dir else ANALYSIS
    committed_dir = Path(args.committed_dir) if args.committed_dir else COMMITTED
    applied_rows = load_applied_rows(analysis_dir)
    subsample_manifest = common.load_json(committed_dir / "subsample_manifest.json")
    ledger_summary = common.load_json(committed_dir / "sc1_ledger_summary.json")
    report = build_report(applied_rows, subsample_manifest, ledger_summary, analysis_dir)
    common.write_json(committed_dir / "census_report.json", report)
    print(f"[report] wrote {committed_dir / 'census_report.json'}", flush=True)
    for family, fr in report["families"].items():
        print(f"  {family}: n_seeds_present={fr['n_seeds_present']}/{fr['n_seeds_registered']} verdict={fr['criterion']['verdict']}", flush=True)
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
