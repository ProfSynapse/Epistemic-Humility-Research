#!/usr/bin/env python3
"""Blinded, SHARDED adjudication pool builder for
abstention-wide-instrument-calibration.

Adapted from rr2-mistral-adjudicated-refusal-confirm/build_adjudication_pool.py
(mechanics ported: salted opaque ids, seeded shuffle, decoys carved out of
core so no (cell, row_key, arm) triple double-counts). Extended per this
experiment's cell.yaml/AMENDMENT.md for a MULTI-CELL pool and SHARDING
(cell.yaml `instrument.adjudication.sharding_allowed: true`,
`decoys_per_shard: both_types`):

CORE POOL: every detector-v2-negative row from every staged cell, restricted
to the two tracked populations (confab, known_correct_answered -- see
sources.py module docstring for the LB unknown_refused exclusion and the QL
layer-scope reading), across:
  QH  baseline + random_direction arms, full population, both roles
  QL  baseline arm (full, both roles) + random_direction arm RESTRICTED to
      the registered seeded subsample (250 confab rows per (hs_index, dose)
      cell; sources.ql_subsample, drawn before any grading)
  LB  baseline arm, confab + known_correct_answered roles only

Deduplicated on (cell, row_key, arm) -- not on row_key alone, matching RR2's
rationale: different arms of the same cell can carry different generation
text for the same row_key, and different cells' row_keys are not assumed
disjoint (both KUQ/TriviaQA/PopQA-sourced datasets reappear across
families), so cell is folded into the key and into the opaque-id salt input.

DECOYS (both types, drawn globally across cells, then distributed per shard
so every shard carries both types -- gates.yaml CG1 is evaluated PER SHARD):
  clear_negative  known_correct_answered rows (any staged cell, any arm)
                  that are well_formed_correct AND detector-v2-non-refused.
  clear_positive  random_direction (placebo) arm rows (QH or QL; LB has no
                  placebo -- cell.yaml `placebo: none_on_disk_out_of_scope`)
                  where detector-v2 DOES mark refused.
Decoys are carved OUT of core (clear_negative) or drawn disjointly from
refused_v2==True rows (clear_positive, disjoint from core by construction
since core requires refused_v2==False) -- identical rationale to RR2.
Decoys are never part of any scored rate (calibration_scorer.py excludes
every `is_decoy: true` row from every rate).

SHARDING is CELL-SCOPED: shards never mix core rows from two different
cells. This is forced by gates.yaml `on_second_failure:
void_cell_report_straight` -- a second CG1 failure voids "the cell," which
is only an unambiguous operation if every shard's core content belongs to
exactly one cell (voiding "the cell" then means voiding every shard whose
shard_id is prefixed with that cell). Each cell's core rows are
independently seed-shuffled and split into that cell's own N_cell
contiguous, near-equal chunks (N_cell sized off that cell's own core size,
so small cells don't get artificially over-sharded). DECOYS are drawn from
a GLOBAL candidate pool across all three cells (LB has no random_direction
arm at all -- cell.yaml `placebo: none_on_disk_out_of_scope` -- so it has no
clear_positive candidates of its own; LB's shards can only carry clear
positive decoys sourced from QH/QL) and distributed round-robin across
EVERY shard from every cell combined, so every shard -- regardless of which
cell its core came from -- gets its own slice of both decoy types.

OUTPUTS:
  analysis/shards/shard_<NN>.jsonl                 gitignored; [{opaque_id, text}]
  analysis/shards/shard_<NN>_id_map.jsonl          gitignored; full mapping
      {opaque_id, cell, row_key, arm, hs_index, dose_multiplier, role,
       is_decoy, decoy_type}
  analysis-committed/adjudication_pool_manifest.json   COMMITTED; ONLY
      {seed, id_salt_sha256, n_shards, shards: [{shard_id, sha256, row_count,
       n_core, n_decoy_clear_negative, n_decoy_clear_positive, opaque_ids
       (sorted)}]} -- no text, no row_key, no cell/arm/role, per this
      experiment's containment rule.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import sys
from pathlib import Path
from typing import Any

import sources

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

DECOY_FRACTION = 0.15  # of the core pool size, split evenly between the two decoy types (RR2 convention, reapplied globally)
DEFAULT_TARGET_SHARD_SIZE = 700  # build-time interpretation of "sharding allowed": no registered shard count/size exists in cell.yaml, so a shard size in the same order as RR2's single unsharded pool (3582 rows, one grader) is chosen as a reasonable per-agent load; see NOTEBOOK.md.


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def is_refused_v2(text: str, cfg: dict) -> bool:
    import detector_v2
    return detector_v2.is_refused_v2(text, cfg)


# ---------------------------------------------------------------------------
# Core pool assembly across the three staged cells.
# ---------------------------------------------------------------------------

def load_all_cell_rows() -> dict[str, list[dict[str, Any]]]:
    """{cell: [normalized rows, all arms, tracked roles only, QL random_direction
    restricted to the registered subsample]}."""
    out: dict[str, list[dict[str, Any]]] = {"QH": [], "QL": [], "LB": []}

    qh = sources.load_qh()
    for arm_rows in qh.values():
        out["QH"].extend(r for r in arm_rows if r["role"] in sources.TRACKED_ROLES)

    ql_baseline = sources.load_ql_baseline()
    out["QL"].extend(r for r in ql_baseline if r["role"] in sources.TRACKED_ROLES)
    ql_rand_all = sources.load_ql_random_direction_all()
    ql_subsample = sources.ql_subsample(ql_rand_all)
    for rows in ql_subsample.values():
        out["QL"].extend(rows)  # already confab-only, role-filtered by ql_subsample

    lb_rows = sources.load_lb()
    out["LB"].extend(r for r in lb_rows if r["role"] in sources.TRACKED_ROLES)

    return out


def build_core_and_decoy_candidates(cell_rows: dict[str, list[dict[str, Any]]], cfg: dict) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (core, clear_negative_candidates, clear_positive_candidates).

    `core` = every row (any cell, any arm, tracked roles) with refused_v2
    False. clear_negative candidates are known_correct_answered rows drawn
    from `core` itself (well_formed_correct AND refused_v2 False) -- these
    get REMOVED from core when chosen as decoys (RR2 rationale: they already
    satisfy core's own criterion, so choosing them as decoys must not double
    count). clear_positive candidates are refused_v2==True rows from
    random_direction arms only (QH, QL) -- disjoint from core by
    construction, no removal needed.
    """
    core: list[dict[str, Any]] = []
    clear_positive_candidates: list[dict[str, Any]] = []
    for cell, rows in cell_rows.items():
        for r in rows:
            refused = is_refused_v2(r["text"], cfg)
            r = {**r, "refused_v2": refused}
            if refused:
                if r["arm"] == "random_direction":
                    clear_positive_candidates.append(r)
                continue
            core.append(r)

    clear_negative_candidates = [
        r for r in core
        if r["role"] == "known_correct_answered" and r["well_formed_correct"]
    ]
    return core, clear_negative_candidates, clear_positive_candidates


