#!/usr/bin/env python3
"""Blinded, SHARDED adjudication pool builder for
rr3-corrected-placebo-replication.

Adapted from `abstention-wide-instrument-calibration/build_adjudication_pool.py`
(read in full before writing this), which itself adapted RR2's single-arm
builder for a multi-cell, sharded pool. This module carries forward the
calibration's mechanics (salted opaque ids, seeded shuffle, cell-scoped
sharding so a second CG1 failure unambiguously voids "the cell") and
implements RR3's TWO REGISTERED SUCCESSOR FIXES from AMENDMENT.md
"Successor instrument fix (a)/(b)":

  (a) HELD-BACK clear-negative decoys. The calibration carved clear_negative
      decoys OUT of the scored known-correct population itself, cannibalizing
      cost coverage. RR3 draws clear_negative decoys ONLY from the held-back
      pool `heldout_scorer.py cmd_heldback` writes (an undosed baseline pass
      over each family's FIT-split known-correct rows -- rows that are NEVER
      part of any scored held-out arm). These decoys are candidates from a
      pool disjoint from every scored population by CONSTRUCTION (they are
      never `held_out` split rows at all), not merely by post-hoc removal;
      RG0 asserts this disjointness (`test_rr3_smoke.py`).
  (b) POOLED clear-positive floor + per-shard count floor >= 25. Every
      shard's clear_positive decoy draw is >= `gates_lib.
      CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR` (25), and
      `apply_adjudication.py` additionally evaluates a POOLED clear-positive
      floor across every shard (gates_lib.cg1_pooled_clear_positive), so a
      single hard decoy subset in one shard cannot void a cell on decoy-draw
      variance alone.

CORE POOL: every detector-v2-negative row from every registered pool source
(cell.yaml `adjudication.pool_source_arms`), across THREE build-time "cells"
(a sharding-scope concept this module introduces, mirroring the
calibration's cell-scoped sharding so `on_second_failure:
void_cell_report_straight` has an unambiguous unit to void):

  core_mistral    core baseline + gated (fired rows only) + random_direction
                  (fired rows only, ALL K seeds) + dose_knowns_ungated
                  (cell.yaml core_cell.arms)
  rider_mistral   rider_mistral_placebo_ladder's random_direction dose-ladder
                  rows (confab subsample + known_correct_answered full, every
                  dose rung). The rider's OWN baseline is `reuse_core_baseline`
                  (cell.yaml): its text is byte-identical to core_mistral's
                  baseline rows already in the pool, so it is NOT re-added
                  (an RR2-style "no duplicate-of-baseline entry" rule).
  rider_llama     rider_llama_placebo_ladder's baseline (full held-out) +
                  random_direction dose-ladder rows (confab subsample + known
                  full, every dose rung).

Deduplicated on the FULL (cell, arm, row_key, seed, dose_multiplier) tuple --
not on (cell, row_key, arm) alone -- because the SAME row_key legitimately
carries MULTIPLE distinct generation texts in this experiment: the core
random_direction arm writes K >= 3 different texts per fired row_key (one per
seed), and each rider dose ladder writes one distinct text per row_key PER
DOSE rung. This generalizes RR2's own (row_key, arm) dedup key (which was
sufficient there because RR2 had no K-seed or dose-ladder arms) and mirrors
the calibration's own fix for the identical collision it hit in its QL dose
ladder (calibration `build_adjudication_pool.py` module docstring,
`salted_opaque_id`).

DECOYS:
  clear_negative  drawn from the HELD-BACK pool (fix (a) above), NEVER from
                  core. well_formed_correct AND detector-v2-non-refused rows
                  from `heldout_scorer.py cmd_heldback`'s run logs (both
                  families pooled as one candidate set; the calibration check
                  is on the ADJUDICATOR's behavior, not a per-family claim).
  clear_positive  drawn from core's own refused_v2==True rows in any
                  random_direction arm (core K-seed or either rider ladder)
                  -- disjoint from core by construction (core requires
                  refused_v2==False), identical rationale to RR2/calibration.

OUTPUTS:
  analysis/shards/shard_<ID>.jsonl              gitignored; [{opaque_id, text}]
  analysis/shards/shard_<ID>_id_map.jsonl        gitignored; full mapping
      {opaque_id, cell, arm, row_key, role, source, seed, dose_multiplier,
       hs_index, is_decoy, decoy_type}
  analysis-committed/adjudication_pool_manifest.json   COMMITTED; ONLY
      {seed, id_salt_sha256, n_shards, shards: [{shard_id, cell, sha256,
       row_count, n_core, n_decoy_clear_negative, n_decoy_clear_positive,
       opaque_ids (sorted)}]} -- no text, no row_key, no arm/role/source, per
      this experiment's containment rule.
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

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import gates_lib  # noqa: E402
import heldout_scorer as hs  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

DECOY_FRACTION = 0.15  # of the core pool size, split evenly between the two decoy types (RR2/calibration convention, reapplied)
DEFAULT_TARGET_SHARD_SIZE = 700  # calibration's own build-time interpretation of "sharding allowed"; reused here for consistency

CELLS = ("core_mistral", "rider_mistral", "rider_llama")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _normalize(rows: list[dict[str, Any]], *, cell: str, arm: str, seed: Any = None, dose_multiplier: Any = None, hs_index: Any = None) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "cell": cell, "arm": arm, "row_key": r["row_key"], "role": r.get("role"),
            "source": r.get("source"), "seed": seed, "dose_multiplier": dose_multiplier,
            "hs_index": hs_index, "text": r.get("answer_text", ""),
            "well_formed_correct": bool(r.get("well_formed_correct")),
            "refused_v2": bool(r.get("refused_v2", False)),
        })
    return out


# ---------------------------------------------------------------------------
# Pool-source loading: every registered arm, normalized to one row shape.
# ---------------------------------------------------------------------------

def load_core_mistral_rows() -> list[dict[str, Any]]:
    layer = hs.FAMILY_TO_LAYER["mistral"]
    out: list[dict[str, Any]] = []
    out += _normalize(load_jsonl(hs.runlog_path("core__baseline")), cell="core_mistral", arm="baseline", hs_index=layer)
    out += _normalize(load_jsonl(hs.runlog_path("core__gated")), cell="core_mistral", arm="gated", hs_index=layer)
    cell = hs.load_cell_yaml()
    seeds = next(a["random_seeds"] for a in cell["core_cell"]["arms"] if a["name"] == "random_direction")
    for seed in seeds:
        out += _normalize(load_jsonl(hs.runlog_path(f"core__random_direction__seed{seed}")), cell="core_mistral", arm="random_direction", seed=seed, hs_index=layer)
    out += _normalize(load_jsonl(hs.runlog_path("core__dose_knowns_ungated")), cell="core_mistral", arm="dose_knowns_ungated", hs_index=layer)
    return out


def load_rider_rows(family: str) -> list[dict[str, Any]]:
    layer = hs.FAMILY_TO_LAYER[family]
    out: list[dict[str, Any]] = []
    if family == "llama":
        out += _normalize(load_jsonl(hs.runlog_path(f"rider_{family}__baseline")), cell=f"rider_{family}", arm="baseline", hs_index=layer)
    # mistral rider baseline is reuse_core_baseline: already present under cell="core_mistral", arm="baseline"; not re-added.
    for dose in hs.DOSE_LADDER:
        seed = hs.rider_direction_seed(family, dose)
        for population in ("confab", "known_correct_answered"):
            tag = f"rider_{family}__random_direction__dose{dose}__{population}"
            out += _normalize(load_jsonl(hs.runlog_path(tag)), cell=f"rider_{family}", arm="random_direction", seed=seed, dose_multiplier=dose, hs_index=layer)
    return out


def load_heldback_candidates() -> list[dict[str, Any]]:
    """Held-back clear-negative decoy candidates: undosed baseline rows over
    each family's FIT-split known-correct rows (never a scored held-out
    row). Pooled across both families -- the CG1 check is on the adjudicator,
    not a per-family claim."""
    out: list[dict[str, Any]] = []
    for family in ("mistral", "llama"):
        rows = load_jsonl(hs.runlog_path(f"heldback__{family}__known_fit_baseline"))
        out += _normalize(rows, cell="heldback", arm=f"heldback_{family}", hs_index=hs.FAMILY_TO_LAYER[family])
    return out


def load_all_pool_source_rows() -> dict[str, list[dict[str, Any]]]:
    return {
        "core_mistral": load_core_mistral_rows(),
        "rider_mistral": load_rider_rows("mistral"),
        "rider_llama": load_rider_rows("llama"),
    }


# ---------------------------------------------------------------------------
# Core pool assembly + decoy carving.
# ---------------------------------------------------------------------------

def item_key(r: dict[str, Any]) -> tuple:
    return (r["cell"], r["arm"], r["row_key"], r.get("seed"), r.get("dose_multiplier"))


def build_core_and_positive_candidates(cell_rows: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Returns (core, clear_positive_candidates), deduplicated on the full
    (cell, arm, row_key, seed, dose_multiplier) tuple. `core` = every row
    with refused_v2 False. `clear_positive_candidates` = refused_v2==True
    rows from any random_direction arm -- disjoint from core by construction."""
    core: list[dict[str, Any]] = []
    positive: list[dict[str, Any]] = []
    seen: set[tuple] = set()
    for rows in cell_rows.values():
        for r in rows:
            k = item_key(r)
            if k in seen:
                raise SystemExit(f"duplicate pool-source item key {k}; a generation pass was double-counted")
            seen.add(k)
            if r["refused_v2"]:
                if r["arm"] == "random_direction":
                    positive.append(r)
                continue
            core.append(r)
    return core, positive


