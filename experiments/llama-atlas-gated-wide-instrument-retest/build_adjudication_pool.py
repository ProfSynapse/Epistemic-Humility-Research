#!/usr/bin/env python3
"""Blinded adjudication pool builder for llama-atlas-gated-wide-instrument-retest.

Adapted from abstention-wide-instrument-calibration/build_adjudication_pool.py
(read in full before writing this; mechanics ported verbatim: salted opaque
ids, seeded shuffle, decoys carved out of core so no (arm, row_key, hs_index,
dose_multiplier) quadruple double-counts, sharding so every shard carries
both decoy types). Simplified to this cell's SINGLE family/cell (no
multi-cell loop): the core pool is every detector_v2-NEGATIVE row from every
arm/rung this harness generated --

  gated             every (layer, dose) rung, both tracked roles
  random_direction  the two registered rungs (hs20 dose12, hs20 dose16),
                     confab role only (cell.yaml arms[2])
  baseline          the reused undosed generations, both tracked roles

restricted to the two tracked populations (confab, known_correct_answered --
unknown_refused is fit_only and out of scope, same LB exclusion rationale as
the calibration cell's sources.py docstring).

DECOYS:
  clear_negative  known_correct_answered rows (any arm/rung) that are
                  well_formed_correct AND detector-v2-non-refused (carved
                  out of core -- RR2/calibration rationale: they already
                  satisfy core's own membership criterion).
  clear_positive  random_direction-arm rows where detector_v2 DOES mark
                  refused (disjoint from core by construction). THE LESSON
                  (AMENDMENT.md decoy_lesson, calibration cell's QL void on
                  decoy-draw variance): target MORE than 14 clear_positive
                  decoys PER SHARD, not the calibration cell's fixed 14-draw
                  fraction -- clear_positive is the scarce resource here
                  (bounded by the 2-rung random_direction population), so
                  this module sizes shard COUNT off clear_positive
                  availability first (via `cap_total_shards_by_cell`,
                  reused) rather than off core size, and reports the
                  resulting per-shard decoy counts plainly so a shortfall is
                  visible rather than silently accepted.

OUTPUTS (identical shape to the calibration cell):
  analysis/shards/shard_<NN>.jsonl            gitignored; [{opaque_id, text}]
  analysis/shards/shard_<NN>_id_map.jsonl     gitignored; full mapping
  analysis-committed/adjudication_pool_manifest.json   COMMITTED; ID-only,
      no text, no row_key, no arm/role, per this experiment's containment
      rule (population.containment in cell.yaml).

Per the harness-build assignment: this script BUILDS the pool and STOPS. It
does not grade anything; the lead orchestrates the CG1-gated blinded grading
lane.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path
from typing import Any

import detector_v2
import dose_ladder as dl

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"

TRACKED_ROLES = ("confab", "known_correct_answered")
CLEAR_NEGATIVE_FRACTION_OF_CORE = 0.075  # half of the calibration cell's 0.15 DECOY_FRACTION (the other half is clear_positive there; here clear_positive is sized separately, see module docstring)
MIN_CLEAR_POSITIVE_PER_SHARD_TARGET = 20  # > calibration's 14-decoy draw that voided its QL cell (AMENDMENT.md decoy_lesson)
DEFAULT_TARGET_SHARD_SIZE = 700


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Row discovery: every RunLog this harness wrote, plus the baseline arm.
# ---------------------------------------------------------------------------

def discover_gated_and_random_runlogs(family: str) -> list[dict[str, Any]]:
    """Parses `hs{layer}__{arm}__dose{mult}.jsonl` filenames under
    analysis/<family>/runlog/ -- the exact tag scheme dose_ladder.py's
    `run_arm` writes -- and returns [{path, layer, arm, dose_mult}]."""
    runlog_dir = ANALYSIS / family / "runlog"
    out = []
    for p in sorted(runlog_dir.glob("hs*__*__dose*.jsonl")):
        stem = p.stem  # hs20__gated__dose12
        parts = stem.split("__")
        if len(parts) != 3:
            continue
        layer = int(parts[0][2:])
        arm = parts[1]
        dose_mult = int(parts[2][4:])
        out.append({"path": p, "layer": layer, "arm": arm, "dose_mult": dose_mult})
    return out


def normalize_runlog_row(raw: dict[str, Any], *, arm: str, layer: int, dose_mult: int) -> dict[str, Any]:
    return {
        "arm": arm, "hs_index": layer, "dose_multiplier": dose_mult,
        "row_key": raw["row_key"], "role": raw.get("role"),
        "text": raw.get("answer_text", ""),
        "well_formed_correct": bool(raw.get("well_formed_correct", False)),
        "refused_v2": bool(raw.get("refused_v2", False)),
    }


def load_core_and_decoy_candidates(family: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Returns (core, clear_negative_candidates, clear_positive_candidates,
    coverage). `core` = every row (any arm/rung, tracked roles) with
    refused_v2 False."""
    cfg = detector_v2.load_patterns()
    core: list[dict[str, Any]] = []
    clear_positive_candidates: list[dict[str, Any]] = []
    counts = {"gated": 0, "random_direction": 0, "baseline": 0}

    for entry in discover_gated_and_random_runlogs(family):
        for raw in load_jsonl(entry["path"]):
            if raw.get("role") not in TRACKED_ROLES:
                continue
            row = normalize_runlog_row(raw, arm=entry["arm"], layer=entry["layer"], dose_mult=entry["dose_mult"])
            counts[entry["arm"]] = counts.get(entry["arm"], 0) + 1
            if row["refused_v2"]:
                if entry["arm"] == "random_direction":
                    clear_positive_candidates.append(row)
                continue
            core.append(row)

    # `baseline_graded_private.jsonl` carries no FIT-population role field of its
    # own (only a pre-fit `role_candidate` in {"answerable","unanswerable"}, a
    # different taxonomy) -- `dl.load_baseline_wide_by_key`'s `role` key is
    # therefore always None by construction (dose_ladder.py never reads it back:
    # its own baseline lookups match by row_key against already role-filtered FIT
    # row lists, so the gap is silent there). This module needs the real role, so
    # it joins against `joined_rows_private.jsonl` (materialize_rows.py's
    # row_key -> role map) by row_key instead.
    pdir = ANALYSIS / family
    role_by_key = {r["row_key"]: r["role"] for r in load_jsonl(pdir / "joined_rows_private.jsonl")}
    baseline_path = HERE / "analysis" / "staged_inputs" / family / "baseline_graded_private.jsonl"
    baseline_wide = dl.load_baseline_wide_by_key(baseline_path)
    for rk, r in baseline_wide.items():
        role = role_by_key.get(rk)
        if role not in TRACKED_ROLES:
            continue
        row = {
            "arm": "baseline", "hs_index": None, "dose_multiplier": None,
            "row_key": rk, "role": role, "text": r.get("answer_text", ""),
            "well_formed_correct": bool(r.get("well_formed_correct", False)),
            "refused_v2": bool(r.get("refused_v2", False)),
        }
        counts["baseline"] += 1
        if row["refused_v2"]:
            continue  # baseline has no random_direction pairing; not a clear_positive source
        core.append(row)

    clear_negative_candidates = [r for r in core if r["role"] == "known_correct_answered" and r["well_formed_correct"]]
    coverage = {"n_rows_by_arm": counts, "n_core": len(core), "n_clear_positive_candidates": len(clear_positive_candidates), "n_clear_negative_candidates": len(clear_negative_candidates)}
    return core, clear_negative_candidates, clear_positive_candidates, coverage


