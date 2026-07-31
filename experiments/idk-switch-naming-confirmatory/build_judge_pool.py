#!/usr/bin/env python3
"""Blinded judge-pool builder for idk-switch-naming-confirmatory.

Thin port of `form-judge-axis-g-rescore/build_judge_pool.py` (source sha256
fdcdb6f8675382ea554f1496d4ceed7e1dd681d0a013c14751d78fb92c1d9f73, matching
that file's own pin; read in full before writing this), restricted per the
harness-build assignment to what THIS cell's AMENDMENT.md actually
registers:

  - ONLY full-pool mode. AMENDMENT.md "Instruments": "construct validation
    carries over from form-judge (G1 0.035 on this same text distribution)
    and is disclosed, not re-earned" -- there is no fresh judge-vs-adjudicator
    calibration slice here (form-judge already earned that). This module has
    no `--mode calibration` at all.
  - Clear-positive decoys ONLY, drawn from and embedded INSIDE the same
    full-pool shards as the real core rows (not a separate calibration pool):
    AMENDMENT.md "Instruments": "Judge-lane in-run validity is gated by
    clear-positive decoys per the standing protocol (floors at sign, sized to
    counted candidates from the FRESH generations' own F4 screen positives)."
    No clear-negative lane (per the harness-build instruction, matching
    form-judge's own governed deviation dropping the text-less
    clear-negative source -- see form-judge NOTEBOOK.md 2026-07-30).
  - No spent-slice exclusion: this cell has never been graded before (no
    prior calibration run of its own to have partially unblinded), so
    form-judge's D-1 spent-pair mechanism does not apply here.

Salted opaque ids, seeded shuffle, sharding, pool manifest committed BEFORE
any grading, no question/answer text under `analysis-committed/` -- same
discipline as form-judge and the naming battery before it.

Per the harness-build assignment: this script BUILDS the pool and STOPS. It
does not grade anything, and `--count-only` mode builds nothing at all -- it
only counts and reports feasibility numbers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path
from typing import Any

import screen_lib

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
SHARDS_DIR = ANALYSIS / "shards"

DEFAULT_RUNLOG_DIR = ANALYSIS / "runlog"
DEFAULT_TARGET_SHARD_SIZE = 55   # matches form-judge's full-pool convention; not a registered gate number

# Defaults mirror cell.yaml `judge_lane` (n_decoys_clear_positive: 25,
# pool_seed: 20260803, proposed 2026-07-31, binding at sign). The lead passes
# the registered values explicitly at run time; these defaults exist so the
# script is runnable pre-sign (count-only / smoke). The earlier placeholder
# seed 20260731 was replaced by the lead: that value is the form-judge cell's
# VOIDED attempt-1 pool seed and must not be reused even as a default.
PLACEHOLDER_N_DECOYS = 25
PLACEHOLDER_SEED = 20260803


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")


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
# Candidate population assembly
# ---------------------------------------------------------------------------

def build_candidate_populations(runlog_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], dict[str, Any]]:
    """Returns (core_by_arm, clear_positive_candidates, report).

    `core_by_arm[arm]`: screened-in rows for that sub-arm (the real payload).
    `clear_positive_candidates`: F4 screen-positive rows across all 4 arms
        (this run's own, fresh -- AMENDMENT.md "the FRESH generations' own F4
        screen positives").
    `report`: feasibility counts, ID-free.
    """
    screened, coverage = screen_lib.load_and_screen(runlog_dir)

    core_by_arm: dict[str, list[dict[str, Any]]] = {}
    clear_positive_candidates: list[dict[str, Any]] = []
    per_arm_core_counts: dict[str, int] = {}
    per_arm_f4_counts: dict[str, int] = {}

    for arm in screen_lib.ALL_ARM_KEYS:
        buckets = screened[arm]
        core_rows = list(buckets[screen_lib.SCREENED_IN])
        core_by_arm[arm] = core_rows
        per_arm_core_counts[arm] = len(core_rows)

        f4_rows = list(buckets[screen_lib.F4_EXPLICIT_IDK])
        clear_positive_candidates.extend(f4_rows)
        per_arm_f4_counts[arm] = len(f4_rows)

    report = {
        "coverage": coverage,
        "per_arm_core_candidates": per_arm_core_counts,
        "per_arm_f4_clear_positive_candidates": per_arm_f4_counts,
        "n_core_candidates_total": sum(per_arm_core_counts.values()),
        "n_clear_positive_candidates_total": len(clear_positive_candidates),
    }
    return core_by_arm, clear_positive_candidates, report


# ---------------------------------------------------------------------------
# Sampling, sharding, opaque ids (ported from form-judge's build_judge_pool.py)
# ---------------------------------------------------------------------------

def _round_robin_chunks(items: list[Any], n_shards: int) -> list[list[Any]]:
    chunks: list[list[Any]] = [[] for _ in range(n_shards)]
    base, rem = divmod(len(items), n_shards)
    idx = 0
    for i in range(n_shards):
        take = base + (1 if i < rem else 0)
        chunks[i] = items[idx:idx + take]
        idx += take
    return chunks


def salted_opaque_id(salt: str, row_key: str, arm: str, tag: str = "") -> str:
    payload = f"{salt}:{row_key}:{arm}:{tag}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def pick_n_shards(pool_size: int, target_shard_size: int) -> int:
    if pool_size <= 0:
        return 1
    return max(1, round(pool_size / target_shard_size))


def build_full_pool_shards_with_decoys(
    core_by_arm: dict[str, list[dict[str, Any]]],
    decoys_pos: list[dict[str, Any]],
    n_shards: int, seed: int, salt: str,
) -> list[dict[str, Any]]:
    """Builds shards over the real core payload (every screened-in row of
    all 4 arms) with clear-positive decoys embedded INSIDE the same shards
    (not a separate pool), per AMENDMENT.md "Judge-lane in-run validity is
    gated by clear-positive decoys". Decoy rows are tagged `decoy_type` so
    `apply_judge_grades.py` can strip them from the real N1/N2/N3 payload
    while still computing in-run decoy agreement from the SAME grading pass
    -- one dispatch per shard, not two."""
    all_core = [row for arm in screen_lib.ALL_ARM_KEYS for row in core_by_arm[arm]]
    core_sorted = sorted(all_core, key=lambda r: (r["arm"], r["row_key"]))
    random.Random(f"{seed}:core").shuffle(core_sorted)
    core_chunks = _round_robin_chunks(core_sorted, n_shards)

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["arm"], r["row_key"]))
    random.Random(f"{seed}:decoy_pos").shuffle(pos_sorted)
    pos_chunks = _round_robin_chunks(pos_sorted, n_shards)

    shards = []
    for i in range(n_shards):
        combined = (
            [{**r, "decoy_type": None} for r in core_chunks[i]]
            + [{**r, "decoy_type": "clear_positive"} for r in pos_chunks[i]]
        )
        random.Random(f"{seed}:shard:{i}").shuffle(combined)
        blinded_pool, id_map = [], []
        for item in combined:
            opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"], tag="fullpool")
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"],
                "is_decoy": item["decoy_type"] is not None, "decoy_type": item["decoy_type"],
            })
        shards.append({
            "shard_id": f"isnc_fullpool_shard_{i:02d}",
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunks[i]), "n_decoy_clear_positive": len(pos_chunks[i]),
        })
    return shards


def write_shards(shards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Fail-closed guard (ported from form-judge, added there after its
    # calibration attempt 1 was voided for silently empty decoy text): a
    # blinded pool row with empty/whitespace text means an upstream join or
    # source bug; grading empty bytes tests nothing. Refuse to write.
    for shard in shards:
        for row in shard["blinded_pool"]:
            if not str(row.get("text", "")).strip():
                raise SystemExit(
                    f"[build_judge_pool] FATAL: empty text in {shard['shard_id']} "
                    f"(opaque_id {row.get('opaque_id')}); refusing to write any shard."
                )
    SHARDS_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for shard in shards:
        pool_path = SHARDS_DIR / f"{shard['shard_id']}.jsonl"
        map_path = SHARDS_DIR / f"{shard['shard_id']}_id_map.jsonl"
        write_jsonl(pool_path, shard["blinded_pool"])
        write_jsonl(map_path, shard["id_map"])
        pool_sha = hashlib.sha256(pool_path.read_bytes()).hexdigest()
        entries.append({
            "shard_id": shard["shard_id"], "pool_sha256": pool_sha, "row_count": len(shard["blinded_pool"]),
            "n_core": shard["n_core"], "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })
    return entries


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> int:
    runlog_dir = Path(args.runlog_dir) if args.runlog_dir else DEFAULT_RUNLOG_DIR

    core_by_arm, decoys_pos, report = build_candidate_populations(runlog_dir)
    print(f"[build_judge_pool] feasibility report:\n{json.dumps(report, indent=2, default=str)}", flush=True)

    if report["n_clear_positive_candidates_total"] < args.n_decoys:
        print(
            f"[build_judge_pool] WARNING: only {report['n_clear_positive_candidates_total']} "
            f"clear_positive decoy candidates available (this run's own F4 screen "
            f"positives), below n_decoys={args.n_decoys}.",
            flush=True,
        )

    if args.count_only:
        summary = {"cell": "idk_switch_naming_confirmatory", "mode": "full-pool", "count_only": True, "feasibility": report}
        ANALYSIS.mkdir(parents=True, exist_ok=True)
        write_json(ANALYSIS / "build_judge_pool_feasibility.json", summary)
        print(json.dumps(summary, indent=2, default=str), flush=True)
        print("\n[build_judge_pool] count-only mode: no pool, no shards, no text written.", flush=True)
        return 0

    salt = args.salt or secrets.token_hex(32)
    rng = random.Random(args.seed)
    decoys_pos_final = list(decoys_pos)
    rng.shuffle(decoys_pos_final)
    decoys_pos_final = decoys_pos_final[: args.n_decoys]

    n_total_for_sizing = report["n_core_candidates_total"] + len(decoys_pos_final)
    n_shards = pick_n_shards(n_total_for_sizing, args.target_shard_size)
    shards = build_full_pool_shards_with_decoys(core_by_arm, decoys_pos_final, n_shards, args.seed, salt)
    shard_entries = write_shards(shards)

    manifest = {
        "cell": "idk_switch_naming_confirmatory", "mode": "full-pool", "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards, "n_core_total": report["n_core_candidates_total"],
        "n_decoy_clear_positive_total": len(decoys_pos_final),
        "n_decoys_target": args.n_decoys,
        "feasibility": report, "shards": shard_entries,
    }
    write_json(ANALYSIS / "full_pool_manifest.json", manifest)
    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_entries]
    print(json.dumps(summary, indent=2, default=str), flush=True)
    print(f"\n[build_judge_pool] wrote {n_shards} full-pool shard(s) under {SHARDS_DIR} (gitignored).", flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runlog-dir", default=None, help=f"default: {DEFAULT_RUNLOG_DIR}")
    ap.add_argument("--seed", type=int, default=PLACEHOLDER_SEED, help="PLACEHOLDER default; not a registered value")
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--n-decoys", type=int, default=PLACEHOLDER_N_DECOYS, help="PLACEHOLDER default; cell.yaml judge_lane.n_decoys_clear_positive is the registered value at sign")
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.add_argument("--count-only", action="store_true", help="report feasibility counts only; write no pool, no shards, no text")
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
