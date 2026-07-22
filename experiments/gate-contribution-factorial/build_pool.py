#!/usr/bin/env python3
"""Blinded, SHARDED grading-pool builder for gate-contribution-factorial
(cell.yaml `wide_instrument.adjudication`; gates.yaml `sc2_grading_integrity`).

Ported (logic) from `placebo-seed-distribution-census/build_pool.py`, read in
full before writing this. Cell = family (qwen35_4b, mistral7b_v03). Per
family, THIRTEEN source passes feed the pool: baseline, true_gate__c_hat,
permuted_gate__c_hat (each one pass, over the full population), plus
true_gate__random and permuted_gate__random (K=5 seeds each). Dedup key is
(cell, arm, row_key, seed) -- arm in {"baseline", "true_gate_c_hat",
"permuted_gate_c_hat", "true_gate_random", "permuted_gate_random"}; a row_key
can legitimately carry up to 5 distinct dosed texts per K-multiplied arm plus
one text per single-pass arm.

DECOYS:
  clear_negative  drawn from a HELD-BACK pool: committed-answer, detector-v2-
                  non-refused known-correct rows that never enter any scored
                  rate (successor fix (a)). STRUCTURAL FINDING (reported to
                  the lead, not resolved here): unlike census (which scores
                  only an S=300 confab subsample, leaving the ENTIRE known-
                  correct pool held back), this experiment's P1/P3 criteria
                  require the FULL known-correct pool scored in EVERY arm
                  (cell.yaml `subsample.known_correct_answered.all_arms:
                  full_pool`), so there is NO known-correct row this
                  experiment's own generation ever leaves unscored --
                  `heldback_decoys.py` will legitimately find ZERO
                  candidates from this family's own held-out pool. The lead
                  needs an alternate clear-negative source (e.g. a small
                  fresh FIT-split known-correct baseline pass) before a REAL
                  pool can be built; `load_heldback_candidates` raises
                  loudly rather than silently degrading, and the
                  pool-assembly LOGIC itself is fully exercised on synthetic
                  fixtures by `test_factorial_smoke.py` regardless.
  clear_positive  drawn from core's own refused_v2==True rows, pooled across
                  every non-baseline arm (broader availability than census's
                  single-arm source, since this experiment has many arms).

OUTPUTS:
  analysis/shards/<shard_id>.jsonl              gitignored; [{opaque_id, text}]
  analysis/shards/<shard_id>_id_map.jsonl        gitignored; full mapping
  analysis-committed/pool_manifest.json          COMMITTED; hashes/counts/
      opaque-ids only, no text, per SC0/containment.
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
sys.path.insert(0, str(HERE))
import config  # noqa: E402
import common  # noqa: E402

ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

DECOY_FRACTION = 0.15
DEFAULT_TARGET_SHARD_SIZE = 700
CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR = config.CG1_CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR

CELLS = config.FAMILIES

# arm -> list of run-log TAG templates this arm's rows are read from.
SINGLE_PASS_ARMS = ("baseline", "true_gate_c_hat", "permuted_gate_c_hat")
K_MULTIPLIED_ARMS = ("true_gate_random", "permuted_gate_random")


def _normalize(rows: list[dict[str, Any]], *, cell: str, arm: str, seed: Any = None) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        out.append({
            "cell": cell, "arm": arm, "row_key": r["row_key"], "role": r.get("role"),
            "source": r.get("source"), "seed": seed, "text": r.get("answer_text", ""),
            "refused_v2": bool(r.get("refused_v2", False)),
        })
    return out


def runlog_path(tag: str) -> Path:
    return ANALYSIS / "runlog" / f"{tag}.jsonl"


def load_family_rows(family: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    out += _normalize(common.load_jsonl(runlog_path(f"{family}__baseline_reused")), cell=family, arm="baseline")
    out += _normalize(common.load_jsonl(runlog_path(f"{family}__true_gate_c_hat_reused")), cell=family, arm="true_gate_c_hat")
    out += _normalize(common.load_jsonl(runlog_path(f"{family}__permuted_gate_c_hat_final")), cell=family, arm="permuted_gate_c_hat")
    for seed in common.accepted_random_seeds(family, committed_dir=COMMITTED, k_expected=config.K_SEEDS_PER_FAMILY):
        tg = common.load_jsonl(runlog_path(f"{family}__true_gate_random__seed{seed}_final"))
        pg = common.load_jsonl(runlog_path(f"{family}__permuted_gate_random__seed{seed}_final"))
        if not tg or not pg:
            raise SystemExit(f"[pool] {family} seed {seed}: accepted-seed runlog missing or empty "
                             f"(true_gate_random n={len(tg)}, permuted_gate_random n={len(pg)})")
        out += _normalize(tg, cell=family, arm="true_gate_random", seed=seed)
        out += _normalize(pg, cell=family, arm="permuted_gate_random", seed=seed)
    return out


def load_all_pool_source_rows() -> dict[str, list[dict[str, Any]]]:
    return {family: load_family_rows(family) for family in CELLS}


def load_heldback_candidates() -> list[dict[str, Any]]:
    """See module docstring: this experiment's own held-out known-correct
    pool is fully scored in every arm, so there is structurally no held-back
    subset from THIS family's own generation. Raises loudly rather than
    silently falling back to an unsafe decoy source."""
    out: list[dict[str, Any]] = []
    missing = []
    for family in CELLS:
        path = runlog_path(f"heldback__{family}")
        if not path.is_file():
            missing.append(str(path))
            continue
        out += _normalize(common.load_jsonl(path), cell="heldback", arm=f"heldback_{family}")
    if missing:
        raise SystemExit(
            f"load_heldback_candidates: missing held-back runlog(s) {missing}. "
            f"This experiment's own held-out known-correct pool is scored in "
            f"EVERY arm (cell.yaml subsample.known_correct_answered.all_arms: "
            f"full_pool), so heldback_decoys.py finds ZERO qualifying candidates "
            f"by construction -- an alternate clear-negative decoy source is a "
            f"build-time finding for the lead, not something this harness "
            f"resolves. Pool-assembly logic itself is fully tested against "
            f"synthetic fixtures in test_factorial_smoke.py."
        )
    if not out:
        raise SystemExit(
            "load_heldback_candidates: heldback__<family> runlog(s) exist but "
            "are EMPTY. See module docstring: this is expected given this "
            "experiment's full-known-pool design; a real pool build needs an "
            "alternate clear-negative decoy source before proceeding."
        )
    return out


def item_key(r: dict[str, Any]) -> tuple:
    return (r["cell"], r["arm"], r["row_key"], r.get("seed"))


def build_core_and_positive_candidates(cell_rows: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
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
                if r["arm"] != "baseline":
                    positive.append(r)
                continue
            core.append(r)
    return core, positive


def carve_decoys(core: list[dict[str, Any]], heldback_candidates: list[dict[str, Any]],
                  positive_candidates: list[dict[str, Any]], rng: random.Random) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    n_each = max(1, round(len(core) * DECOY_FRACTION / 2)) if core else 0

    neg_pool = [r for r in heldback_candidates if not r["refused_v2"]][:]
    rng.shuffle(neg_pool)
    decoys_neg = [{**r, "decoy_type": "clear_negative"} for r in neg_pool[:n_each]]

    pos_pool = positive_candidates[:]
    rng.shuffle(pos_pool)
    decoys_pos = [{**r, "decoy_type": "clear_positive"} for r in pos_pool[:n_each]]

    return decoys_neg, decoys_pos


def salted_opaque_id(salt: str, cell: str, arm: str, row_key: str, seed: Any, regrade_index: int = 0) -> str:
    payload = f"{salt}:{cell}:{arm}:{row_key}:{seed}:{regrade_index}"
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
    max_by_neg = max(1, n_decoys_neg)
    max_by_pos = max(1, n_decoys_pos // CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR)
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
        rows_sorted = sorted(rows, key=lambda r: (r["row_key"], r["arm"], str(r.get("seed"))))
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

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["cell"], r["row_key"], r["arm"], str(r.get("seed"))))
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
            opaque_id = salted_opaque_id(salt, item["cell"], item["arm"], item["row_key"], item.get("seed"))
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "cell": item["cell"], "arm": item["arm"], "row_key": item["row_key"],
                "role": item.get("role"), "source": item.get("source"), "seed": item.get("seed"),
                "is_decoy": "decoy_type" in item, "decoy_type": item.get("decoy_type"),
            })
        shards.append({
            "shard_id": f"{cell}_shard_{chunk_i:02d}", "cell": cell,
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunk), "n_decoy_clear_negative": len(neg_chunks[idx]), "n_decoy_clear_positive": len(pos_chunks[idx]),
        })
    return shards


def build_regrade_shard(original_id_map: list[dict[str, Any]], salt: str, regrade_index: int, seed: int) -> dict[str, Any]:
    items = list(original_id_map)
    random.Random(seed + 5000 + regrade_index).shuffle(items)
    id_map = []
    for item in items:
        opaque_id = salted_opaque_id(salt, item["cell"], item["arm"], item["row_key"], item.get("seed"), regrade_index=regrade_index)
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
        common.write_jsonl(pool_path, shard["blinded_pool"])
        common.write_jsonl(map_path, shard["id_map"])
        pool_sha = common.sha256_of_file(pool_path)
        shard_manifest_entries.append({
            "shard_id": shard["shard_id"], "cell": shard["cell"], "pool_sha256": pool_sha,
            "row_count": len(shard["blinded_pool"]), "n_core": shard["n_core"],
            "n_decoy_clear_negative": shard["n_decoy_clear_negative"], "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "seed": args.seed, "id_salt_sha256": common.sha256_of_bytes(salt.encode("utf-8")),
        "n_shards": n_shards, "n_core_total": len(core),
        "n_decoy_clear_negative_total": len(decoys_neg), "n_decoy_clear_positive_total": len(decoys_pos),
        "clear_positive_per_shard_floor": CLEAR_POSITIVE_DECOYS_PER_SHARD_FLOOR,
        "shards": shard_manifest_entries,
    }
    common.write_json(COMMITTED / "pool_manifest.json", manifest)

    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_manifest_entries]
    print(summary, flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=config.SUBSAMPLE_PERMUTATION_SEED)
    ap.add_argument("--salt", default=None)
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