# ---------------------------------------------------------------------------
# Decoy carving, sharding, opaque ids -- ported verbatim from the
# calibration cell's build_adjudication_pool.py.
# ---------------------------------------------------------------------------

def carve_decoys(core: list[dict[str, Any]], clear_negative_candidates: list[dict[str, Any]],
                  clear_positive_candidates: list[dict[str, Any]], rng: random.Random,
                  n_shards_target: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    n_neg = max(1, round(len(core) * CLEAR_NEGATIVE_FRACTION_OF_CORE)) if core else 0
    n_pos_wanted = MIN_CLEAR_POSITIVE_PER_SHARD_TARGET * max(1, n_shards_target)

    neg_pool = clear_negative_candidates[:]
    rng.shuffle(neg_pool)
    chosen_neg = neg_pool[:n_neg]
    chosen_neg_keys = {(r["row_key"], r["arm"], r["hs_index"], r["dose_multiplier"]) for r in chosen_neg}
    remaining_core = [r for r in core if (r["row_key"], r["arm"], r["hs_index"], r["dose_multiplier"]) not in chosen_neg_keys]
    decoys_neg = [{**r, "decoy_type": "clear_negative"} for r in chosen_neg]

    pos_pool = clear_positive_candidates[:]
    rng.shuffle(pos_pool)
    n_pos = min(len(pos_pool), n_pos_wanted)
    decoys_pos = [{**r, "decoy_type": "clear_positive"} for r in pos_pool[:n_pos]]

    return remaining_core, decoys_neg, decoys_pos


def salted_opaque_id(salt: str, row_key: str, arm: str, hs_index: Any, dose_multiplier: Any, regrade_index: int = 0) -> str:
    payload = f"{salt}:{row_key}:{arm}:{hs_index}:{dose_multiplier}:{regrade_index}"
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


def pick_n_shards(core_size: int, target_shard_size: int) -> int:
    if core_size <= 0:
        return 1
    return max(1, round(core_size / target_shard_size))


def cap_shards_by_decoy_availability(n_shards: int, n_decoy_neg: int, n_decoy_pos: int, min_per_shard: int) -> int:
    """Every shard must carry >= min_per_shard of the SCARCER decoy type
    (default: MIN_CLEAR_POSITIVE_PER_SHARD_TARGET), or round-robin
    distribution leaves some shards short. Reduces shard count rather than
    decoy target."""
    max_by_scarce = max(1, min(n_decoy_neg, n_decoy_pos) // max(1, min_per_shard))
    return max(1, min(n_shards, max_by_scarce))


def build_shards(core: list[dict[str, Any]], decoys_neg: list[dict[str, Any]], decoys_pos: list[dict[str, Any]],
                  n_shards: int, seed: int, salt: str) -> list[dict[str, Any]]:
    rows_sorted = sorted(core, key=lambda r: (r["row_key"], r["arm"], str(r["hs_index"]), str(r["dose_multiplier"])))
    random.Random(f"{seed}:core").shuffle(rows_sorted)
    core_chunks = _round_robin_chunks(rows_sorted, n_shards)

    neg_sorted = sorted(decoys_neg, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(seed + 1).shuffle(neg_sorted)
    neg_chunks = _round_robin_chunks(neg_sorted, n_shards)

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(seed + 2).shuffle(pos_sorted)
    pos_chunks = _round_robin_chunks(pos_sorted, n_shards)

    shards = []
    for i in range(n_shards):
        combined = core_chunks[i] + neg_chunks[i] + pos_chunks[i]
        random.Random(seed + 1000 + i).shuffle(combined)
        blinded_pool = []
        id_map = []
        for item in combined:
            opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"], item.get("hs_index"), item.get("dose_multiplier"))
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"],
                "hs_index": item.get("hs_index"), "dose_multiplier": item.get("dose_multiplier"),
                "role": item.get("role"), "is_decoy": "decoy_type" in item, "decoy_type": item.get("decoy_type"),
            })
        shards.append({
            "shard_id": f"llama_wide_retest_shard_{i:02d}",
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunks[i]), "n_decoy_clear_negative": len(neg_chunks[i]), "n_decoy_clear_positive": len(pos_chunks[i]),
        })
    return shards


