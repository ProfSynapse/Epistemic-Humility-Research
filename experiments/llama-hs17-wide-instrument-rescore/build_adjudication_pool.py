#!/usr/bin/env python3
"""Blinded adjudication pool builder for llama-hs17-wide-instrument-rescore
(AMENDMENT.md "Instruments" -- wide two-instrument stack; per
`.skills/experiment-runner/reference/abstention-grading.md`).

Reuse, not reinvention: the generic sharding/decoy/opaque-id mechanics
(`carve_decoys`, `salted_opaque_id`, `pick_n_shards_by_cell`,
`cap_total_shards_by_cell`, `build_shards`) are imported DIRECTLY from
`abstention-wide-instrument-calibration/build_adjudication_pool.py` (sys.path,
no copy) -- those functions are pure over generic `{cell, row_key, arm, ...}`
row dicts and carry no cell-specific assumption. What THIS module supplies
instead of abstention's own `build_core_and_decoy_candidates` /
`load_all_cell_rows` (which hardcode a 3-cell QH/QL/LB corpus and a single
literal `arm == "random_direction"` predicate) is the core/candidate
construction for THIS cell's own arm vocabulary: one cell ("WR"), 17 arms,
of which 15 have DISTINCT literal ids (`arm2_random_<seed>`) rather than one
shared arm string differentiated by a `seed` field -- so, unlike
`qwen3-4b-l34-placebo-seed-census` (which needed a seed-aware pool builder
because its 15 arms DID collide on one literal arm string), this cell's rows
already key uniquely on `(cell, row_key, arm)` and can use
`abstention-wide-instrument-calibration`'s pool mechanics without the
census's seed-in-schema workaround.

CORE POOL: every detector-v2-negative row from every arm (0, 1, 2..16),
across both tracked roles (confab: all 17 arms; known_correct_answered:
arm0 and arm1 only, per cell.yaml's registered population) -- "every
detector-negative row from every scored arm and both populations" per the
reference doc.

DECOYS:
  clear_negative  known_correct_answered rows (arm0 or arm1) that are
                  well_formed_correct AND detector-v2-non-refused --
                  abstention-wide-instrument-calibration's OWN convention
                  (decoys carved out of the scored known-correct population
                  itself); this cell registers no held-back pool, so RR3's
                  successor fix (a) does not apply here.
  clear_positive  arm2_random_<seed> rows (any of the 15) where detector-v2
                  DOES mark refused -- the placebo/random-direction arms are
                  this cell's own "unambiguous abstention" source, exactly
                  analogous to abstention's own `random_direction` arm.

CONTAINMENT: shard pool files and id maps (carry `text` / `row_key`) are
written ONLY under gitignored `analysis/`. The committed pool manifest
(`analysis-committed/<family>/adjudication_pool_manifest.json`) carries only
{seed, id_salt_sha256, n_shards, shards: [{shard_id, cell, pool_sha256,
row_count, n_core, n_decoy_clear_negative, n_decoy_clear_positive,
opaque_ids}]} -- no text, no row_key, no arm/role.
"""

from __future__ import annotations

import argparse
import hashlib
import random
import secrets
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
WIDE_CAL_DIR = REPO_ROOT / "experiments" / "abstention-wide-instrument-calibration"

import score_wide_rescore as swr  # noqa: E402  (same directory; load_jsonl/write_json/verify_wide_pins/ARM_IDS/FAMILY)

FAMILY = swr.FAMILY
ARM_IDS = swr.ARM_IDS
ANALYSIS = HERE / "analysis" / FAMILY
ANALYSIS_COMMITTED = HERE / "analysis-committed" / FAMILY
SCORED_DIR = ANALYSIS / "scored"
SHARDS_DIR = ANALYSIS / "shards"

DEFAULT_TARGET_SHARD_SIZE = 700  # abstention-wide-instrument-calibration's own convention, reused as-is


def _bap():
    # abstention-wide-instrument-calibration/build_adjudication_pool.py bare-
    # imports `sources` at its own module top; routed through
    # score_wide_rescore.import_from_dir (the eviction-and-restore loader,
    # ported from qwen3-4b-l34-placebo-seed-census/pipeline_census_l34.py)
    # so a same-named `sources` module cached from some OTHER experiment
    # directory in this same process can never be silently substituted.
    return swr._cached_import("wr_build_adjudication_pool", WIDE_CAL_DIR, "build_adjudication_pool.py")