def carve_decoys(core: list[dict[str, Any]], clear_negative_candidates: list[dict[str, Any]],
                  clear_positive_candidates: list[dict[str, Any]], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    n_each = max(1, round(len(core) * DECOY_FRACTION / 2)) if core else 0

    neg_pool = clear_negative_candidates[:]
    rng.shuffle(neg_pool)
    chosen_neg = neg_pool[:n_each]
    chosen_neg_keys = {(r["cell"], r["row_key"], r["arm"]) for r in chosen_neg}
    remaining_core = [r for r in core if (r["cell"], r["row_key"], r["arm"]) not in chosen_neg_keys]
    decoys_neg = [{**r, "decoy_type": "clear_negative"} for r in chosen_neg]

    pos_pool = clear_positive_candidates[:]
    rng.shuffle(pos_pool)
    decoys_pos = [{**r, "decoy_type": "clear_positive"} for r in pos_pool[:n_each]]

    return remaining_core, decoys_neg, decoys_pos


def salted_opaque_id(salt: str, cell: str, row_key: str, arm: str, regrade_index: int = 0) -> str:
    payload = f"{salt}:{cell}:{row_key}:{arm}:{regrade_index}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _round_robin_chunks(items: list[Any], n_shards: int) -> list[list[Any]]:
    """Splits `items` (already in the desired deterministic order) into
    n_shards near-equal contiguous chunks, remainder distributed to the
    first chunks so every chunk gets >= floor(len/n_shards) items and the
    first `len % n_shards` chunks get one extra."""
    chunks: list[list[Any]] = [[] for _ in range(n_shards)]
    base, rem = divmod(len(items), n_shards)
    idx = 0
    for i in range(n_shards):
        take = base + (1 if i < rem else 0)
        chunks[i] = items[idx:idx + take]
        idx += take
    return chunks


def plan_cell_shards(core: list[dict[str, Any]], n_shards_by_cell: dict[str, int], seed: int) -> dict[str, list[list[dict[str, Any]]]]:
    """{cell: [core_chunk_0, core_chunk_1, ...]}, one deterministic seeded
    shuffle+split per cell (cell-scoped, per module docstring)."""
    by_cell: dict[str, list[dict[str, Any]]] = {}
    for r in core:
        by_cell.setdefault(r["cell"], []).append(r)
    out: dict[str, list[list[dict[str, Any]]]] = {}
    for cell, rows in by_cell.items():
        rows_sorted = sorted(rows, key=lambda r: (r["row_key"], r["arm"]))
        random.Random(f"{seed}:{cell}").shuffle(rows_sorted)
        out[cell] = _round_robin_chunks(rows_sorted, n_shards_by_cell[cell])
    return out


def build_shards(core: list[dict[str, Any]], decoys_neg: list[dict[str, Any]], decoys_pos: list[dict[str, Any]],
                  n_shards_by_cell: dict[str, int], seed: int, salt: str) -> list[dict[str, Any]]:
    """Returns a list of shard dicts: {shard_id, blinded_pool, id_map}, one
    per (cell, chunk_index). shard_id is prefixed with the cell so a
    second-failure void unambiguously identifies which cell's shards to
    exclude (`shard_id.split('_shard_')[0]`)."""
    cell_chunks = plan_cell_shards(core, n_shards_by_cell, seed)

    shard_ids: list[tuple[str, int]] = []
    for cell in sorted(cell_chunks.keys()):
        for i in range(len(cell_chunks[cell])):
            shard_ids.append((cell, i))
    n_total_shards = len(shard_ids)

    neg_sorted = sorted(decoys_neg, key=lambda r: (r["cell"], r["row_key"], r["arm"]))
    random.Random(seed + 1).shuffle(neg_sorted)
    neg_chunks = _round_robin_chunks(neg_sorted, n_total_shards) if n_total_shards else []

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["cell"], r["row_key"], r["arm"]))
    random.Random(seed + 2).shuffle(pos_sorted)
    pos_chunks = _round_robin_chunks(pos_sorted, n_total_shards) if n_total_shards else []

    shards = []
    for idx, (cell, chunk_i) in enumerate(shard_ids):
        core_chunk = cell_chunks[cell][chunk_i]
        combined = core_chunk + neg_chunks[idx] + pos_chunks[idx]
        random.Random(seed + 1000 + idx).shuffle(combined)
        blinded_pool = []
        id_map = []
        for item in combined:
            opaque_id = salted_opaque_id(salt, item["cell"], item["row_key"], item["arm"])
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "cell": item["cell"], "row_key": item["row_key"], "arm": item["arm"],
                "hs_index": item.get("hs_index"), "dose_multiplier": item.get("dose_multiplier"),
                "role": item.get("role"), "is_decoy": "decoy_type" in item, "decoy_type": item.get("decoy_type"),
            })
        shards.append({
            "shard_id": f"{cell}_shard_{chunk_i:02d}",
            "cell": cell,
            "blinded_pool": blinded_pool,
            "id_map": id_map,
            "n_core": len(core_chunk),
            "n_decoy_clear_negative": len(neg_chunks[idx]),
            "n_decoy_clear_positive": len(pos_chunks[idx]),
        })
    return shards