def cmd_build(args: argparse.Namespace) -> int:
    core, neg_cand, pos_cand, coverage = load_core_and_decoy_candidates(args.family)
    print(f"[build_adjudication_pool] coverage: {json.dumps(coverage)}", flush=True)

    n_shards_target = pick_n_shards(len(core), args.target_shard_size)

    salt = args.salt or secrets.token_hex(32)
    rng = random.Random(args.seed)
    remaining_core, decoys_neg, decoys_pos = carve_decoys(core, neg_cand, pos_cand, rng, n_shards_target)

    n_shards = cap_shards_by_decoy_availability(n_shards_target, len(decoys_neg), len(decoys_pos), args.min_clear_positive_per_shard)
    shards = build_shards(remaining_core, decoys_neg, decoys_pos, n_shards, args.seed, salt)

    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    shard_manifest_entries = []
    for shard in shards:
        pool_path = SHARDS_DIR / f"{shard['shard_id']}.jsonl"
        map_path = SHARDS_DIR / f"{shard['shard_id']}_id_map.jsonl"
        write_jsonl(pool_path, shard["blinded_pool"])
        write_jsonl(map_path, shard["id_map"])
        pool_sha = hashlib.sha256(pool_path.read_bytes()).hexdigest()
        shard_manifest_entries.append({
            "shard_id": shard["shard_id"], "pool_sha256": pool_sha, "row_count": len(shard["blinded_pool"]),
            "n_core": shard["n_core"], "n_decoy_clear_negative": shard["n_decoy_clear_negative"],
            "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "cell": "llama_wide_retest", "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards, "n_core_total": len(remaining_core),
        "n_decoy_clear_negative_total": len(decoys_neg), "n_decoy_clear_positive_total": len(decoys_pos),
        "min_clear_positive_per_shard_target": args.min_clear_positive_per_shard,
        "coverage": coverage,
        "shards": shard_manifest_entries,
    }
    write_json(COMMITTED / "adjudication_pool_manifest.json", manifest)

    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_manifest_entries]
    print(json.dumps(summary, indent=2, default=str), flush=True)
    print(
        f"\n[build_adjudication_pool] wrote {n_shards} shard(s) under {SHARDS_DIR} (gitignored). "
        f"Pool manifest committed to {COMMITTED / 'adjudication_pool_manifest.json'}. "
        f"NO grading has occurred and NO id map has been unblinded by this script.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--family", default="llama", choices=("llama",))
    ap.add_argument("--seed", type=int, default=20260719)
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.add_argument("--min-clear-positive-per-shard", type=int, default=MIN_CLEAR_POSITIVE_PER_SHARD_TARGET)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