# --------------------------------------------------------------------------
# This cell's own core/candidate construction (the one thing NOT reused from
# abstention's own build_core_and_decoy_candidates -- see module docstring).
# --------------------------------------------------------------------------

def load_all_scored_rows(scored_dir: Path = SCORED_DIR) -> list[dict[str, Any]]:
    """Loads every arm's scored rows (score_wide_rescore.py output, already
    tagged with `refused_v2`) and normalizes to the generic pool-builder
    schema: {cell, row_key, arm, role, text, well_formed_correct, refused_v2,
    fire}. `fire` is carried through for WR-G4's fired-only join, done later
    by gates_wide_rescore.py against this same normalized row list -- NOT
    part of the id_map/opaque-id payload (which stays generic, per
    abstention's own schema)."""
    out = []
    for arm_id in ARM_IDS:
        path = scored_dir / f"{arm_id}.jsonl"
        if not path.is_file():
            raise SystemExit(f"[build_adjudication_pool] missing scored rows for {arm_id}: {path}; run score_wide_rescore.py first")
        for r in swr.load_jsonl(path):
            out.append({
                "cell": "WR", "row_key": r["row_key"], "arm": arm_id, "role": r["role"],
                "text": r["out_text"], "well_formed_correct": bool(r["well_formed_correct"]),
                "refused_v2": bool(r["refused_v2"]), "fire": bool(r["fire"]),
            })
    return out


def build_core_and_candidates(rows: list[dict[str, Any]]) -> tuple[list[dict], list[dict], list[dict]]:
    """Returns (core, clear_negative_candidates, clear_positive_candidates).
    core = refused_v2==False rows (any arm, either tracked role). Mirrors
    abstention's own build_core_and_decoy_candidates predicate shape, adapted
    to this cell's arm vocabulary (see module docstring)."""
    core = [r for r in rows if not r["refused_v2"]]
    clear_negative_candidates = [
        r for r in core if r["role"] == "known_correct_answered" and r["well_formed_correct"]
    ]
    clear_positive_candidates = [
        r for r in rows if r["arm"].startswith("arm2_random_") and r["refused_v2"]
    ]
    return core, clear_negative_candidates, clear_positive_candidates


def build_pool(*, seed: int = 20260826, salt: str | None = None, target_shard_size: int = DEFAULT_TARGET_SHARD_SIZE,
               scored_dir: Path = SCORED_DIR, analysis_dir: Path = ANALYSIS,
               committed_dir: Path = ANALYSIS_COMMITTED) -> dict[str, Any]:
    bap = _bap()

    rows = load_all_scored_rows(scored_dir)
    core, neg_cand, pos_cand = build_core_and_candidates(rows)

    salt = salt or secrets.token_hex(32)
    rng = random.Random(seed)
    remaining_core, decoys_neg, decoys_pos = bap.carve_decoys(core, neg_cand, pos_cand, rng)

    n_shards_by_cell = bap.pick_n_shards_by_cell(remaining_core, target_shard_size)
    max_total_shards = max(1, min(len(decoys_neg), len(decoys_pos))) if decoys_neg and decoys_pos else 1
    n_shards_by_cell = bap.cap_total_shards_by_cell(n_shards_by_cell, max_total_shards)
    shards = bap.build_shards(remaining_core, decoys_neg, decoys_pos, n_shards_by_cell, seed, salt)

    shards_dir = analysis_dir / "shards"
    shards_dir.mkdir(parents=True, exist_ok=True)
    shard_manifest_entries = []
    for shard in shards:
        pool_path = shards_dir / f"{shard['shard_id']}.jsonl"
        map_path = shards_dir / f"{shard['shard_id']}_id_map.jsonl"
        swr.write_jsonl(pool_path, shard["blinded_pool"])
        swr.write_jsonl(map_path, shard["id_map"])
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
    swr.write_json(committed_dir / "adjudication_pool_manifest.json", manifest)
    print(
        f"[build_adjudication_pool] wrote {len(shards)} shard(s) under {shards_dir} (gitignored). "
        f"Pool manifest at {committed_dir / 'adjudication_pool_manifest.json'} "
        "(NOT committed to git by this script -- the lead commits it before dispatching grading "
        "agents, per the unblinding-order guarantee). NO grading has occurred."
    )
    return manifest


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20260826)
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.add_argument("--scored-dir", type=Path, default=SCORED_DIR)
    args = ap.parse_args(argv)
    build_pool(seed=args.seed, salt=args.salt, target_shard_size=args.target_shard_size, scored_dir=args.scored_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