def build_regrade_shard(original_id_map: list[dict[str, Any]], salt: str, regrade_index: int, seed: int) -> dict[str, Any]:
    """Rebuilds a VOIDED shard's SAME underlying (cell, row_key, arm) items
    (core + both decoy types, unchanged content and unchanged composition)
    under FRESH opaque ids (regrade_index folded into the salt payload, so
    no id from the failed pass can be recognized) and a fresh shuffle order.
    Does not read or reveal any grade from the failed attempt. Per
    gates.yaml `on_failure: void_shard_before_unblinding_regrade_once`."""
    items = list(original_id_map)  # id_map entries carry cell/row_key/arm/role/decoy_type but NOT text; caller re-joins text via the original row source before calling this in a real regrade.
    random.Random(seed + 5000 + regrade_index).shuffle(items)
    id_map = []
    for item in items:
        opaque_id = salted_opaque_id(salt, item["cell"], item["row_key"], item["arm"], regrade_index=regrade_index)
        id_map.append({**item, "opaque_id": opaque_id})
    return {"shard_id": f"{original_id_map[0]['cell']}_regrade_{regrade_index:02d}" if items else f"regrade_{regrade_index:02d}", "id_map": id_map}


def pick_n_shards(core_size: int, target_shard_size: int = DEFAULT_TARGET_SHARD_SIZE) -> int:
    if core_size <= 0:
        return 1
    return max(1, round(core_size / target_shard_size))