def carve_decoys(core: list[dict[str, Any]], heldback_candidates: list[dict[str, Any]],
                  positive_candidates: list[dict[str, Any]], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """clear_negative: drawn from the HELD-BACK candidate pool (well_formed_correct
    AND refused_v2 False), never from core -- successor fix (a). No removal
    from core is needed (held-back rows were never in core: they carry
    cell="heldback", disjoint by construction from the three scored cells).
    clear_positive: drawn from `positive_candidates` (disjoint from core by
    construction, no removal needed), sized so every planned shard clears the
    per-shard floor (see `cmd_build`'s shard-count capping)."""
    n_each = max(1, round(len(core) * DECOY_FRACTION / 2)) if core else 0

    neg_pool = [r for r in heldback_candidates if r["well_formed_correct"] and not r["refused_v2"]]
    neg_pool = neg_pool[:]
    rng.shuffle(neg_pool)
    decoys_neg = [{**r, "decoy_type": "clear_negative"} for r in neg_pool[:n_each]]

    pos_pool = positive_candidates[:]
    rng.shuffle(pos_pool)
    decoys_pos = [{**r, "decoy_type": "clear_positive"} for r in pos_pool[:n_each]]

    return decoys_neg, decoys_pos


def salted_opaque_id(salt: str, cell: str, arm: str, row_key: str, seed: Any, dose_multiplier: Any, regrade_index: int = 0) -> str:
    """Extended payload (cell, arm, row_key, seed, dose_multiplier,
    regrade_index) so the opaque id is unique per SCORED GENERATION, not per
    source row -- the calibration's own fix for the identical collision
    (same row_key/arm at multiple (hs_index, dose) points; here also at
    multiple K seeds), generalized: this experiment folds seed AND
    dose_multiplier into the payload from the start rather than retrofitting
    it after a collision, per the lead's explicit build instruction."""
    payload = f"{salt}:{cell}:{arm}:{row_key}:{seed}:{dose_multiplier}:{regrade_index}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _round_robin_chunks(items: list[Any], n_shards: int) -> list[list[Any]]:
    chunks: list[list[Any]] = [[] for _ in range(n_shards)]
    base, rem = divmod(len(items), n_shards)
    idx = 0
    for i in range(n_shards):
        take = base + (1 if i < rem else 0)
        chunks[i] = items[idx:idx + take]
        idx += take
    return chunks


def pick_n_shards(core_size: int, target_shard_size: int = DEFAULT_TARGET_SHARD_SIZE) -> int:
    if core_size <= 0:
        return 1
    return max(1, round(core_size / target_shard_size))


def pick_n_shards_by_cell(core: list[dict[str, Any]], target_shard_size: int = DEFAULT_TARGET_SHARD_SIZE) -> dict[str, int]:
    sizes: dict[str, int] = {}
    for r in core:
        sizes[r["cell"]] = sizes.get(r["cell"], 0) + 1
    return {cell: pick_n_shards(n, target_shard_size) for cell, n in sizes.items()}


def cap_total_shards_by_cell(n_shards_by_cell: dict[str, int], n_decoys_neg: int, n_decoys_pos: int) -> dict[str, int]:
    """Enforces TWO floors simultaneously: every shard must carry at least
    one clear_negative decoy, AND every shard must clear the registered
    per-shard clear_positive count floor (gates_lib.
    CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR, 25) -- successor fix (b).
    Reduces shard counts from the cell with the most shards first (ties
    broken by cell name, deterministic), never below 1 shard for a cell that
    has any core rows at all."""
    max_by_neg = max(1, n_decoys_neg)
    max_by_pos = max(1, n_decoys_pos // gates_lib.CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR)
    max_total_shards = max(1, min(max_by_neg, max_by_pos))
    n_shards_by_cell = dict(n_shards_by_cell)
    while sum(n_shards_by_cell.values()) > max_total_shards:
        candidates = [c for c in n_shards_by_cell if n_shards_by_cell[c] > 1]
        if not candidates:
            break
        c = max(candidates, key=lambda c: (n_shards_by_cell[c], c))
        n_shards_by_cell[c] -= 1
    return n_shards_by_cell


def plan_cell_shards(core: list[dict[str, Any]], n_shards_by_cell: dict[str, int], seed: int) -> dict[str, list[list[dict[str, Any]]]]:
    by_cell: dict[str, list[dict[str, Any]]] = {}
    for r in core:
        by_cell.setdefault(r["cell"], []).append(r)
    out: dict[str, list[list[dict[str, Any]]]] = {}
    for cell, rows in by_cell.items():
        rows_sorted = sorted(rows, key=lambda r: (r["row_key"], r["arm"], str(r.get("seed")), str(r.get("dose_multiplier"))))
        random.Random(f"{seed}:{cell}").shuffle(rows_sorted)
        out[cell] = _round_robin_chunks(rows_sorted, n_shards_by_cell[cell])
    return out


def build_shards(core: list[dict[str, Any]], decoys_neg: list[dict[str, Any]], decoys_pos: list[dict[str, Any]],
                  n_shards_by_cell: dict[str, int], seed: int, salt: str) -> list[dict[str, Any]]:
    cell_chunks = plan_cell_shards(core, n_shards_by_cell, seed)

    shard_ids: list[tuple[str, int]] = []
    for cell in sorted(cell_chunks.keys()):
        for i in range(len(cell_chunks[cell])):
            shard_ids.append((cell, i))
    n_total_shards = len(shard_ids)

    neg_sorted = sorted(decoys_neg, key=lambda r: (r["cell"], r["row_key"], r["arm"]))
    random.Random(seed + 1).shuffle(neg_sorted)
    neg_chunks = _round_robin_chunks(neg_sorted, n_total_shards) if n_total_shards else []

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["cell"], r["row_key"], r["arm"], str(r.get("seed")), str(r.get("dose_multiplier"))))
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
            opaque_id = salted_opaque_id(salt, item["cell"], item["arm"], item["row_key"], item.get("seed"), item.get("dose_multiplier"))
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "cell": item["cell"], "arm": item["arm"], "row_key": item["row_key"],
                "role": item.get("role"), "source": item.get("source"), "seed": item.get("seed"),
                "dose_multiplier": item.get("dose_multiplier"), "hs_index": item.get("hs_index"),
                "is_decoy": "decoy_type" in item, "decoy_type": item.get("decoy_type"),
            })
        shards.append({
            "shard_id": f"{cell}_shard_{chunk_i:02d}", "cell": cell,
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunk), "n_decoy_clear_negative": len(neg_chunks[idx]), "n_decoy_clear_positive": len(pos_chunks[idx]),
        })
    return shards


