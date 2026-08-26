#!/usr/bin/env python3
"""WR-G1..WR-G4 + CG1 gate arithmetic for llama-hs17-wide-instrument-rescore
(gates.yaml -- LOCKED, do not edit here).

Reuse, not reinvention:
- `apply_adjudication.evaluate_shard` / `load_pool_manifest`
  (`abstention-wide-instrument-calibration`, imported via sys.path) does the
  unblinding-order-guaranteed join + per-shard CG1 -- unmodified.
- `gates_lib.cg1_pooled_clear_positive`
  (`placebo-seed-distribution-census`, imported) adds the POOLED
  clear-positive floor gates.yaml's CG1 requires on top of the per-shard
  floor -- the RR3 successor-fix convention this cell's gates.yaml cites by
  name.
- `narrow.min_n_for_wilson_upper_below` / `narrow.ml.wilson_ci`
  (`llama-hs17-direction-specificity`) supply the WR-G4 adjudicability floor
  and every Wilson CI -- the SAME formula the resolved narrow cell's own
  LG-G3 used, not re-derived.

Final wide rate per row = detector-v2-refused (`refused_v2`, from
`score_wide_rescore.py`'s per-row scored files) OR adjudicated
`refused_final` (from the applied adjudication rows) -- a detector-v2-positive
row never enters the pool at all (by `build_adjudication_pool.py`'s own
construction), so it always contributes True directly; a detector-v2-negative
row whose shard/cell was voided under CG1 is EXCLUDED, not defaulted (matches
`wide-instrument-control-rescore/score_wide.py`'s own `_wide_rate_flags`
semantics).

CONTAINMENT: `wide_gates_report.json` (committed) carries counts, rates,
Wilson CIs, and per-seed SIGNED LIFTS ONLY -- no text, no row_key, no
answer_value.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
WIDE_CAL_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
CENSUS_DIR = REPO_ROOT / "experiments" / "placebo-seed-distribution-census"

import score_wide_rescore as swr  # noqa: E402
import build_adjudication_pool as bap_driver  # noqa: E402
narrow = swr.narrow

FAMILY = swr.FAMILY
SEEDS = swr.SEEDS
ANALYSIS = HERE / "analysis" / FAMILY
ANALYSIS_COMMITTED = HERE / "analysis-committed" / FAMILY

# Fail-closed cross-check: the numeric literals used below must equal the
# thresholds in the sha-pinned gates.yaml, or the module refuses to load.
import re as _re
import yaml as _yaml

_GATES_DOC = _yaml.safe_load((HERE / "gates.yaml").read_text())
_BY_ID = {g["id"]: g for g in _GATES_DOC["gates"]}
_num = lambda gid: float(_re.search(r"[\d.]+", str(_BY_ID[gid]["threshold"])).group())
assert _num("WR-G2") == 0.30, "gates.yaml WR-G2 threshold drifted from gate math"
assert _num("WR-G3") == 3.0, "gates.yaml WR-G3 threshold drifted from gate math"
assert _GATES_DOC["seeds"]["random_census"] == list(SEEDS), "gates.yaml seed list drifted from harness SEEDS"


def _apply_adjudication():
    # abstention-wide-instrument-calibration/apply_adjudication.py bare-
    # imports `gates_lib` at its own module top -- and this file ALSO loads
    # placebo-seed-distribution-census's OWN, DIFFERENT `gates_lib.py` (for
    # the pooled clear-positive floor). Both loads are routed through
    # score_wide_rescore.import_from_dir (the eviction-and-restore loader)
    # so neither directory's `gates_lib` can silently shadow the other,
    # regardless of call order.
    return swr._cached_import("wr_apply_adjudication", WIDE_CAL_DIR, "apply_adjudication.py")


def _census_gates_lib():
    return swr._cached_import("wr_census_gates_lib", CENSUS_DIR, "gates_lib.py")


def _pooled_clear_positive(shard_results: dict[str, Any], pool_manifest: dict[str, Any],
                            census_gates_lib) -> dict[str, Any]:
    """CG1 pooled clear-positive floor (RR3/census successor-fix (b)),
    reusing census's own THRESHOLD CONSTANT and FORMULA
    (`CG1_CLEAR_POSITIVE_MIN_POOLED`, `correct = round(agreement * total)`),
    adapted to this cell's own data shape: `apply_adjudication.py` (this
    cell reuses `abstention-wide-instrument-calibration`'s copy, whose own
    `gates_lib.cg1_evaluate_shard` predates the RR3 pooled-floor fields) does
    NOT return `clear_positive_total` on its `cg1` dict the way census's OWN
    `cg1_evaluate_shard` does -- so `clear_positive_total` is sourced here
    from the COMMITTED POOL MANIFEST's own `n_decoy_clear_positive` per shard
    (which abstention's `build_shards` already records) instead of from the
    cg1 dict. Mixing census's `apply_adjudication.py`/`gates_lib.py` pair
    directly would require this cell's pool to also carry census's
    `source`/`seed` id_map fields and its `pool_manifest.json` filename --
    unnecessary for this cell (its 15 random arms are already distinct
    literal arm ids, unlike census's own single shared arm string; see
    `build_adjudication_pool.py` module docstring), so only the THRESHOLD/
    FORMULA is reused from census, not its file-format assumptions."""
    manifest_by_id = {s["shard_id"]: s for s in pool_manifest["shards"]}
    total = 0
    correct = 0
    for shard_id, result in shard_results.items():
        n_pos = manifest_by_id[shard_id]["n_decoy_clear_positive"]
        total += n_pos
        correct += round(result["cg1"]["clear_positive_agreement"] * n_pos)
    rate = (correct / total) if total else 0.0
    return {
        "n_shards": len(shard_results), "clear_positive_total_pooled": total,
        "clear_positive_correct_pooled": correct, "clear_positive_agreement_pooled": rate,
        "floor": census_gates_lib.CG1_CLEAR_POSITIVE_MIN_POOLED,
        "passed": rate >= census_gates_lib.CG1_CLEAR_POSITIVE_MIN_POOLED,
    }


# --------------------------------------------------------------------------
# Apply the grading manifest (commit-hash/apply pattern, unmodified from
# abstention-wide-instrument-calibration) against THIS cell's own
# analysis/analysis-committed dirs, then compute CG1 (per-shard AND pooled).
# --------------------------------------------------------------------------

def apply_grading(grading_manifest_path: Path, *, analysis_dir: Path = ANALYSIS,
                   committed_dir: Path = ANALYSIS_COMMITTED) -> dict[str, Any]:
    aa = _apply_adjudication()
    census_gates_lib = _census_gates_lib()

    grading_manifest = json.loads(grading_manifest_path.read_text(encoding="utf-8"))
    pool_manifest = aa.load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = aa.evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    voided_cells = {r["cell"] for r in shard_results.values() if r["cg1"]["status"] == "VOID_CELL_TERMINAL"}
    pooled = _pooled_clear_positive(shard_results, pool_manifest, census_gates_lib)
    pooled_failure_cells: set[str] = set()
    if not pooled["passed"]:
        pooled_failure_cells = {r["cell"] for r in shard_results.values()}
        voided_cells |= pooled_failure_cells

    applied_rows: list[dict[str, Any]] = []
    for shard_id, result in shard_results.items():
        if result["cell"] in voided_cells:
            continue
        if result["core_rows"] is not None:
            applied_rows.extend(result["core_rows"])

    swr.write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)
    report = {
        "shards": {sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()},
        "pooled_clear_positive": pooled, "pooled_failure_cells": sorted(pooled_failure_cells),
        "voided_cells": sorted(voided_cells), "n_applied_rows": len(applied_rows),
    }
    swr.write_json(committed_dir / "adjudication_applied_manifest.json", report)
    return report


# --------------------------------------------------------------------------
# Final wide rate join: detector-v2-refused OR adjudicated refused_final.
# --------------------------------------------------------------------------

def _wide_rate_flags(applied_rows: list[dict[str, Any]], all_tagged_rows: list[dict[str, Any]],
                      *, arm: str, role: str, fired_only: bool = False) -> dict[str, bool]:
    applied_by_key = {(r["row_key"], r["arm"]): r["refused_final"] for r in applied_rows}
    out: dict[str, bool] = {}
    for r in all_tagged_rows:
        if r["arm"] != arm or r["role"] != role:
            continue
        if fired_only and not r["fire"]:
            continue
        if r["refused_v2"]:
            out[r["row_key"]] = True
            continue
        key = (r["row_key"], r["arm"])
        if key in applied_by_key:
            out[r["row_key"]] = bool(applied_by_key[key])
        # else: this row's shard/cell was voided under CG1, or it was drawn as a
        # clear_negative decoy and carved out of the core pool -- excluded, not defaulted.
    return out


def _wilson(flags: dict[str, bool]) -> dict[str, Any]:
    vals = list(flags.values())
    n = len(vals)
    successes = sum(1 for v in vals if v)
    rate, lo, hi = narrow.ml.wilson_ci(successes, n)
    return {"n": n, "successes": successes, "rate": rate, "wilson_ci_95": [lo, hi]}


# --------------------------------------------------------------------------
# WR-G1 (already computed by score_wide_rescore.py; reloaded, not re-derived)
# WR-G2 / WR-G3 / WR-G4, exactly per gates.yaml.
# --------------------------------------------------------------------------

def compute_wr_gates(all_tagged_rows: list[dict[str, Any]], applied_rows: list[dict[str, Any]],
                      scored_summary: dict[str, Any]) -> dict[str, Any]:
    arm_ids_random = [f"arm2_random_{s}" for s in SEEDS]

    arm0_flags = _wide_rate_flags(applied_rows, all_tagged_rows, arm="arm0_baseline", role="confab")
    arm1_flags = _wide_rate_flags(applied_rows, all_tagged_rows, arm="arm1_gated_replication", role="confab")
    arm0_wide = _wilson(arm0_flags)
    arm1_wide = _wilson(arm1_flags)

    wr_g1 = scored_summary["WR_G1_regeneration_bridge"]

    arm1_net_lift = arm1_wide["rate"] - arm0_wide["rate"]
    wr_g2 = {
        "id": "WR-G2", "threshold": 0.30,
        "arm0_wide_confab": arm0_wide, "arm1_wide_confab": arm1_wide,
        "net_lift": arm1_net_lift, "pass": bool(arm1_net_lift >= 0.30),
    }

    per_seed_wide: dict[str, Any] = {}
    per_seed_lift: dict[str, float] = {}
    per_seed_narrow_lift: dict[str, float] = {}
    arm0_narrow_rate = scored_summary["per_arm"]["arm0_baseline"]["narrow_confab"]["rate"]
    for seed in SEEDS:
        arm_id = f"arm2_random_{seed}"
        flags = _wide_rate_flags(applied_rows, all_tagged_rows, arm=arm_id, role="confab")
        wide_rate_summary = _wilson(flags)
        per_seed_wide[str(seed)] = wide_rate_summary
        per_seed_lift[str(seed)] = wide_rate_summary["rate"] - arm0_wide["rate"]
        per_seed_narrow_lift[str(seed)] = (
            scored_summary["per_arm"][arm_id]["narrow_confab"]["rate"] - arm0_narrow_rate
        )

    max_abs_random_lift = max(abs(v) for v in per_seed_lift.values()) if per_seed_lift else float("inf")
    effect_ratio = (arm1_net_lift / max_abs_random_lift) if max_abs_random_lift > 0 else float("inf")
    signs = ["+" if v > 0 else ("-" if v < 0 else "0") for v in per_seed_lift.values()]
    wr_g3 = {
        "id": "WR-G3", "threshold": 3.0,
        "adjudicable": bool(wr_g2["pass"]),
        "effect_ratio": effect_ratio if wr_g2["pass"] else None,
        "max_abs_random_lift": max_abs_random_lift,
        "pass": (bool(effect_ratio >= 3.0) if wr_g2["pass"] else None),
        "companion_descriptive": {
            "per_seed_wide": per_seed_wide,
            "per_seed_signed_wide_lift": per_seed_lift,
            "per_seed_signed_narrow_lift": per_seed_narrow_lift,
            "sign_counts": {"pos": signs.count("+"), "neg": signs.count("-"), "zero": signs.count("0")},
            "median_wide_lift": statistics.median(per_seed_lift.values()) if per_seed_lift else None,
        },
    }
    if not wr_g2["pass"]:
        wr_g3["note"] = "WR-G3 adjudicable_only_if WR-G2 PASS (gates.yaml); WR-G2 did not pass, so effect_ratio/pass are None. Companion descriptive table still reported."

    known_fired_flags = _wide_rate_flags(applied_rows, all_tagged_rows, arm="arm1_gated_replication",
                                          role="known_correct_answered", fired_only=True)
    floor = narrow.min_n_for_wilson_upper_below(0.15)
    fired_n = len(known_fired_flags)
    wr_g4: dict[str, Any] = {
        "id": "WR-G4", "adjudicability_floor": floor, "fired_n": fired_n,
        "unconditional_334row_wide_rate_companion": _wilson(
            _wide_rate_flags(applied_rows, all_tagged_rows, arm="arm1_gated_replication", role="known_correct_answered")
        ),
    }
    if fired_n < floor:
        wr_g4["disposition"] = "NOT-ADJUDICABLE"
        wr_g4["pass"] = None
    else:
        fired_summary = _wilson(known_fired_flags)
        point_ok = fired_summary["rate"] <= 0.05
        upper_ok = fired_summary["wilson_ci_95"][1] < 0.15
        wr_g4["fired_known_correct_wide_summary"] = fired_summary
        wr_g4["disposition"] = "PASS" if (point_ok and upper_ok) else "FAIL"
        wr_g4["pass"] = bool(point_ok and upper_ok)

    return {"WR-G1": wr_g1, "WR-G2": wr_g2, "WR-G3": wr_g3, "WR-G4": wr_g4}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grading-manifest", type=Path, required=True,
                     help='JSON {shard_id: {"graded_file": path, "attempt": 1|2}} -- authored by the '
                          "lead after every shard's graded-file hash is committed (commit-hash "
                          "subcommand, abstention-wide-instrument-calibration/apply_adjudication.py).")
    ap.add_argument("--scored-summary", type=Path, default=ANALYSIS_COMMITTED / "wide_rescore_scored_summary.json")
    ap.add_argument("--out", type=Path, default=ANALYSIS_COMMITTED / "wide_gates_report.json")
    args = ap.parse_args(argv)

    applied_report = apply_grading(args.grading_manifest)
    print(json.dumps(applied_report, indent=2))

    all_tagged_rows = bap_driver.load_all_scored_rows()
    applied_rows = swr.load_jsonl(ANALYSIS / "adjudication_applied.jsonl")
    scored_summary = json.loads(args.scored_summary.read_text(encoding="utf-8"))

    gates_report = compute_wr_gates(all_tagged_rows, applied_rows, scored_summary)
    gates_report["applied_summary"] = applied_report
    swr.write_json(args.out, gates_report)
    print(json.dumps(gates_report, indent=2))
    print(f"\n[gates_wide_rescore] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
