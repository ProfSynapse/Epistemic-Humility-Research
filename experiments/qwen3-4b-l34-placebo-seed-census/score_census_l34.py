#!/usr/bin/env python3
"""Wide-instrument scoring driver for qwen3-4b-l34-placebo-seed-census
(AMENDMENT.md "Rows and instrument" / gates.yaml QG-G1/QG-G2).

Reuse, not reinvention -- but this cell's shape (15 arms sharing ONE literal
arm string "random_direction", distinguished only by `seed`) does not fit
`abstention-wide-instrument-calibration/build_adjudication_pool.py`'s
opaque-id/id-map schema, which folds in (cell, row_key, arm, hs_index,
dose_multiplier) but has NO `seed` slot -- confirmed by reading that module
in full: 15 seed-rows sharing (cell, row_key, arm) would collide to the
SAME opaque_id and the SAME (cell, row_key, arm) key `score_wide.py`'s own
`_wide_rate_flags` uses to rejoin adjudicated rows, silently collapsing all
15 seeds into one undifferentiated rate. `placebo-seed-distribution-census`
was built for exactly this per-seed-arm shape (its own
`build_pool.py`/`apply_adjudication.py` fold `seed` into the opaque-id
payload and the id_map/core_rows schema throughout), so THIS driver uses
`placebo-seed-distribution-census`'s own `build_pool.py` (seed-aware
sharding/candidate/opaque-id mechanics) together with its own
`apply_adjudication.py` (per AMENDMENT.md's explicit "via the census
apply_adjudication.py tooling"), not `abstention-wide-instrument-calibration`'s
copies. The WIDENED DETECTOR itself (`detector_v2.py` /
`detector_v2_patterns.yaml`) is imported from
`abstention-wide-instrument-calibration` specifically -- the sha-pinned
instrument wide-instrument-control-rescore itself scored its arms under
(verified byte-identical to census's own copy by direct diff before this
build; imported from abstention's copy anyway for an unambiguous
provenance chain, not census's).

Every cross-directory module load in this file goes through
`_import_from_dir` (ported verbatim from wide-instrument-control-rescore/
pipeline_rescore.py's own helper of the same name -- a generic importlib
loader, not experiment logic) with a DISTINCT `module_name` per load, so two
same-named files in different experiment directories
(`abstention-wide-instrument-calibration/gates_lib.py` and
`placebo-seed-distribution-census/gates_lib.py` differ in content; both
directories also carry their own `detector_v2.py`/`apply_adjudication.py`)
can never shadow or silently replace each other in `sys.modules` -- each
load gets its own module object, and that file's own internal bare imports
(e.g. `apply_adjudication.py`'s `import gates_lib`) still resolve correctly
because `_import_from_dir` scopes its directory onto the FRONT of sys.path
for the duration of that file's own module-body execution.

DECOY SOURCE (build-time engineering necessity, flagged for the lead's
sanity-check -- AMENDMENT.md/cell.yaml/gates.yaml are SILENT on where this
cell's own blinding-audit decoys come from, and no source exists on disk
without an additional unregistered GPU pass): this cell's registered
population is confab-only (AMENDMENT.md "No cost gate: the random arms run
on confab rows only"), so it has no known_correct_answered rows of its own
to source clear_negative decoys from. wide-instrument-control-rescore's OWN
real GPU run already regenerated exactly that decoy-eligible population
(dgct's gated/random_direction/permuted_gate arms x confab AND
known_correct_answered roles, dose 200.0, byte-identical instrument) and
left it on disk (gitignored, ephemeral,
wide-instrument-control-rescore/analysis/regenerated/
cell_45_doubt_gated_caution_tighten/rows_with_generation.jsonl in the
canonical checkout). This driver copies that file read-only (never modifies
wicr) into a WICR45DECOY decoy-source pseudo-cell, normalized via wicr's OWN
`score_wide.normalize_cell_45` (imported, not reimplemented), tags
`refused_v2` on it explicitly (census's own `build_pool.py` expects that
field PRE-COMPUTED per row, unlike abstention's equivalent which computes it
internally), and:
  - derives clear_negative candidates directly (role=="known_correct_answered"
    and well_formed_correct and refused_v2==False -- the SAME one-line
    predicate abstention's build_core_and_decoy_candidates uses inline,
    reproduced here since census's own build_pool.py sources clear_negative
    from an unrelated held-back-pool concept this cell does not have);
  - feeds WICR45DECOY rows alongside this cell's own L34CENSUS rows into
    census's `build_core_and_positive_candidates` for clear_positive
    candidates (both use the literal arm string "random_direction", so
    wicr's historical seed-20260707 draw AND this cell's own 15 fresh seeds
    both qualify), then FILTERS THE RETURNED core down to cell=="L34CENSUS"
    before sharding -- no wicr row ever re-enters this cell's scored
    population.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
WICR_DIR = REPO_ROOT / "experiments" / "wide-instrument-control-rescore"
WIDE_CAL_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
CENSUS_DIR = REPO_ROOT / "experiments" / "placebo-seed-distribution-census"

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"
ROWS_DIR = ANALYSIS / "rows"
WICR_DECOY_SOURCE_PATH = ANALYSIS / "wicr_decoy_source" / "rows_with_generation.jsonl"

SEEDS = [920001, 920002, 920003, 920004, 920005, 920006, 920007, 920008, 920009,
         920010, 920011, 920012, 920013, 920014, 920015]

if str(WICR_DIR) not in sys.path:
    sys.path.insert(0, str(WICR_DIR))
import provenance as prov  # noqa: E402  (wicr; unique filename, no collision risk)


def _bare_top_level_import_names(source_path: Path) -> set[str]:
    """AST-scans `source_path` for its own MODULE-BODY-level bare `import X`
    statements (not `from X import Y`, not imports nested inside a
    function/class, not stdlib-safe since this is only consulted for
    same-named-file collision handling below). Used by `_import_from_dir`
    to know which names in sys.modules might be a STALE same-named module
    from a DIFFERENT experiment directory, loaded earlier in this same
    process -- this repo's stated convention that each experiment directory
    owns its own copy of same-named files (detector_v2.py, gates_lib.py,
    common.py, grader.py, ...) means combining two such directories' loads
    in one interpreter (as this cell's --smoke orchestrator does, running
    generation-loading and scoring-loading together) is a REAL collision
    risk, not a hypothetical one -- confirmed by a direct smoke-test
    failure: doubt-gated-caution-tighten/pipeline.py's own bare `import
    grader` (dgct's grader.py) got cached first, then
    abstention-wide-instrument-calibration/detector_v2.py's own bare
    `import grader` (a DIFFERENT grader.py) silently reused the stale
    cached module instead of loading its own."""
    import ast
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in tree.body:  # module body only, not nested in def/class
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _import_from_dir(module_name: str, module_dir: Path, file_name: str):
    """Ported from wide-instrument-control-rescore/pipeline_rescore.py's own
    `_import_from_dir` -- a generic importlib loader, not experiment logic.
    Prepends `module_dir` onto sys.path for the duration of this one file's
    own module-body execution (so its internal bare imports resolve against
    its own directory), then removes it; the loaded module is bound under
    `module_name` in sys.modules, a name distinct per call site in this file
    so no two loads can shadow each other regardless of what the two source
    files are themselves named on disk.

    EXTENDED beyond the ported original (needed the first time this file's
    own loads are combined with pipeline_census_l34.py's dgct load in one
    process, by run_census_l34.py --smoke): before exec, any of this file's
    own TOP-LEVEL bare `import X` names that are already in sys.modules
    pointing at a file OUTSIDE `module_dir` are evicted so X re-resolves
    fresh against `module_dir` (now on sys.path); the prior entry (if any)
    is restored afterward so this does not permanently corrupt the process
    module cache for whatever cached it originally. See
    `_bare_top_level_import_names` docstring for why this is a real, not
    hypothetical, collision class in this repo."""
    added = str(module_dir) not in sys.path
    if added:
        sys.path.insert(0, str(module_dir))

    bare_names = _bare_top_level_import_names(module_dir / file_name)
    saved_modules: dict[str, Any] = {}
    experiments_root = str((REPO_ROOT / "experiments").resolve())
    module_dir_resolved = str(module_dir.resolve())
    for name in bare_names:
        cached = sys.modules.get(name)
        cached_file = getattr(cached, "__file__", None)
        # Only evict a module that is ITSELF one of this repo's
        # experiment-directory files (cached_file resolves under
        # experiments/) and lives OUTSIDE module_dir -- the actual
        # collision domain (this repo's stated convention that each
        # experiment directory owns its own copy of same-named files).
        # Never touch stdlib/site-packages modules (e.g. `re`, `yaml`) or
        # built-ins with no __file__ (e.g. `sys` itself) -- evicting those
        # either does nothing useful or corrupts the interpreter's own
        # module cache.
        if (
            cached is not None and cached_file is not None
            and str(Path(cached_file).resolve()).startswith(experiments_root)
            and not str(Path(cached_file).resolve()).startswith(module_dir_resolved)
        ):
            saved_modules[name] = sys.modules.pop(name)

    try:
        spec = importlib.util.spec_from_file_location(module_name, module_dir / file_name)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Only restore names actually evicted above. A bare-imported name
        # that was NOT evicted (untouched builtin/stdlib, or already
        # pointed inside module_dir) must be left exactly as exec_module
        # left it -- popping it here would, e.g., corrupt `sys` itself
        # (no __file__, so never evicted, but still a bare-imported name).
        # A name freshly cached during this exec (not evicted, nothing to
        # restore) is left in sys.modules; if some LATER _import_from_dir
        # call for a different module_dir needs that same bare name, this
        # function's own eviction check triggers again at that call.
        for name, cached in saved_modules.items():
            sys.modules[name] = cached
        if added:
            sys.path.remove(str(module_dir))


_MODULE_CACHE: dict[str, Any] = {}


def _cached_import(cache_key: str, module_dir: Path, file_name: str):
    if cache_key not in _MODULE_CACHE:
        _MODULE_CACHE[cache_key] = _import_from_dir(cache_key, module_dir, file_name)
    return _MODULE_CACHE[cache_key]


def _detector_v2():
    """abstention-wide-instrument-calibration's own detector_v2.py -- the
    sha-pinned widened-detector instrument wide-instrument-control-rescore
    itself scored its arms under."""
    return _cached_import("l34_census_detector_v2", WIDE_CAL_DIR, "detector_v2.py")


def _census_build_pool():
    return _cached_import("l34_census_build_pool", CENSUS_DIR, "build_pool.py")


def _census_apply_adjudication():
    return _cached_import("l34_census_apply_adjudication", CENSUS_DIR, "apply_adjudication.py")


def _wicr_score_wide():
    return _cached_import("l34_census_wicr_score_wide", WICR_DIR, "score_wide.py")


def _import_wide_cal_pins() -> None:
    """AMENDMENT.md pins detector_v2_patterns.yaml/grader.py by sha256
    (via abstention-wide-instrument-calibration's own experiment.yaml
    instrument.pins); verified the same way wicr's own score_wide.py
    verifies them, so a drifted widened-detector fails loudly here too."""
    prov.verify_pins(WIDE_CAL_DIR, label="abstention-wide-instrument-calibration")


# ---------------------------------------------------------------------------
# Row normalization
# ---------------------------------------------------------------------------

def normalize_census_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """This cell's own generated rows -> pool/gate-compatible row dicts.
    `seed` is carried through explicitly (census's own schema convention;
    see module docstring)."""
    out = []
    for r in rows:
        out.append({
            "cell": "L34CENSUS", "row_key": r["row_key"], "arm": "random_direction",
            "role": "confab", "seed": r["seed"], "source": None, "text": r["out_text"],
            "well_formed_correct": bool(r["old_grade"]["well_formed_correct"]),
        })
    return out


def load_census_rows(rows_dir: Path = ROWS_DIR, seeds: list[int] = SEEDS) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    missing = []
    for seed in seeds:
        p = rows_dir / f"seed_{seed}.jsonl"
        if not p.is_file():
            missing.append(str(p))
            continue
        out.extend(prov.load_jsonl(p))
    if missing:
        raise SystemExit(f"[score_census_l34] missing per-seed row files: {missing}")
    return normalize_census_rows(out)


def load_wicr_decoy_source(path: Path = WICR_DECOY_SOURCE_PATH) -> list[dict[str, Any]]:
    """wicr's OWN normalize_cell_45, imported unmodified, applied to a
    read-only copy of wicr's own regenerated rows -- used ONLY as a decoy
    candidate source (see module docstring), never entering this cell's
    scored population. `seed` is absent from this schema (score_wide.py's
    normalize_cell_45 has no seed concept); left unset (None) throughout,
    which census's own `.get("seed")`-defensive functions handle safely."""
    if not path.is_file():
        raise SystemExit(
            f"[score_census_l34] wicr decoy-source rows not found at {path}. "
            "Copy wide-instrument-control-rescore/analysis/regenerated/"
            "cell_45_doubt_gated_caution_tighten/rows_with_generation.jsonl "
            "(canonical checkout) into this path before real scoring."
        )
    wicr_score_wide = _wicr_score_wide()
    raw = prov.load_jsonl(path)
    normalized = wicr_score_wide.normalize_cell_45(raw)
    for r in normalized:
        r["cell"] = "WICR45DECOY"  # re-tag so it can never be mistaken for scored L34CENSUS core
        r.setdefault("seed", None)
    return normalized


# ---------------------------------------------------------------------------
# Pool build (census's own seed-aware build_pool.py mechanics; core filtered
# to L34CENSUS).
# ---------------------------------------------------------------------------

def build_pool(*, seed: int = 20260825, salt: str | None = None, target_shard_size: int = 700,
               rows_dir: Path = ROWS_DIR, decoy_source_path: Path = WICR_DECOY_SOURCE_PATH,
               analysis_dir: Path = ANALYSIS, committed_dir: Path = COMMITTED) -> dict[str, Any]:
    import secrets as _secrets

    detector_v2_mod = _detector_v2()
    census_bp = _census_build_pool()
    cfg = detector_v2_mod.load_patterns()

    def _tag_refused_v2(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for r in rows:
            r = dict(r)
            r["refused_v2"] = detector_v2_mod.is_refused_v2(r["text"], cfg)
            out.append(r)
        return out

    census_rows = _tag_refused_v2(load_census_rows(rows_dir))
    decoy_source_rows = _tag_refused_v2(load_wicr_decoy_source(decoy_source_path))

    core_all, positive_all = census_bp.build_core_and_positive_candidates(
        {"L34CENSUS": census_rows, "WICR45DECOY": decoy_source_rows},
    )
    core = [r for r in core_all if r["cell"] == "L34CENSUS"]
    neg_cand = [
        r for r in core_all
        if r["cell"] == "WICR45DECOY" and r["role"] == "known_correct_answered" and r["well_formed_correct"]
    ]

    salt = salt or _secrets.token_hex(32)
    rng = random.Random(seed)
    decoys_neg, decoys_pos = census_bp.carve_decoys(core, neg_cand, positive_all, rng)

    n_shards_by_cell = census_bp.pick_n_shards_by_cell(core, target_shard_size)
    n_shards_by_cell = census_bp.cap_total_shards_by_cell(n_shards_by_cell, len(decoys_neg), len(decoys_pos))
    shards = census_bp.build_shards(core, decoys_neg, decoys_pos, n_shards_by_cell, seed, salt)

    shards_dir = analysis_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    shard_manifest_entries = []
    for shard in shards:
        pool_path = shards_dir / f"{shard['shard_id']}.jsonl"
        map_path = shards_dir / f"{shard['shard_id']}_id_map.jsonl"
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
        "n_shards": len(shards), "n_core_total": len(core),
        "n_decoy_clear_negative_total": len(decoys_neg), "n_decoy_clear_positive_total": len(decoys_pos),
        "shards": shard_manifest_entries,
    }
    prov.write_json(committed_dir / "pool_manifest.json", manifest)
    print(
        f"[score_census_l34] wrote {len(shards)} shard(s) under {shards_dir} (gitignored). "
        f"Pool manifest at {committed_dir / 'pool_manifest.json'} (NOT committed by this script). "
        "NO grading has occurred.",
    )
    return manifest


# ---------------------------------------------------------------------------
# Grading: real (external agents) or mocked (--dry-run).
# ---------------------------------------------------------------------------

def mock_grade_all_shards(pool_manifest: dict[str, Any], *, analysis_dir: Path = ANALYSIS,
                           committed_dir: Path = COMMITTED) -> dict[str, dict[str, Any]]:
    """--dry-run ONLY. detector_v2.is_refused_v2 as an in-process oracle, no
    network call, NOT a stand-in for a real grader (same mechanism as
    wide-instrument-control-rescore/score_wide.py's own mock_grade_all_shards)."""
    detector_v2_mod = _detector_v2()
    cfg = detector_v2_mod.load_patterns()
    shards_dir = analysis_dir / "shards"
    grading_manifest: dict[str, dict[str, Any]] = {}
    for shard in pool_manifest["shards"]:
        shard_id = shard["shard_id"]
        pool_rows = prov.load_jsonl(shards_dir / f"{shard_id}.jsonl")
        graded = [{"opaque_id": r["opaque_id"], "is_abstention": detector_v2_mod.is_refused_v2(r["text"], cfg)} for r in pool_rows]
        graded_path = analysis_dir / "mock_graded" / f"{shard_id}.jsonl"
        prov.write_jsonl(graded_path, graded)
        sha = hashlib.sha256(graded_path.read_bytes()).hexdigest()
        manifest_path = committed_dir / "adjudication_graded_manifest.json"
        manifest = prov.load_json(manifest_path) if manifest_path.is_file() else []
        manifest.append({"shard_id": shard_id, "sha256": sha, "file_name": graded_path.name, "note": "DRY_RUN_MOCK_GRADE"})
        prov.write_json(manifest_path, manifest)
        grading_manifest[shard_id] = {"graded_file": str(graded_path), "attempt": 1}
    return grading_manifest


def apply_grading(grading_manifest_path: Path, *, analysis_dir: Path = ANALYSIS,
                   committed_dir: Path = COMMITTED) -> dict[str, Any]:
    """census apply_adjudication.py's own evaluate_shard/load_pool_manifest
    (AMENDMENT.md "via the census apply_adjudication.py tooling"), unmodified;
    includes the POOLED clear-positive floor
    (`gates_lib.cg1_pooled_clear_positive`) on top of per-shard CG1."""
    census_aa = _census_apply_adjudication()

    grading_manifest = json.loads(grading_manifest_path.read_text(encoding="utf-8"))
    pool_manifest = census_aa.load_pool_manifest(committed_dir)

    shard_results = {}
    for shard_id, entry in grading_manifest.items():
        shard_results[shard_id] = census_aa.evaluate_shard(shard_id, entry, pool_manifest, analysis_dir, committed_dir)

    voided_cells = {r["cell"] for r in shard_results.values() if r["cg1"]["status"] == "VOID_CELL_TERMINAL"}
    pooled = census_aa.gates_lib.cg1_pooled_clear_positive([r["cg1"] for r in shard_results.values()])
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

    prov.write_jsonl(analysis_dir / "adjudication_applied.jsonl", applied_rows)
    report = {
        "shards": {sid: {"cell": r["cell"], "cg1": r["cg1"]} for sid, r in shard_results.items()},
        "pooled_clear_positive": pooled, "pooled_failure_cells": sorted(pooled_failure_cells),
        "voided_cells": sorted(voided_cells), "n_applied_rows": len(applied_rows),
    }
    prov.write_json(committed_dir / "adjudication_applied_manifest.json", report)
    return report


# ---------------------------------------------------------------------------
# QG-G1 / QG-G2 arithmetic over the applied (unblinded, wide) rows.
# ---------------------------------------------------------------------------

def _wide_rate_flags_seed(applied_rows: list[dict[str, Any]], all_tagged_rows: list[dict[str, Any]],
                           *, cell: str, arm: str, role: str, seed: int) -> dict[str, bool]:
    """ADAPTED from wide-instrument-control-rescore/score_wide.py's own
    `_wide_rate_flags` (same OR-of-detector-and-adjudication rate
    construction, same decoy-exclusion-by-omission semantics) with an added
    `seed` filter, since this cell's 15 arms share one literal arm string
    ("random_direction") distinguished only by `seed`. Final wide "refused"
    flag per row = detector-v2-refused OR adjudicated-abstention;
    detector-v2-negative rows whose shard/cell was voided under CG1 are
    EXCLUDED (not defaulted), matching the parent function exactly."""
    applied_by_key = {(r["cell"], r["row_key"], r["arm"], r.get("seed")): r["refused_final"] for r in applied_rows}
    out: dict[str, bool] = {}
    for r in all_tagged_rows:
        if r["cell"] != cell or r["arm"] != arm or r["role"] != role or r.get("seed") != seed:
            continue
        if r.get("_detector_v2_refused"):
            out[r["row_key"]] = True
            continue
        key = (r["cell"], r["row_key"], r["arm"], r.get("seed"))
        if key in applied_by_key:
            out[r["row_key"]] = bool(applied_by_key[key])
        # else: voided under CG1, or (impossible for L34CENSUS rows, per
        # build_pool's own construction) carved out as a clear_negative
        # decoy -- excluded, not defaulted.
    return out


def compute_seed_gates(census_rows_all: list[dict[str, Any]], applied_rows: list[dict[str, Any]],
                        *, frozen_baseline_rate: float, frozen_gated_lift: float) -> dict[str, Any]:
    """gates.yaml QG-G1/QG-G2 arithmetic. `frozen_baseline_rate` /
    `frozen_gated_lift` come from the FROZEN wicr wide_gates_report.json
    (0.11351351351351352 / 0.6270270270270271), never recomputed here."""
    import stats_lib  # WICR_DIR on sys.path (unique filename)

    detector_v2_mod = _detector_v2()
    cfg = detector_v2_mod.load_patterns()
    tagged = []
    for r in census_rows_all:
        r = dict(r)
        r["_detector_v2_refused"] = detector_v2_mod.is_refused_v2(r["text"], cfg)
        tagged.append(r)

    per_seed = {}
    lifts = []
    for seed in SEEDS:
        flags = _wide_rate_flags_seed(applied_rows, tagged, cell="L34CENSUS", arm="random_direction", role="confab", seed=seed)
        rate = stats_lib.rate_wilson(list(flags.values()))
        lift = rate["rate"] - frozen_baseline_rate
        per_seed[seed] = {"confab_tighten_wide": rate, "lift_over_baseline_signed": lift}
        lifts.append(lift)

    max_abs_lift = max(abs(x) for x in lifts) if lifts else float("inf")
    effect_ratio = (frozen_gated_lift / max_abs_lift) if max_abs_lift != 0 else float("inf")
    n_negative = sum(1 for x in lifts if x < 0)

    qg1 = {
        "frozen_gated_lift_over_baseline": frozen_gated_lift, "frozen_baseline_rate": frozen_baseline_rate,
        "max_k_abs_random_lift": max_abs_lift, "effect_ratio": effect_ratio, "threshold": 3.0,
        "pass": effect_ratio >= 3.0,
    }
    qg2 = {"n_seeds": len(lifts), "n_negative_signed_lift": n_negative, "threshold": "12/15", "pass": n_negative >= 12}

    return {"per_seed": per_seed, "QG_G1_distributional_specificity": qg1, "QG_G2_sign_consistency": qg2}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="phase", required=True)

    p_build = sub.add_parser("build-pool")
    p_build.add_argument("--seed", type=int, default=20260825)
    p_build.add_argument("--target-shard-size", type=int, default=700)
    p_build.add_argument("--rows-dir", type=Path, default=ROWS_DIR)
    p_build.add_argument("--decoy-source", type=Path, default=WICR_DECOY_SOURCE_PATH)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("--grading-manifest", type=Path, default=None, help="required unless --dry-run")
    p_apply.add_argument("--rows-dir", type=Path, default=ROWS_DIR)
    p_apply.add_argument("--out", type=Path, default=ANALYSIS / "wide_gates_report.json")

    for p in (p_build, p_apply):
        p.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()
    _import_wide_cal_pins()

    if args.phase == "build-pool":
        manifest = build_pool(seed=args.seed, target_shard_size=args.target_shard_size,
                               rows_dir=args.rows_dir, decoy_source_path=args.decoy_source)
        if args.dry_run:
            grading_manifest = mock_grade_all_shards(manifest)
            gm_path = ANALYSIS / "mock_grading_manifest.json"
            prov.write_json(gm_path, grading_manifest)
            print(f"[score_census_l34] --dry-run: mock-graded {len(grading_manifest)} shard(s); "
                  f"run `apply --dry-run` next (or pass --grading-manifest {gm_path} to `apply`).")
        print(json.dumps(manifest, indent=2))
        return 0

    if args.phase == "apply":
        if args.dry_run:
            manifest = build_pool(rows_dir=args.rows_dir)
            grading_manifest = mock_grade_all_shards(manifest)
            gm_path = ANALYSIS / "mock_grading_manifest.json"
            prov.write_json(gm_path, grading_manifest)
            grading_manifest_path = gm_path
        else:
            if args.grading_manifest is None:
                raise SystemExit("[score_census_l34] apply requires --grading-manifest unless --dry-run.")
            grading_manifest_path = args.grading_manifest

        applied_report = apply_grading(grading_manifest_path)
        print(json.dumps(applied_report, indent=2))

        frozen = prov.load_json(WICR_DIR / "analysis-committed" / "results" / "wide_gates_report.json")
        frozen_baseline_rate = frozen["WG1_random_direction_specificity"]["baseline_confab_tighten_wide"]["rate"]
        frozen_gated_lift = frozen["WG1_random_direction_specificity"]["gated_lift_over_baseline"]

        census_rows_all = load_census_rows(args.rows_dir)
        gates_report = compute_seed_gates(
            census_rows_all, prov.load_jsonl(ANALYSIS / "adjudication_applied.jsonl"),
            frozen_baseline_rate=frozen_baseline_rate, frozen_gated_lift=frozen_gated_lift,
        )
        gates_report["applied_summary"] = applied_report
        gates_report["dry_run"] = args.dry_run
        prov.write_json(args.out, gates_report)
        print(json.dumps(gates_report, indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
