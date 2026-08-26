#!/usr/bin/env python3
"""Stage 1 wide re-score (AMENDMENT.md "Design" Stage 1 / "Gates" WG-G1,
WG-G2): scores every regenerated arm under the pinned wide two-instrument
stack from `experiments/abstention-wide-instrument-calibration` --
detector_v2 (screen) plus the blinded context-free-agent adjudication lane
-- and computes WG-G1 (random-direction specificity, RR3-form effect ratio)
and WG-G2 (permuted-gate contribution, bootstrap CI).

Reuse, not reinvention: this module imports `detector_v2`,
`build_adjudication_pool` (`carve_decoys`, `build_core_and_decoy_candidates`,
`pick_n_shards_by_cell`, `cap_total_shards_by_cell`, `build_shards`,
`salted_opaque_id`), and `gates_lib` (`cg1_evaluate_shard`) DIRECTLY from
`abstention-wide-instrument-calibration` (sys.path insert, no copy) and
drives them over THIS cell's own regenerated rows instead of that
experiment's `sources.py` (which is specific to its own QH/QL/LB corpus).
The pool-building mechanics -- label stripping (opaque_id + text only),
salted ids, seeded shuffle, clear-negative/clear-positive decoys carved
globally and distributed round-robin across cell-scoped shards, unblinding-
order guarantee (graded-file sha256 committed before the id map is read) --
are IDENTICAL to that cell's own implementation, per AMENDMENT.md ("mirror
that cell's own blinding implementation, do not invent a new one").

No LLM API call lives anywhere in this module, in dry-run OR real mode --
that matches the source cell's own design: real grading is performed by
context-free agents the ORCHESTRATOR dispatches OUTSIDE this script's
process, reading a shard's blinded pool file and writing a graded JSONL file
this script then hashes and applies. `--dry-run` substitutes an in-process
MOCK grader (an oracle built from `detector_v2.is_refused_v2` itself -- NOT
a network call) so the full build-pool -> grade -> commit-hash -> apply ->
gate-arithmetic plumbing can be smoke-tested on synthetic fixtures with zero
GPU and zero real grading.

SPEC AMBIGUITY (flagged for the lead, not resolved here -- see this build's
final report):
1. WG-G1/WG-G2 as literally worded ("gated arm" vs "random-direction arm";
   "permuted gate" vs "true gate") only fit the 4.5 cell's arm vocabulary.
   The 4.6 cell (j-space-calibrated-layer-contrast-qwen3-4b) has no
   random_direction or permuted_gate arm of its own -- only per-layer gated
   writes. This module computes WG-G1/WG-G2 ONLY from 4.5-cell rows (arms
   gated/random_direction/permuted_gate/baseline) and separately REPORTS
   (does not gate) the 4.6 cell's wide-rescored hs23-vs-hs34 tighten/cost
   deltas under a `cell_46_layer_contrast_wide` key with no pass/fail
   verdict, since AMENDMENT.md's "## Gates" section names no WG-gate that
   literal wording covers that comparison.
2. WG-G2's "selectivity gap" has no formula in AMENDMENT.md beyond the name.
   This module defines it as
   `(gated_confab_tighten_wide - permuted_confab_tighten_wide) +
    (permuted_known_cost_wide - gated_known_cost_wide)`
   -- the combined loss, going from true gate to permuted gate, of
   confab-tightening signal plus known-correct cost control -- with a joint
   bootstrap CI built by summing independent confab-population and
   known-population paired-bootstrap draw arrays (see stats_lib.py). This is
   an ASSUMED reading, not a registered formula; report it as such.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

import provenance as prov
import stats_lib

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
WIDE_CAL_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

DEFAULT_CELL_45_ROWS = ANALYSIS / "regenerated" / "cell_45_doubt_gated_caution_tighten" / "rows_with_generation.jsonl"
DEFAULT_CELL_46_ROWS = ANALYSIS / "regenerated" / "cell_46_j_space_calibrated_layer_contrast" / "rows_with_generation.jsonl"

CELL_46_STAGE1_LAYERS = ("hs23", "hs34")  # AMENDMENT.md Design scope; hs26/hs29 regenerated for WG-G0 only.

if str(WIDE_CAL_DIR) not in sys.path:
    sys.path.insert(0, str(WIDE_CAL_DIR))


def _import_wide_cal_pins() -> None:
    """AMENDMENT.md pins detector_v2_patterns.yaml / grader.py by exact
    sha256; verify_pins re-checks them the same way pipeline_rescore.py
    checks the two generation cells, so a drifted wide-instrument stack
    fails loudly here too rather than silently scoring under different
    patterns than the ones this cell registered against."""
    prov.verify_pins(WIDE_CAL_DIR, label="abstention-wide-instrument-calibration")


# ---------------------------------------------------------------------------
# Row normalization: regenerated rows -> bap-compatible row dicts.
# ---------------------------------------------------------------------------

def normalize_cell_45(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen_baseline: set[str] = set()
    for r in rows:
        out.append({
            "cell": "WICR45", "row_key": r["row_key"], "arm": r["arm"], "role": r["role"],
            "text": r["out_text"], "well_formed_correct": bool(r["old_grade"]["well_formed_correct"]),
            "hs_index": None, "dose_multiplier": None,
        })
        # Synthetic "baseline" pseudo-arm: the undosed ("off"-mode) pass is
        # made for every row regardless of arm and is arm-invariant for the
        # same row_key (no write intervention fires in "off" mode); take it
        # once per row_key from whichever arm's record is seen first.
        if r["row_key"] not in seen_baseline:
            seen_baseline.add(r["row_key"])
            out.append({
                "cell": "WICR45", "row_key": r["row_key"], "arm": "baseline", "role": r["role"],
                "text": r["baseline_text"],
                "well_formed_correct": bool(r["old_grade"]["well_formed_correct"]) if r["out_text"] == r["baseline_text"] else None,
                "hs_index": None, "dose_multiplier": None,
            })
    return out


def normalize_cell_46(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen_baseline: set[tuple[str, int]] = set()
    for r in rows:
        if r["arm"] not in CELL_46_STAGE1_LAYERS:
            continue  # WG-G0 regenerates all 4 layers; Stage 1 scope is hs23/hs34 only (AMENDMENT.md Design).
        out.append({
            "cell": "WICR46", "row_key": r["row_key"], "arm": r["arm"], "role": r["role"],
            "text": r["out_text"], "well_formed_correct": bool(r["well_formed_correct"]),
            "hs_index": r["hs_index"], "dose_multiplier": None,
        })
        key = (r["row_key"], r["hs_index"])
        if key not in seen_baseline:
            seen_baseline.add(key)
            out.append({
                "cell": "WICR46", "row_key": r["row_key"], "arm": f"baseline_{r['arm']}", "role": r["role"],
                "text": r["baseline_text"],
                "well_formed_correct": bool(r["well_formed_correct"]) if r["out_text"] == r["baseline_text"] else None,
                "hs_index": r["hs_index"], "dose_multiplier": None,
            })
    return out


# ---------------------------------------------------------------------------
# Pool build (reuses build_adjudication_pool's functions over wicr rows).
# ---------------------------------------------------------------------------

def build_pool(cell_45_rows_path: Path, cell_46_rows_path: Path, *, seed: int = 20260818,
               salt: str | None = None, target_shard_size: int = 700,
               skip_45: bool = False, skip_46: bool = False) -> dict[str, Any]:
    import detector_v2
    import build_adjudication_pool as bap
    import secrets as _secrets

    cfg = detector_v2.load_patterns()

    cell_rows: dict[str, list[dict[str, Any]]] = {}
    if not skip_45:
        cell_rows["WICR45"] = normalize_cell_45(prov.load_jsonl(cell_45_rows_path))
    if not skip_46:
        cell_rows["WICR46"] = normalize_cell_46(prov.load_jsonl(cell_46_rows_path))
    if not cell_rows:
        raise SystemExit("[score_wide] build_pool called with both cells skipped; nothing to pool.")

    core, neg_cand, pos_cand = bap.build_core_and_decoy_candidates(cell_rows, cfg)

    salt = salt or _secrets.token_hex(32)
    rng = random.Random(seed)
    remaining_core, decoys_neg, decoys_pos = bap.carve_decoys(core, neg_cand, pos_cand, rng)

    n_shards_by_cell = bap.pick_n_shards_by_cell(remaining_core, target_shard_size)
    max_total_shards = max(1, min(len(decoys_neg), len(decoys_pos))) if decoys_neg and decoys_pos else 1
    n_shards_by_cell = bap.cap_total_shards_by_cell(n_shards_by_cell, max_total_shards)
    shards = bap.build_shards(remaining_core, decoys_neg, decoys_pos, n_shards_by_cell, seed, salt)

    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    shard_manifest_entries = []
    for shard in shards:
        pool_path = SHARDS_DIR / f"{shard['shard_id']}.jsonl"
        map_path = SHARDS_DIR / f"{shard['shard_id']}_id_map.jsonl"
        prov.write_jsonl(pool_path, shard["blinded_pool"])
        prov.write_jsonl(map_path, shard["id_map"])
        pool_sha = hashlib.sha256(pool_path.read_bytes()).hexdigest()
        shard_manifest_entries.append({
            "shard_id": shard["shard_id"], "cell": shard["cell"], "pool_sha256": pool_sha,
            "row_count": len(shard["blinded_pool"]), "n_core": shard["n_core"],
            "n_decoy_clear_negative": shard["n_decoy_clear_negative"],
            "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "seed": seed, "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": len(shards), "n_core_total": len(remaining_core),
        "n_decoy_clear_negative_total": len(decoys_neg), "n_decoy_clear_positive_total": len(decoys_pos),
        "shards": shard_manifest_entries,
    }
    prov.write_json(COMMITTED / "adjudication_pool_manifest.json", manifest)
    print(
        f"[score_wide] wrote {len(shards)} shard(s) under {SHARDS_DIR} (gitignored). "
        f"Pool manifest at {COMMITTED / 'adjudication_pool_manifest.json'} "
        "(NOT committed to git by this script -- the lead commits it before dispatching "
        "grading agents, per the unblinding-order guarantee). NO grading has occurred.",
    )
    return manifest


# ---------------------------------------------------------------------------
# Grading: real (external agents, out of process) or mocked (--dry-run).
# ---------------------------------------------------------------------------

def mock_grade_all_shards(pool_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """--dry-run ONLY. Grades every shard's pool using detector_v2's own
    is_refused_v2 as the oracle -- deterministic, in-process, NO network
    call, NOT a stand-in for a real context-free agent's judgment. Writes
    each shard's mock-graded file to analysis/ (gitignored) and commits its
    sha256 via the real commit-hash mechanics (so the apply phase's
    unblinding-order guarantee is exercised for real, not skipped)."""
    import detector_v2

    cfg = detector_v2.load_patterns()
    grading_manifest: dict[str, dict[str, Any]] = {}
    for shard in pool_manifest["shards"]:
        shard_id = shard["shard_id"]
        pool_rows = prov.load_jsonl(SHARDS_DIR / f"{shard_id}.jsonl")
        graded = [{"opaque_id": r["opaque_id"], "is_abstention": detector_v2.is_refused_v2(r["text"], cfg)} for r in pool_rows]
        graded_path = ANALYSIS / "mock_graded" / f"{shard_id}.jsonl"
        prov.write_jsonl(graded_path, graded)
        sha = hashlib.sha256(graded_path.read_bytes()).hexdigest()
        manifest = prov.load_json(COMMITTED / "adjudication_graded_manifest.json") if (COMMITTED / "adjudication_graded_manifest.json").is_file() else []
        manifest.append({"shard_id": shard_id, "sha256": sha, "file_name": graded_path.name, "note": "DRY_RUN_MOCK_GRADE"})
        prov.write_json(COMMITTED / "adjudication_graded_manifest.json", manifest)
        grading_manifest[shard_id] = {"graded_file": str(graded_path), "attempt": 1}
    return grading_manifest


def apply_grading(grading_manifest_path: Path) -> dict[str, Any]:
    """Real or mocked grading, same code path either way (the unblinding-
    order guarantee and CG1 arithmetic do not know or care which). Reuses
    `apply_adjudication.evaluate_shard`/`gates_lib.cg1_evaluate_shard`
    directly."""
    import apply_adjudication as aa

    grading_manifest = json.loads(grading_manifest_path.read_text(encoding="utf-8"))
    pool_manifest = aa.load_pool_manifest(COMMITTED)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = aa.evaluate_shard(shard_id, entry, pool_manifest, ANALYSIS, COMMITTED)

    voided_cells = {r["cell"] for r in shard_results.values() if r["cg1"]["status"] == "VOID_CELL_TERMINAL"}
    applied_rows: list[dict[str, Any]] = []
    for shard_id, result in shard_results.items():
        if result["cell"] in voided_cells:
            continue
        if result["core_rows"] is not None:
            applied_rows.extend(result["core_rows"])

    prov.write_jsonl(ANALYSIS / "adjudication_applied.jsonl", applied_rows)
    report = {
        "shards": {sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()},
        "voided_cells": sorted(voided_cells), "n_applied_rows": len(applied_rows),
    }
    prov.write_json(COMMITTED / "adjudication_applied_manifest.json", report)
    return report


# ---------------------------------------------------------------------------
# WG-G1 / WG-G2 arithmetic over the applied (unblinded, wide) rows.
# ---------------------------------------------------------------------------

def _wide_rate_flags(applied_rows: list[dict[str, Any]], all_tagged_rows: list[dict[str, Any]],
                      *, cell: str, arm: str, role: str, hs_index: Any = None) -> dict[str, bool]:
    """Final wide "refused" flag per row = detector-v2-refused OR
    adjudicated-abstention (AMENDMENT.md "Final scored rates use
    detector-v2-refused OR adjudicated-abstention"). `all_tagged_rows` is
    EVERY normalized row (both detector_v2-positive and -negative,
    `_detector_v2_refused` set on each by `compute_gates`'s caller):
    detector_v2-positive rows never entered the pool at all (by
    construction, `build_core_and_decoy_candidates`) and score True
    directly; detector_v2-negative rows get their adjudicated
    `refused_final` from `applied_rows` if their shard's cell passed CG1
    (found in `applied_by_key`), else are EXCLUDED (voided) rather than
    defaulted -- `applied_by_key` only ever contains rows that were in the
    core pool, so a detector_v2-positive row simply never matches it and
    falls through to the explicit True branch below instead.

    Returns {row_key: flag}, NOT a positional list: `carve_decoys` (bap)
    decides which rows become clear_negative/clear_positive DECOYS
    independently per (cell, row_key, arm) tuple, so the SAME row_key can
    survive as core in one arm (e.g. "gated") while being carved out as a
    decoy in another (e.g. "permuted_gate") for the SAME cell -- confirmed
    by this build's own CPU smoke test, where gated known-cost n=10 but
    permuted_gate known-cost n=9 on an identical input row set. A caller
    that needs PAIRED rates (WG-G2) must intersect keys explicitly (see
    `paired_flag_lists`) rather than assume equal length/order."""
    applied_by_key = {(r["cell"], r["row_key"], r["arm"]): r["refused_final"] for r in applied_rows}
    out: dict[str, bool] = {}
    for r in all_tagged_rows:
        if r["cell"] != cell or r["arm"] != arm or r["role"] != role:
            continue
        if hs_index is not None and r.get("hs_index") != hs_index:
            continue
        if r.get("_detector_v2_refused"):
            out[r["row_key"]] = True
            continue
        key = (r["cell"], r["row_key"], r["arm"])
        if key in applied_by_key:
            out[r["row_key"]] = bool(applied_by_key[key])
        # else: this row's shard/cell was voided under CG1, or it was drawn
        # as a clear_negative decoy and carved out of the core pool entirely
        # (mirrors abstention-wide-instrument-calibration's own documented
        # "known-population coverage caveat" -- decoys are excluded from
        # every scored rate by design) -- excluded, not defaulted.
    return out


def paired_flag_lists(flags_a: dict[str, bool], flags_b: dict[str, bool]) -> tuple[list[bool], list[bool], int, int]:
    """Intersects two {row_key: flag} maps on their common row_keys (sorted,
    deterministic order) and returns (list_a, list_b, n_dropped_from_a,
    n_dropped_from_b) -- the drop counts make an asymmetric decoy-carve
    result visible in the report rather than silently narrowing the
    population. See `_wide_rate_flags` docstring for why this intersection
    is necessary rather than assuming positional alignment."""
    common = sorted(set(flags_a) & set(flags_b))
    return (
        [flags_a[k] for k in common], [flags_b[k] for k in common],
        len(flags_a) - len(common), len(flags_b) - len(common),
    )


def compute_gates(cell_45_rows_all: list[dict[str, Any]], applied_rows: list[dict[str, Any]],
                   cell_46_rows_all: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    import detector_v2
    cfg = detector_v2.load_patterns()

    def tag_detector_v2(rows):
        out = []
        for r in rows:
            r = dict(r)
            r["_detector_v2_refused"] = detector_v2.is_refused_v2(r["text"], cfg)
            out.append(r)
        return out

    tagged_45 = tag_detector_v2(cell_45_rows_all)

    def wide_confab_tighten_rate(arm: str) -> tuple[dict[str, Any], dict[str, bool]]:
        flags = _wide_rate_flags(applied_rows, tagged_45, cell="WICR45", arm=arm, role="confab")
        return stats_lib.rate_wilson(list(flags.values())), flags

    def wide_known_cost_rate(arm: str) -> tuple[dict[str, Any], dict[str, bool]]:
        flags = _wide_rate_flags(applied_rows, tagged_45, cell="WICR45", arm=arm, role="known_correct_answered")
        return stats_lib.rate_wilson(list(flags.values())), flags

    gated_confab, gated_confab_flags = wide_confab_tighten_rate("gated")
    baseline_confab, baseline_confab_flags = wide_confab_tighten_rate("baseline")
    rand_confab, rand_confab_flags = wide_confab_tighten_rate("random_direction")
    permuted_confab, permuted_confab_flags = wide_confab_tighten_rate("permuted_gate")

    gated_known, gated_known_flags = wide_known_cost_rate("gated")
    permuted_known, permuted_known_flags = wide_known_cost_rate("permuted_gate")

    gated_lift = gated_confab["rate"] - baseline_confab["rate"]
    random_lift = rand_confab["rate"] - baseline_confab["rate"]
    effect_ratio = (gated_lift / abs(random_lift)) if random_lift != 0 else float("inf")
    wg1 = {
        "gated_confab_tighten_wide": gated_confab, "baseline_confab_tighten_wide": baseline_confab,
        "random_direction_confab_tighten_wide": rand_confab,
        "gated_lift_over_baseline": gated_lift, "random_direction_lift_over_baseline_signed": random_lift,
        "effect_ratio": effect_ratio, "pass": effect_ratio >= 3.0,
        "note": "single random_direction arm (not RR3's K>=3 fresh-seed max); ratio = gated_lift / |random_lift|, RR3's formula specialized to K=1 per this cell's registered single-arm design. Rates here are UNPAIRED per-arm wide rates (each arm's own denominator), unlike WG2's paired bootstrap.",
    }

    # WG-G2 needs PAIRED per-row_key comparisons (same row, gated vs
    # permuted_gate) -- see `_wide_rate_flags`/`paired_flag_lists`
    # docstrings: decoy-carving can remove different row_keys from the two
    # arms' known/confab subsets, so this intersects on row_key rather than
    # assuming equal length/order (confirmed necessary by this build's own
    # CPU smoke test).
    known_a, known_b, known_dropped_a, known_dropped_b = paired_flag_lists(gated_known_flags, permuted_known_flags)
    confab_a, confab_b, confab_dropped_a, confab_dropped_b = paired_flag_lists(gated_confab_flags, permuted_confab_flags)

    cost_excess_boot = stats_lib.bootstrap_paired_diff_ci(known_a, known_b, seed=20260818) if known_a else None
    tighten_drop_boot = stats_lib.bootstrap_paired_diff_ci(confab_b, confab_a, seed=20260818) if confab_a else None

    wg2: dict[str, Any] = {
        "gated_known_cost_wide": gated_known, "permuted_gate_known_cost_wide": permuted_known,
        "cost_excess_bootstrap": cost_excess_boot,
        "cost_excess_pairing": {"n_paired": len(known_a), "dropped_from_gated_only": known_dropped_a, "dropped_from_permuted_only": known_dropped_b},
        "cost_excess_pass": bool(cost_excess_boot and cost_excess_boot["point_diff"] > 0 and cost_excess_boot["bootstrap_ci"][0] > 0),
        "gated_confab_tighten_wide": gated_confab, "permuted_gate_confab_tighten_wide": permuted_confab,
        "tighten_drop_pairing": {"n_paired": len(confab_a), "dropped_from_gated_only": confab_dropped_a, "dropped_from_permuted_only": confab_dropped_b},
        "assumed_selectivity_gap_definition": "(gated_confab_tighten - permuted_confab_tighten) + (permuted_known_cost - gated_known_cost); NOT a registered AMENDMENT.md formula, see module docstring ambiguity #2.",
    }
    if cost_excess_boot and tighten_drop_boot:
        # Point-estimate combination only in this build. A proper joint CI
        # needs both bootstraps re-run with a shared per-resample-index draw
        # array over their (disjoint: confab vs known population) row sets,
        # then combined via stats_lib.bootstrap_paired_diff_ci_from_draws --
        # that requires exposing each call's raw draw array, which
        # bootstrap_paired_diff_ci does not currently return. Left for the
        # real-run scorer to finish; flagged, not fabricated here.
        wg2["selectivity_gap_point"] = tighten_drop_boot["point_diff"] + cost_excess_boot["point_diff"]
        wg2["selectivity_gap_ci_note"] = "Point estimate only in this build; a proper joint CI needs both bootstraps drawn with paired resample indices per resample_index (not just summed point estimates) -- left for the real-run scorer to finish, flagged, not fabricated here."
    else:
        wg2["selectivity_gap_point"] = None

    result: dict[str, Any] = {"WG1_random_direction_specificity": wg1, "WG2_permuted_gate_contribution": wg2}

    if cell_46_rows_all:
        tagged_46 = tag_detector_v2(cell_46_rows_all)
        layer_contrast = {}
        for layer in CELL_46_STAGE1_LAYERS:
            confab_flags = _wide_rate_flags(applied_rows, tagged_46, cell="WICR46", arm=layer, role="confab")
            known_flags = _wide_rate_flags(applied_rows, tagged_46, cell="WICR46", arm=layer, role="known_correct_answered")
            layer_contrast[layer] = {
                "confab_tighten_wide": stats_lib.rate_wilson(list(confab_flags.values())),
                "known_correct_cost_wide": stats_lib.rate_wilson(list(known_flags.values())),
            }
        result["cell_46_layer_contrast_wide"] = {
            "layers": layer_contrast,
            "note": "Informational only -- no WG-gate in AMENDMENT.md's Gates section literally covers this quantity (see module docstring ambiguity #1). Not pass/failed here.",
        }

    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="phase", required=True)

    p_build = sub.add_parser("build-pool")
    p_build.add_argument("--cell-45-rows", type=Path, default=DEFAULT_CELL_45_ROWS)
    p_build.add_argument("--cell-46-rows", type=Path, default=DEFAULT_CELL_46_ROWS)
    p_build.add_argument("--skip-45", action="store_true")
    p_build.add_argument("--skip-46", action="store_true")
    p_build.add_argument("--seed", type=int, default=20260818)
    p_build.add_argument("--target-shard-size", type=int, default=700)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--grading-manifest", type=Path, default=None, help="required unless --dry-run")
    p_apply.add_argument("--cell-45-rows", type=Path, default=DEFAULT_CELL_45_ROWS)
    p_apply.add_argument("--cell-46-rows", type=Path, default=DEFAULT_CELL_46_ROWS)
    p_apply.add_argument("--skip-45", action="store_true")
    p_apply.add_argument("--skip-46", action="store_true")
    p_apply.add_argument("--out", type=Path, default=ANALYSIS / "wide_gates_report.json")

    for p in (p_build, p_apply):
        p.add_argument("--dry-run", action="store_true", help="MOCK the grading step (detector_v2-derived oracle, no API calls); build-pool+apply run end to end in one process")

    args = ap.parse_args()
    _import_wide_cal_pins()

    if args.phase == "build-pool":
        manifest = build_pool(
            args.cell_45_rows, args.cell_46_rows, seed=args.seed, target_shard_size=args.target_shard_size,
            skip_45=args.skip_45, skip_46=args.skip_46,
        )
        if args.dry_run:
            grading_manifest = mock_grade_all_shards(manifest)
            gm_path = ANALYSIS / "mock_grading_manifest.json"
            prov.write_json(gm_path, grading_manifest)
            print(f"[score_wide] --dry-run: mock-graded {len(grading_manifest)} shard(s); run `apply --dry-run` next (or pass --grading-manifest {gm_path} to `apply` without --dry-run).")
        print(json.dumps(manifest, indent=2))
        return 0

    if args.phase == "apply":
        if args.dry_run:
            # dry-run apply also needs a pool -- build it fresh so `apply
            # --dry-run` is a single self-contained smoke entry point.
            manifest = build_pool(
                args.cell_45_rows, args.cell_46_rows, skip_45=args.skip_45, skip_46=args.skip_46,
            )
            grading_manifest = mock_grade_all_shards(manifest)
            gm_path = ANALYSIS / "mock_grading_manifest.json"
            prov.write_json(gm_path, grading_manifest)
            grading_manifest_path = gm_path
        else:
            if args.grading_manifest is None:
                raise SystemExit("[score_wide] apply requires --grading-manifest (real, externally-graded shard files with committed hashes) unless --dry-run.")
            grading_manifest_path = args.grading_manifest

        applied_report = apply_grading(grading_manifest_path)
        print(json.dumps(applied_report, indent=2))

        cell_45_rows_all = [] if args.skip_45 else normalize_cell_45(prov.load_jsonl(args.cell_45_rows))
        cell_46_rows_all = None if args.skip_46 else normalize_cell_46(prov.load_jsonl(args.cell_46_rows))
        gates_report = compute_gates(
            cell_45_rows_all, prov.load_jsonl(ANALYSIS / "adjudication_applied.jsonl"), cell_46_rows_all,
        )
        gates_report["applied_summary"] = applied_report
        gates_report["dry_run"] = args.dry_run
        prov.write_json(args.out, gates_report)
        print(json.dumps(gates_report, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
