#!/usr/bin/env python3
"""Adjudication-pool builder for this cell's per-family runlogs, reusing the
PINNED `abstention-wide-instrument-calibration/build_adjudication_pool.py`
(cell.yaml `grading.pinned_instrument.build_adjudication_pool`, sha256
verified below at import time) as a LIBRARY, unmodified on disk.

WHY NOT INVOKE THE PINNED SCRIPT'S OWN CLI DIRECTLY: its `main()` /
`cmd_build()` / `load_all_cell_rows()` are hardwired to
`abstention-wide-instrument-calibration/sources.py`'s own three registered
cells (QH, QL, LB), which read from THAT experiment's own staged sibling
worktrees (see `sources.py` `_QH_SRC_DIR` / `_QL_SRC_DIR` / `_LB_SRC_DIR`).
There is no code path from that CLI to this cell's own runlogs at
`experiments/no-abstention-prompt-gated-replication/analysis/<family>/runlog/`.
Running it "unmodified" in the literal CLI sense would silently build a pool
over the WRONG experiment's data.

What this script does instead: imports the pinned module via
`importlib.util` (file never edited; sha re-verified at import time) and
calls its GENERIC, data-agnostic functions --
`build_core_and_decoy_candidates`, `carve_decoys`, `pick_n_shards_by_cell`,
`cap_total_shards_by_cell`, `build_shards`, `salted_opaque_id` -- against
rows loaded from THIS cell's own runlog and normalized into the exact same
row schema `sources.normalize_row` produces:
  {cell, arm, hs_index, dose_multiplier, row_key, role, text,
   well_formed, well_formed_correct}
This is reuse-as-library, not a reimplementation: every line of pool-shaping
logic (dedup key, decoy fraction, round-robin sharding, salted opaque ids)
runs from the pinned file's own bytes.

Registered adjudication_contract (cell.yaml `grading.pinned_instrument.
adjudication_contract`): rr2-verbatim rubric, context-free-agent grader,
sharding allowed, decoys both types per shard. The rubric/grader clauses
govern the (out-of-scope, not-run-here) judge stage; the sharding/decoys
clauses are exactly what this script produces.

SCOPE: pool build only. Does NOT run `apply_adjudication.py` (the LLM judge
stage), which awaits separate PI approval per the standing task scope.

Usage: python build_adjudication_pool_from_runlog.py --family qwen3-4b [--seed N] [--salt S]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
CALIB_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"
CELL = None  # loaded lazily in main() after argparse, kept module-global for helpers


# ---------------------------------------------------------------------------
# Per-family runlog -> normalized-row loading.
# ---------------------------------------------------------------------------

# hs_index per family, from cell.yaml `families.<family>.site` (fixed
# operating point, not a dose ladder, for every family in this cell --
# dose_multiplier is therefore always None, matching how sources.py's own
# QH cell -- also a fixed single operating point, not QL's ladder -- is
# normalized).
FAMILY_HS_INDEX = {
    "qwen3-4b": 23,
    "qwen3.5-4b": 20,
    "llama-3.2-3b": 17,
    "mistral-7b-v0.3": 15,
    "gemma-4-e4b": 15,
}

# Which grader.py (grade_one) computes well_formed_correct for each family's
# runlog rows -- the SAME module each family's own run_*.py script already
# imports for this purpose (grade_one is not re-derived here; reused
# unmodified via direct import, one per family to avoid any cross-family
# sys.modules collision).
FAMILY_GRADER_DIR = {
    "qwen3-4b": REPO_ROOT / "experiments" / "j-space-midband-write-sweep-qwen3-4b",
    "llama-3.2-3b": REPO_ROOT / "experiments" / "j-space-cross-family-layer-contrast",
    "mistral-7b-v0.3": REPO_ROOT / "experiments" / "j-space-cross-family-layer-contrast",
    "gemma-4-e4b": REPO_ROOT / "experiments" / "gemma4-e4b-kv-seam-quarantine",
    # qwen3.5-4b's own run_qwen35_4b.py grades via gate_lib.rate_summary, not
    # grader.grade_one, and its runlog rows already carry
    # `well_formed_correct` from gen_lib.grade_row at generation time -- see
    # _load_family_rows's schema branch below.
}


def _load_grader_for(family: str):
    grader_dir = FAMILY_GRADER_DIR[family]
    spec = importlib.util.spec_from_file_location(f"_pool_grader_{family.replace('.', '_').replace('-', '_')}", grader_dir / "grader.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_jsonl(p: Path) -> list[dict[str, Any]]:
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


# AMENDMENT.md "Arms": per-family registered arms, one runlog file each
# (qwen3.5-4b is handled separately in load_family_rows -- its own
# baseline.jsonl/gated.jsonl schema, not one file per arm). cell.yaml does
# not carry a per-family arms list, so this mirrors each family's own
# run_*.py script (already reviewed/fixed above), not a new decision.
FAMILY_ARMS = {
    "qwen3-4b": ["no_op", "gated", "random_direction"],
    "llama-3.2-3b": ["no_op", "gated", "random_direction"],
    "mistral-7b-v0.3": ["no_op", "gated"],
    "gemma-4-e4b": ["no_op", "gated"],
}


def _arms_for(family: str) -> list[str]:
    return FAMILY_ARMS[family]


def _runlog_dir_for(family: str) -> Path:
    return HERE / "analysis" / family / "runlog"


def load_family_rows(family: str) -> list[dict[str, Any]]:
    """Normalized rows for one family, ALL registered arms, tracked roles
    only (confab, known_correct_answered -- same population scope as
    sources.py's TRACKED_ROLES; this cell has no unknown_refused role)."""
    runlog_dir = _runlog_dir_for(family)
    hs_index = FAMILY_HS_INDEX[family]
    rows: list[dict[str, Any]] = []

    if family == "qwen3.5-4b":
        # This family's own generate stage already writes well_formed /
        # well_formed_correct per row via gen_lib.grade_row (see
        # run_qwen35_4b.py cmd_generate -> steer_lib.run_rows), and its rows
        # live in baseline.jsonl (shared no_op pass) + gated.jsonl (fired
        # subset only) rather than one file per arm. Reconstruct the two
        # registered arms (no_op, gated) the same way that family's own
        # cmd_grade does: combine_active_and_baseline.
        baseline_by_key = {r["row_key"]: r for r in load_jsonl(runlog_dir / "baseline.jsonl")}
        gated_by_key = {r["row_key"]: r for r in load_jsonl(runlog_dir / "gated.jsonl")}
        for arm, active_by_key in (("no_op", {}), ("gated", gated_by_key)):
            for row_key, base_rec in baseline_by_key.items():
                rec = active_by_key.get(row_key) or base_rec
                if rec.get("role") not in ("confab", "known_correct_answered"):
                    continue
                rows.append({
                    "cell": family, "arm": arm, "hs_index": hs_index, "dose_multiplier": None,
                    "row_key": row_key, "role": rec["role"],
                    "text": rec.get("answer_text", rec.get("out_text", "")),
                    "well_formed": bool(rec.get("well_formed", False)),
                    "well_formed_correct": bool(rec.get("well_formed_correct", False)),
                })
        return rows

    grader_mod = _load_grader_for(family)
    for arm in _arms_for(family):
        for rec in load_jsonl(runlog_dir / f"{arm}.jsonl"):
            if rec.get("role") not in ("confab", "known_correct_answered"):
                continue
            og = grader_mod.grade_one(rec.get("out_text", ""), rec.get("aliases"))
            rows.append({
                "cell": family, "arm": arm, "hs_index": hs_index, "dose_multiplier": None,
                "row_key": rec["row_key"], "role": rec["role"],
                "text": rec.get("out_text", ""),
                "well_formed": bool(not og["degenerate"]),
                "well_formed_correct": bool(og["well_formed_correct"]),
            })
    return rows


# ---------------------------------------------------------------------------
# Pinned build_adjudication_pool.py, imported as a library (never edited).
# ---------------------------------------------------------------------------

def _import_detector_v2_once():
    """Imports detector_v2 correctly and permanently caches it in
    sys.modules["detector_v2"] -- see run_qwen3_4b.py's identical helper for
    the full sys.modules-collision rationale. Doing this ONCE, before
    loading the pinned build_adjudication_pool.py, matters here specifically
    because that module's OWN `import detector_v2` calls are deferred
    (inside `cmd_build`/`is_refused_v2`, not at module-exec time) and run
    AFTER `load_family_rows` has already poisoned sys.modules["grader"] with
    a family-specific grader.py. Once "detector_v2" itself is cached here,
    any later `import detector_v2` (from anywhere, including from inside the
    pinned module's functions) just returns this cached, correctly-wired
    object -- Python does not re-resolve "grader" on a cache hit."""
    calib_grader_path = CALIB_DIR / "grader.py"
    spec = importlib.util.spec_from_file_location("_calib_grader_for_pool", calib_grader_path)
    calib_grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(calib_grader)
    if not hasattr(calib_grader, "_is_stated_confidence_refusal"):
        raise RuntimeError(f"{calib_grader_path} lacks _is_stated_confidence_refusal")

    sys.path.insert(0, str(CALIB_DIR))
    prior_grader = sys.modules.get("grader")
    sys.modules["grader"] = calib_grader
    try:
        import detector_v2
    finally:
        if prior_grader is not None:
            sys.modules["grader"] = prior_grader
        else:
            sys.modules.pop("grader", None)
    return detector_v2


def _load_pinned_pool_module():
    """Loads build_adjudication_pool.py from its pinned path and re-verifies
    its sha256 against cell.yaml's own pin before use -- if the pinned file
    drifted since sign, this raises rather than silently running against a
    different version of the instrument. Module-level, this file only does
    `import sources` (no grader collision risk at load time); its deferred
    `import detector_v2` calls are handled by pre-caching detector_v2 via
    `_import_detector_v2_once` before this is called."""
    pinned = CELL["grading"]["pinned_instrument"]["build_adjudication_pool"]
    path = REPO_ROOT / pinned["path"]
    actual_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    expected_sha = pinned["sha256"]
    if actual_sha != expected_sha:
        raise RuntimeError(
            f"build_adjudication_pool.py sha mismatch: cell.yaml pins "
            f"{expected_sha}, on-disk file is {actual_sha}. Refusing to run "
            "against a drifted pinned instrument."
        )
    spec = importlib.util.spec_from_file_location("_pinned_build_adjudication_pool", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(CALIB_DIR))  # so this module's own `import sources` resolves
    spec.loader.exec_module(mod)
    print(f"[build_pool] pinned build_adjudication_pool.py loaded from {path} (sha256 {actual_sha} matches cell.yaml)", flush=True)
    return mod


EXTERNAL_POSITIVE_TRACKED_ROLES = ("confab", "known_correct_answered")
EXTERNAL_POSITIVE_ARM_PREFERENCE = ("random_direction", "gated")  # pinned clear_positive definition first, then top up


def load_external_positives(source_path: Path, seed: int, cap: int, detector_v2, cfg: dict, external_cell_tag: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Selects externally-sourced clear_positive candidate rows for a family
    whose OWN no-abstention-prompt data has structurally zero native
    positives (e.g. qwen3-4b, per this cell's pool v1: n_clear_positive_candidates=0).

    Re-derives refusal with the PINNED detector_v2 over the source file's own
    raw generation text (`out_text`, falling back to `answer_text` for
    sources that use that field name instead -- same fallback chain as
    load_family_rows' own qwen3.5-4b branch above) -- NEVER trusts that
    file's own `semantic_refuse` flag (per lead ruling, NOTEBOOK.md
    2026-08-29). Prefers `random_direction`-arm
    detector-refused rows first (the pinned instrument's own clear_positive
    definition in build_adjudication_pool.build_core_and_decoy_candidates),
    then tops up from `gated`-arm detector-refused rows, up to `cap`. Seeded
    sample so the selection is reproducible.

    Rows are tagged with `external_cell_tag` (NOT the target family's own
    cell name) so they can never collide with the target family's own
    (cell, row_key, arm) dedup key even if a row_key happens to be shared
    across the two experiments' pools. Their true source arm is preserved
    per-row -- visible only in the gitignored id map the pinned build_shards
    writes, never in the committed pool manifest (counts/shas only).

    Returns (normalized_rows, selection_report). selection_report carries
    counts only, no text, no row_key -- safe to print/commit.
    """
    rows = load_jsonl(source_path)
    tracked = [r for r in rows if r.get("role") in EXTERNAL_POSITIVE_TRACKED_ROLES]

    refused_by_arm: dict[str, list[dict[str, Any]]] = {arm: [] for arm in EXTERNAL_POSITIVE_ARM_PREFERENCE}
    for r in tracked:
        arm = r.get("arm")
        if arm not in refused_by_arm:
            continue
        raw_text = r.get("out_text", r.get("answer_text", ""))
        if detector_v2.is_refused_v2(raw_text, cfg):
            refused_by_arm[arm].append(r)

    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    selected_by_arm: dict[str, int] = {arm: 0 for arm in EXTERNAL_POSITIVE_ARM_PREFERENCE}
    for arm in EXTERNAL_POSITIVE_ARM_PREFERENCE:
        if len(selected) >= cap:
            break
        pool = sorted(refused_by_arm[arm], key=lambda r: r["row_key"])  # deterministic pre-shuffle order
        rng.shuffle(pool)
        for r in pool:
            if len(selected) >= cap:
                break
            selected.append(r)
            selected_by_arm[arm] += 1

    normalized = [
        {
            "cell": external_cell_tag, "arm": r["arm"], "hs_index": None, "dose_multiplier": None,
            "row_key": r["row_key"], "role": r["role"], "text": r.get("out_text", r.get("answer_text", "")),
            "well_formed": bool((r.get("grade") or {}).get("well_formed", False)),
            "well_formed_correct": bool(r.get("well_formed_correct", False)),
        }
        for r in selected
    ]

    report = {
        "source_path": str(source_path),
        "n_source_rows": len(rows),
        "n_tracked_rows": len(tracked),
        "n_refused_candidates_by_arm": {arm: len(refused_by_arm[arm]) for arm in EXTERNAL_POSITIVE_ARM_PREFERENCE},
        "seed": seed,
        "cap": cap,
        "n_selected": len(normalized),
        "n_selected_by_arm": selected_by_arm,
        "external_cell_tag": external_cell_tag,
        "note": "planted clear_positive decoys, judge-sensitivity control only; source arm recorded per-row only in the gitignored id map",
    }
    return normalized, report


def build_pool_for_family(family: str, seed: int, salt: str | None, target_shard_size: int,
                           external_positives_path: Path | None = None,
                           external_positives_seed: int = 20260714,
                           external_positives_cap: int = 20,
                           external_positives_replace: bool = False,
                           version_subdir: str = "") -> dict[str, Any]:
    """`version_subdir`: "" (default) writes to analysis/<family>/shards/ and
    analysis-committed/<family>/adjudication_pool_manifest.json, exactly as
    before. A non-empty value (e.g. "v2") nests BOTH the analysis and
    committed roots one level deeper (analysis/<family>/v2/shards/,
    analysis-committed/<family>/v2/adjudication_pool_manifest.json) so a
    later pool build never overwrites an earlier one for the same family,
    while keeping the "shards" subdir name and manifest filename literally
    what the PINNED apply_adjudication.py hardcodes (it accepts
    --analysis-dir/--committed-dir overrides but not a filename/dirname
    override, so versioning must happen one level up, not via a suffix on
    those names)."""
    rows = load_family_rows(family)
    detector_v2 = _import_detector_v2_once()
    pool_mod = _load_pinned_pool_module()
    cfg = detector_v2.load_patterns()

    cell_rows = {family: rows}
    core, neg_cand, pos_cand = pool_mod.build_core_and_decoy_candidates(cell_rows, cfg)

    external_report = None
    if external_positives_path is not None:
        ext_rows, external_report = load_external_positives(
            external_positives_path, external_positives_seed, external_positives_cap,
            detector_v2, cfg, external_cell_tag=f"{family}_wicr_external",
        )
        if external_positives_replace:
            # v2 judge-lane contract (NOTEBOOK.md pre-statement, 2026-08-30):
            # planted clear_positive decoys come from the external with-prompt
            # gated-arm draw INSTEAD OF native random/no-prompt-arm detector
            # hits -- native candidates are excluded, not augmented.
            external_report["replace_native_positives"] = {
                "n_native_candidates_excluded": len(pos_cand),
                "note": "v2 contract: external gated-arm draw replaces native clear_positive candidates",
            }
            pos_cand = ext_rows
        else:
            pos_cand = pos_cand + ext_rows

    salt = salt or secrets.token_hex(32)
    rng = random.Random(seed)
    remaining_core, decoys_neg, decoys_pos = pool_mod.carve_decoys(core, neg_cand, pos_cand, rng)

    n_shards_by_cell = pool_mod.pick_n_shards_by_cell(remaining_core, target_shard_size)
    max_total_shards = max(1, min(len(decoys_neg), len(decoys_pos))) if (decoys_neg and decoys_pos) else max(1, len(n_shards_by_cell))
    n_shards_by_cell = pool_mod.cap_total_shards_by_cell(n_shards_by_cell, max_total_shards)
    shards = pool_mod.build_shards(remaining_core, decoys_neg, decoys_pos, n_shards_by_cell, seed, salt)

    out_analysis = HERE / "analysis" / family / version_subdir if version_subdir else HERE / "analysis" / family
    out_committed = HERE / "analysis-committed" / family / version_subdir if version_subdir else HERE / "analysis-committed" / family
    shards_dir = out_analysis / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    out_committed.mkdir(parents=True, exist_ok=True)

    shard_manifest_entries = []
    for shard in shards:
        pool_path = shards_dir / f"{shard['shard_id']}.jsonl"
        map_path = shards_dir / f"{shard['shard_id']}_id_map.jsonl"
        pool_mod.write_jsonl(pool_path, shard["blinded_pool"])
        pool_mod.write_jsonl(map_path, shard["id_map"])
        pool_sha = hashlib.sha256(pool_path.read_bytes()).hexdigest()
        shard_manifest_entries.append({
            "shard_id": shard["shard_id"],
            "cell": shard["cell"],
            "pool_sha256": pool_sha,
            "row_count": len(shard["blinded_pool"]),
            "n_core": shard["n_core"],
            "n_decoy_clear_negative": shard["n_decoy_clear_negative"],
            "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "family": family,
        "n_rows_loaded": len(rows),
        "n_core_before_decoy_carve": len(core),
        "n_clear_negative_candidates": len(neg_cand),
        "n_clear_positive_candidates": len(pos_cand),
        "seed": seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": len(shards),
        "n_core_total": len(remaining_core),
        "n_decoy_clear_negative_total": len(decoys_neg),
        "n_decoy_clear_positive_total": len(decoys_pos),
        "shards": shard_manifest_entries,
        "source_instrument": {
            "build_adjudication_pool_path": str(CELL["grading"]["pinned_instrument"]["build_adjudication_pool"]["path"]),
            "build_adjudication_pool_sha256": CELL["grading"]["pinned_instrument"]["build_adjudication_pool"]["sha256"],
        },
        "note": "pool build only; apply_adjudication.py (LLM judge stage) NOT run, per standing task scope",
    }
    if external_report is not None:
        manifest["external_positive_source"] = external_report
    manifest_path = out_committed / "adjudication_pool_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    global CELL
    import yaml
    CELL = yaml.safe_load((HERE / "cell.yaml").read_text())

    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True, choices=list(FAMILY_HS_INDEX.keys()))
    ap.add_argument("--seed", type=int, default=20260714)  # same default as the pinned script, for provenance consistency
    ap.add_argument("--salt", default=None)
    ap.add_argument("--target-shard-size", type=int, default=700)  # same default as the pinned script
    ap.add_argument("--external-positives-file", default=None,
                     help="path (repo-relative or absolute) to a with-prompt runlog to draw planted "
                          "clear_positive decoys from, for a family whose own data has none")
    ap.add_argument("--external-positives-seed", type=int, default=20260714)
    ap.add_argument("--external-positives-cap", type=int, default=20)
    ap.add_argument("--external-positives-replace", action="store_true",
                     help="use the external draw as the ONLY clear_positive candidate set, "
                          "excluding native candidates (v2 judge-lane contract: external "
                          "with-prompt gated-arm refusals INSTEAD OF random/no-prompt-arm "
                          "detector hits)")
    ap.add_argument("--version-subdir", default="",
                     help="nest both analysis/<family>/ and analysis-committed/<family>/ one level "
                          "deeper under this name (e.g. 'v2'), so a later pool build for the same "
                          "family never overwrites an earlier one. 'shards' subdir name and "
                          "'adjudication_pool_manifest.json' filename stay literal underneath, "
                          "matching what the pinned apply_adjudication.py hardcodes.")
    args = ap.parse_args()

    external_path = None
    if args.external_positives_file:
        p = Path(args.external_positives_file)
        external_path = p if p.is_absolute() else (REPO_ROOT / p)
        if not external_path.is_file():
            raise SystemExit(f"--external-positives-file not found: {external_path}")

    manifest = build_pool_for_family(
        args.family, args.seed, args.salt, args.target_shard_size,
        external_positives_path=external_path,
        external_positives_seed=args.external_positives_seed,
        external_positives_cap=args.external_positives_cap,
        external_positives_replace=args.external_positives_replace,
        version_subdir=args.version_subdir,
    )
    out_analysis_rel = f"analysis/{args.family}/{args.version_subdir}/shards" if args.version_subdir else f"analysis/{args.family}/shards"
    out_committed_rel = f"analysis-committed/{args.family}/{args.version_subdir}/adjudication_pool_manifest.json" if args.version_subdir else f"analysis-committed/{args.family}/adjudication_pool_manifest.json"
    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in manifest["shards"]]
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"\n[build_pool] {args.family}: wrote {manifest['n_shards']} shard(s) under "
        f"{out_analysis_rel} (gitignored). Manifest committed to "
        f"{out_committed_rel}. "
        "NO grading has occurred and NO id map has been unblinded.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