def build_regrade_shard(original_id_map: list[dict[str, Any]], salt: str, regrade_index: int, seed: int) -> dict[str, Any]:
    """Rebuilds a VOIDED shard's SAME underlying items (core + both decoy
    types, unchanged composition) under FRESH opaque ids and a fresh
    shuffle, per gates.yaml `on_failure:
    void_shard_before_unblinding_regrade_once_with_fresh_agent`. Mirrors the
    calibration's `build_regrade_shard` exactly."""
    items = list(original_id_map)
    random.Random(seed + 5000 + regrade_index).shuffle(items)
    id_map = []
    for item in items:
        opaque_id = salted_opaque_id(salt, item["cell"], item["arm"], item["row_key"], item.get("seed"), item.get("dose_multiplier"), regrade_index=regrade_index)
        id_map.append({**item, "opaque_id": opaque_id})
    return {"shard_id": f"{original_id_map[0]['cell']}_regrade_{regrade_index:02d}" if items else f"regrade_{regrade_index:02d}", "id_map": id_map}


def cmd_build(args: argparse.Namespace) -> int:
    cell_rows = load_all_pool_source_rows()
    core, positive_candidates = build_core_and_positive_candidates(cell_rows)
    heldback = load_heldback_candidates()

    salt = args.salt or secrets.token_hex(32)
    rng = random.Random(args.seed)
    decoys_neg, decoys_pos = carve_decoys(core, heldback, positive_candidates, rng)

    n_shards_by_cell = pick_n_shards_by_cell(core, args.target_shard_size)
    n_shards_by_cell = cap_total_shards_by_cell(n_shards_by_cell, len(decoys_neg), len(decoys_pos))
    shards = build_shards(core, decoys_neg, decoys_pos, n_shards_by_cell, args.seed, salt)
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
            "shard_id": shard["shard_id"], "cell": shard["cell"], "pool_sha256": pool_sha,
            "row_count": len(shard["blinded_pool"]), "n_core": shard["n_core"],
            "n_decoy_clear_negative": shard["n_decoy_clear_negative"], "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "seed": args.seed, "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards, "n_core_total": len(core),
        "n_decoy_clear_negative_total": len(decoys_neg), "n_decoy_clear_positive_total": len(decoys_pos),
        "clear_positive_per_shard_floor": gates_lib.CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR,
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
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