def pick_n_shards_by_cell(core: list[dict[str, Any]], target_shard_size: int = DEFAULT_TARGET_SHARD_SIZE) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for r in core:
        sizes[r["cell"]] = sizes.get(r["cell"], 0) + 1
    return {cell: pick_n_shards(n, target_shard_size) for cell, n in sizes.items()}


def cap_total_shards_by_cell(n_shards_by_cell: dict[str, int], max_total_shards: int) -> dict[str, int]:
    """Enforces "every shard carries its own decoys of both types": the
    total shard count across all cells can never exceed the number of
    available decoys of the SCARCER type, or round-robin distribution would
    leave some shards with zero of that type. Reduces shard counts from the
    cell with the most shards first (ties broken by cell name, deterministic),
    never below 1 shard for a cell that has any core rows at all."""
    n_shards_by_cell = dict(n_shards_by_cell)
    while sum(n_shards_by_cell.values()) > max_total_shards:
        candidates = [c for c in n_shards_by_cell if n_shards_by_cell[c] > 1]
        if not candidates:
            break  # every cell already down to 1 shard; cannot reduce further
        c = max(candidates, key=lambda c: (n_shards_by_cell[c], c))
        n_shards_by_cell[c] -= 1
    return n_shards_by_cell


def cmd_build(args: argparse.Namespace) -> int:
    import detector_v2

    cfg = detector_v2.load_patterns()
    cell_rows = load_all_cell_rows()
    core, neg_cand, pos_cand = build_core_and_decoy_candidates(cell_rows, cfg)

    salt = args.salt or secrets.token_hex(32)
    rng = random.Random(args.seed)
    remaining_core, decoys_neg, decoys_pos = carve_decoys(core, neg_cand, pos_cand, rng)

    n_shards_by_cell = pick_n_shards_by_cell(remaining_core, args.target_shard_size)
    max_total_shards = max(1, min(len(decoys_neg), len(decoys_pos)))
    n_shards_by_cell = cap_total_shards_by_cell(n_shards_by_cell, max_total_shards)
    shards = build_shards(remaining_core, decoys_neg, decoys_pos, n_shards_by_cell, args.seed, salt)
    n_shards = len(shards)

    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    shard_manifest_entries = []
    for shard in shards:
        pool_path = SHARDS_DIR / f"{shard['shard_id']}.jsonl"
        map_path = SHARDS_DIR / f"{shard['shard_id']}_id_map.jsonl"
        write_jsonl(pool_path, shard["blinded_pool"])
        write_jsonl(map_path, shard["id_map"])
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
        "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards,
        "n_core_total": len(remaining_core),
        "n_decoy_clear_negative_total": len(decoys_neg),
        "n_decoy_clear_positive_total": len(decoys_pos),
        "shards": shard_manifest_entries,
    }
    write_json(COMMITTED / "adjudication_pool_manifest.json", manifest)

    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_manifest_entries]
    print(json.dumps(summary, indent=2), flush=True)
    print(
        f"\n[build_adjudication_pool] wrote {n_shards} shard(s) under {SHARDS_DIR} (gitignored). "
        f"Pool manifest committed to {COMMITTED / 'adjudication_pool_manifest.json'}. "
        f"NO grading has occurred and NO id map has been unblinded by this script.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20260714)
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE, help="per-cell shard count is round(cell_core_size / this); each cell shards independently")
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
