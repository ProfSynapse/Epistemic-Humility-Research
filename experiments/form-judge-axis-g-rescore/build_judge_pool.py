#!/usr/bin/env python3
"""Blinded-adjudication pool builder for form-judge-axis-g-rescore.

Ports the naming battery's `build_form_adjudication_pool.py` mechanics
(read in full before writing this, per the harness-build assignment; itself
adapted from the M1/CG1 pattern in `.skills/experiment-runner/reference/
abstention-grading.md`): salted opaque ids, seeded shuffle, sharding, pool
manifest committed BEFORE any grading, no question/answer text under
`analysis-committed/`.

WHAT DIFFERS FROM THE NAMING-BATTERY REFERENCE (documented, not a silent
deviation), per AMENDMENT.md "Design" / "Instrument validation":

  - Core candidates are drawn from ALL 7 sub-arms (not just the 5 dosed
    arms) via `screen_lib.load_and_screen`, not from a pre-computed
    `form_class` field -- this cell has no automated F1/F2/F3 classifier
    (that instrument was voided); the judge lane IS the F1/F2/F3 instrument.
  - A FRESH SPENT-SLICE EXCLUSION applies: every (row_key, arm) pair the
    naming battery's own spent 219-row calibration pool touched (200 core +
    19 decoys; AMENDMENT.md D-1 disclosure) is excluded from every candidate
    population in THIS cell's pools, core and decoy alike, because the lead
    saw those exact texts unblinded already.
  - TWO decoy types, not one: clear-positive (F4 screen positives, this
    cell's own sub-arms) AND clear-negative (naming battery's Arm C
    `c_baseline` rows with `correct_v2 == True`, a disjoint population that
    never enters any axis-G rate by construction, RR3 held-back-pool
    pattern -- see `.skills/experiment-runner/reference/
    abstention-grading.md` "Fix (a)").
  - Two build modes: `--mode calibration` (default; the fresh 200-row
    stratified slice with both decoy types, for instrument validation) and
    `--mode full-pool` (shards ALL screened-in rows across all 7 sub-arms,
    no decoys, for the payload axis-G rescore -- gated on the calibration
    passing its registered floors; this script only builds the pool, it
    never grades and never checks gates.yaml).

UNRESOLVED AMBIGUITY (flagged, not silently resolved -- see harness-build
report): AMENDMENT.md's payload description ("the judge lane grades every
screened-in row of all 7 sub-arms") does not say whether the calibration
slice's 200 core rows should be excluded from the full-pool payload to avoid
re-grading them. `--mode full-pool` currently does NOT exclude the
calibration slice (it shards literally every screened-in row, matching the
amendment's plain text); this is a judgment call for the lead to confirm or
override at sign.

Per the harness-build assignment: this script BUILDS the pool and STOPS. It
does not grade anything, and `--count-only` mode builds nothing at all --
it only counts and reports feasibility numbers.
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

DEFAULT_RUNLOG_DIR = HERE.parent / "write-direction-naming-battery" / "analysis" / "runlog_form_merged"
DEFAULT_C_BASELINE_RUNLOG = HERE.parent / "write-direction-naming-battery" / "analysis" / "runlog" / "c_baseline.jsonl"
DEFAULT_SPENT_SHARDS_DIR = HERE.parent / "write-direction-naming-battery" / "analysis" / "shards"

# AMENDMENT.md "Instrument validation" item 1: n = 200 core rows.
DEFAULT_SLICE_N = 200
DEFAULT_TARGET_SHARD_SIZE = 50

# Placeholder default -- NOT a registered seed. cell.yaml is still the
# "TODO: replace this placeholder" scaffold stub; the actual seed must be
# pinned there at sign, mirroring the naming battery's
# `cell.yaml surface.seeds.calibration_slice` convention. This default
# exists only so the script is runnable pre-sign; it must never be read as
# a committed value.
PLACEHOLDER_SEED = 20260730


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
# Spent-slice exclusion (naming battery's already-unblinded 219-row pool)
# ---------------------------------------------------------------------------

def load_spent_row_arm_pairs(spent_shards_dir: Path) -> set[tuple[str, str]]:
    """Every (row_key, arm) pair the naming battery's spent calibration pool
    touched -- core AND decoy rows alike (AMENDMENT.md D-1: "the lead ...
    seen the naming battery's spent 200-row calibration slice UNBLINDED").

    Reads the naming battery's per-shard `*_id_map.jsonl` files directly.
    These carry `row_key`; the naming battery's COMMITTED pool manifest
    (`analysis-committed/form_adjudication_pool_manifest.json`) does NOT --
    it is salted-opaque-id-only by design (that is what makes it safe to
    read pre-grading). The id_map files are the naming battery's own
    gitignored `analysis/` output, already unblinded now that cell resolved;
    reading them here is consistent with the AMENDMENT's own D-1 disclosure
    of that exact slice, not a new blinding violation. See harness-build
    report: this is flagged as a place the task's stated shortcut ("read the
    committed manifest, it's ID-only and safe") does not actually hold.
    """
    pairs: set[tuple[str, str]] = set()
    if not spent_shards_dir.is_dir():
        return pairs
    for path in sorted(spent_shards_dir.glob("*_id_map.jsonl")):
        for row in load_jsonl(path):
            row_key = row.get("row_key")
            arm = row.get("arm")
            if row_key is not None and arm is not None:
                pairs.add((row_key, arm))
    return pairs


# ---------------------------------------------------------------------------
# Candidate population assembly
# ---------------------------------------------------------------------------

def build_candidate_populations(
    runlog_dir: Path, c_baseline_runlog: Path, spent_shards_dir: Path,
    extra_spent_dirs: list[Path] | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Returns (core_by_arm, clear_positive_candidates, clear_negative_candidates, report).

    `core_by_arm[arm]`: screened-in rows for that sub-arm, spent pairs excluded.
    `clear_positive_candidates`: F4 screen-positive rows across all 7 sub-arms, spent pairs excluded.
    `clear_negative_candidates`: c_baseline rows with correct_v2 == True, spent pairs excluded
        (this population is disjoint from Arm A by construction -- different arm key entirely --
        so the spent-pair exclusion is a defensive no-op here, not load-bearing; c_baseline
        was never part of the naming battery's Arm A spent pool).
    `report`: feasibility counts, ID-free.
    """
    spent = load_spent_row_arm_pairs(spent_shards_dir)
    # Additional spent sets (e.g. a voided calibration attempt's id maps):
    # rows the lead has partially seen are excluded from any fresh draw.
    for extra_dir in (extra_spent_dirs or []):
        spent |= load_spent_row_arm_pairs(extra_dir)
    screened, coverage = screen_lib.load_and_screen(runlog_dir)

    core_by_arm: dict[str, list[dict[str, Any]]] = {}
    clear_positive_candidates: list[dict[str, Any]] = []
    n_core_excluded_spent = 0
    n_decoy_pos_excluded_spent = 0
    per_arm_core_counts: dict[str, int] = {}
    per_arm_f4_counts: dict[str, int] = {}

    for arm in screen_lib.ALL_ARM_KEYS:
        buckets = screened[arm]

        core_rows = []
        for row in buckets[screen_lib.SCREENED_IN]:
            if (row["row_key"], row["arm"]) in spent:
                n_core_excluded_spent += 1
                continue
            core_rows.append(row)
        core_by_arm[arm] = core_rows
        per_arm_core_counts[arm] = len(core_rows)

        f4_rows = []
        for row in buckets[screen_lib.F4_EXPLICIT_IDK]:
            if (row["row_key"], row["arm"]) in spent:
                n_decoy_pos_excluded_spent += 1
                continue
            f4_rows.append(row)
        clear_positive_candidates.extend(f4_rows)
        per_arm_f4_counts[arm] = len(f4_rows)

    # Clear-negative lane REMOVED (governed deviation, PI-approved 2026-07-30,
    # recorded in NOTEBOOK.md and gates.yaml): the registered source (Arm C
    # baseline correct_v2 rows) retains no generation text anywhere on disk;
    # the c_baseline runlog is metrics-only. The first build silently
    # substituted empty strings for all 25 clear-negative decoys, voiding
    # calibration attempt 1 at the lead spot-check. G2 now gates
    # clear-positive decoys only.
    clear_negative_candidates: list[dict[str, Any]] = []
    n_c_baseline_rows = 0
    n_c_baseline_correct = 0
    n_decoy_neg_excluded_spent = 0

    report = {
        "coverage": coverage,
        "n_spent_pairs_total": len(spent),
        "per_arm_core_candidates_post_exclusion": per_arm_core_counts,
        "per_arm_f4_clear_positive_candidates_post_exclusion": per_arm_f4_counts,
        "n_core_candidates_total": sum(per_arm_core_counts.values()),
        "n_core_excluded_as_spent": n_core_excluded_spent,
        "n_clear_positive_candidates_total": len(clear_positive_candidates),
        "n_clear_positive_excluded_as_spent": n_decoy_pos_excluded_spent,
        "n_c_baseline_rows_total": n_c_baseline_rows,
        "n_c_baseline_correct_v2_true": n_c_baseline_correct,
        "n_clear_negative_candidates_total": len(clear_negative_candidates),
        "n_clear_negative_excluded_as_spent": n_decoy_neg_excluded_spent,
    }
    return core_by_arm, clear_positive_candidates, clear_negative_candidates, report


# ---------------------------------------------------------------------------
# Sampling, sharding, opaque ids (ported from build_form_adjudication_pool.py)
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


def stratified_sample_core(core_by_arm: dict[str, list[dict[str, Any]]], slice_n: int, rng: random.Random) -> list[dict[str, Any]]:
    """Stratifies by arm (AMENDMENT.md item 1: "stratified across the 7
    sub-arms"), drawing as close to an even split as `slice_n` and each
    arm's availability allow, via round-robin over per-arm shuffled
    buckets -- same algorithm as the naming battery's
    `stratified_sample_core`, generalized from 5 arms to 7."""
    by_arm = {arm: list(rows) for arm, rows in core_by_arm.items()}
    for arm_rows in by_arm.values():
        rng.shuffle(arm_rows)

    arms = sorted(a for a in by_arm if by_arm[a])
    if not arms:
        return []
    chosen: list[dict[str, Any]] = []
    cursors = {a: 0 for a in arms}
    while len(chosen) < slice_n:
        progressed = False
        for arm in arms:
            if len(chosen) >= slice_n:
                break
            rows = by_arm[arm]
            c = cursors[arm]
            if c < len(rows):
                chosen.append(rows[c])
                cursors[arm] = c + 1
                progressed = True
        if not progressed:
            break  # exhausted every arm's candidates before reaching slice_n
    return chosen


def salted_opaque_id(salt: str, row_key: str, arm: str, tag: str = "") -> str:
    payload = f"{salt}:{row_key}:{arm}:{tag}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def pick_n_shards(pool_size: int, target_shard_size: int) -> int:
    if pool_size <= 0:
        return 1
    return max(1, round(pool_size / target_shard_size))


def build_calibration_shards(
    core: list[dict[str, Any]],
    decoys_pos: list[dict[str, Any]],
    decoys_neg: list[dict[str, Any]],
    n_shards: int, seed: int, salt: str,
) -> list[dict[str, Any]]:
    core_sorted = sorted(core, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(f"{seed}:core").shuffle(core_sorted)
    core_chunks = _round_robin_chunks(core_sorted, n_shards)

    pos_sorted = sorted(decoys_pos, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(f"{seed}:decoy_pos").shuffle(pos_sorted)
    pos_chunks = _round_robin_chunks(pos_sorted, n_shards)

    neg_sorted = sorted(decoys_neg, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(f"{seed}:decoy_neg").shuffle(neg_sorted)
    neg_chunks = _round_robin_chunks(neg_sorted, n_shards)

    shards = []
    for i in range(n_shards):
        combined = (
            [{**r, "decoy_type": None} for r in core_chunks[i]]
            + [{**r, "decoy_type": "clear_positive"} for r in pos_chunks[i]]
            + [{**r, "decoy_type": "clear_negative"} for r in neg_chunks[i]]
        )
        random.Random(f"{seed}:shard:{i}").shuffle(combined)
        blinded_pool, id_map = [], []
        for item in combined:
            opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"])
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"],
                "is_decoy": item["decoy_type"] is not None, "decoy_type": item["decoy_type"],
            })
        shards.append({
            "shard_id": f"form_judge_calib_shard_{i:02d}",
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunks[i]),
            "n_decoy_clear_positive": len(pos_chunks[i]),
            "n_decoy_clear_negative": len(neg_chunks[i]),
        })
    return shards


def build_full_pool_shards(all_rows: list[dict[str, Any]], n_shards: int, seed: int, salt: str) -> list[dict[str, Any]]:
    rows_sorted = sorted(all_rows, key=lambda r: (r["arm"], r["row_key"]))
    random.Random(f"{seed}:full_pool").shuffle(rows_sorted)
    chunks = _round_robin_chunks(rows_sorted, n_shards)

    shards = []
    for i in range(n_shards):
        blinded_pool, id_map = [], []
        for item in chunks[i]:
            opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"], tag="fullpool")
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({"opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"], "is_decoy": False, "decoy_type": None})
        shards.append({
            "shard_id": f"form_judge_fullpool_shard_{i:02d}",
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(chunks[i]), "n_decoy_clear_positive": 0, "n_decoy_clear_negative": 0,
        })
    return shards


def write_shards(shards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Fail-closed guard (added after calibration attempt 1 was voided): a
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
            "n_decoy_clear_negative": shard["n_decoy_clear_negative"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })
    return entries


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def cmd_build(args: argparse.Namespace) -> int:
    runlog_dir = Path(args.runlog_dir) if args.runlog_dir else DEFAULT_RUNLOG_DIR
    c_baseline_runlog = Path(args.c_baseline_runlog) if args.c_baseline_runlog else DEFAULT_C_BASELINE_RUNLOG
    spent_shards_dir = Path(args.spent_shards_dir) if args.spent_shards_dir else DEFAULT_SPENT_SHARDS_DIR

    core_by_arm, decoys_pos, decoys_neg, report = build_candidate_populations(
        runlog_dir, c_baseline_runlog, spent_shards_dir,
        extra_spent_dirs=[Path(p) for p in args.extra_spent_dirs],
    )
    print(f"[build_judge_pool] feasibility report:\n{json.dumps(report, indent=2, default=str)}", flush=True)

    if args.mode == "calibration":
        n_core_available = report["n_core_candidates_total"]
        if n_core_available < args.slice_n:
            print(
                f"[build_judge_pool] WARNING: only {n_core_available} core candidates "
                f"available post spent-exclusion, below the registered slice_n={args.slice_n}.",
                flush=True,
            )
        if report["n_clear_positive_candidates_total"] < args.min_decoys:
            print(
                f"[build_judge_pool] WARNING: only {report['n_clear_positive_candidates_total']} "
                f"clear_positive decoy candidates available, below min_decoys={args.min_decoys}.",
                flush=True,
            )

        if args.count_only:
            summary = {"cell": "form_judge_axis_g_rescore", "mode": "calibration", "count_only": True, "feasibility": report}
            ANALYSIS.mkdir(parents=True, exist_ok=True)
            write_json(ANALYSIS / "build_judge_pool_feasibility_calibration.json", summary)
            print(json.dumps(summary, indent=2, default=str), flush=True)
            print("\n[build_judge_pool] count-only mode: no pool, no shards, no text written.", flush=True)
            return 0

        salt = args.salt or secrets.token_hex(32)
        rng = random.Random(args.seed)
        core = stratified_sample_core(core_by_arm, args.slice_n, rng)

        # Registered G2 sizes the decoy sets at exactly min_decoys per type
        # (gates.yaml: 25 + 25), sampled seeded from the counted candidate
        # populations. min_decoys is also the feasibility floor warned about
        # above. (The CG1 take-everything rationale applied when decoys were
        # scarce; here the populations are 795/595 and the registration
        # fixes the count.)
        decoys_pos_final = list(decoys_pos)
        decoys_neg_final = list(decoys_neg)
        rng.shuffle(decoys_pos_final)
        rng.shuffle(decoys_neg_final)
        decoys_pos_final = decoys_pos_final[: args.min_decoys]
        decoys_neg_final = decoys_neg_final[: args.min_decoys]

        n_shards = pick_n_shards(len(core), args.target_shard_size)
        shards = build_calibration_shards(core, decoys_pos_final, decoys_neg_final, n_shards, args.seed, salt)
        shard_entries = write_shards(shards)

        manifest = {
            "cell": "form_judge_axis_g_rescore", "mode": "calibration", "seed": args.seed,
            "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
            "n_shards": n_shards, "n_core_total": len(core),
            "n_decoy_clear_positive_total": len(decoys_pos_final),
            "n_decoy_clear_negative_total": len(decoys_neg_final),
            "slice_n_target": args.slice_n, "min_decoys_target": args.min_decoys,
            "feasibility": report, "shards": shard_entries,
        }
        # TODO(post-sign): move to analysis-committed/ once the cell is
        # signed; kept under analysis/ (gitignored) while still DRAFT.
        write_json(ANALYSIS / "calibration_pool_manifest.json", manifest)
        summary = {k: v for k, v in manifest.items() if k != "shards"}
        summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_entries]
        print(json.dumps(summary, indent=2, default=str), flush=True)
        print(f"\n[build_judge_pool] wrote {n_shards} calibration shard(s) under {SHARDS_DIR} (gitignored).", flush=True)
        return 0

    # mode == "full-pool"
    all_rows = [row for arm in screen_lib.ALL_ARM_KEYS for row in core_by_arm[arm]]
    # NOTE: core_by_arm here already excludes spent pairs; see module
    # docstring "UNRESOLVED AMBIGUITY" -- full-pool does NOT additionally
    # exclude the calibration slice sampled from these same candidates.
    if args.count_only:
        per_arm_totals = {arm: len(core_by_arm[arm]) for arm in screen_lib.ALL_ARM_KEYS}
        summary = {
            "cell": "form_judge_axis_g_rescore", "mode": "full-pool", "count_only": True,
            "per_arm_screened_in_post_spent_exclusion": per_arm_totals,
            "n_total_screened_in_post_spent_exclusion": len(all_rows),
            "feasibility": report,
        }
        ANALYSIS.mkdir(parents=True, exist_ok=True)
        write_json(ANALYSIS / "build_judge_pool_feasibility_full_pool.json", summary)
        print(json.dumps(summary, indent=2, default=str), flush=True)
        print("\n[build_judge_pool] count-only mode: no pool, no shards, no text written.", flush=True)
        return 0

    salt = args.salt or secrets.token_hex(32)
    n_shards = pick_n_shards(len(all_rows), args.target_shard_size)
    shards = build_full_pool_shards(all_rows, n_shards, args.seed, salt)
    shard_entries = write_shards(shards)

    manifest = {
        "cell": "form_judge_axis_g_rescore", "mode": "full-pool", "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards, "n_rows_total": len(all_rows),
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
    ap.add_argument("--mode", choices=("calibration", "full-pool"), default="calibration")
    ap.add_argument("--runlog-dir", default=None, help=f"default: {DEFAULT_RUNLOG_DIR}")
    ap.add_argument("--c-baseline-runlog", default=None, help=f"default: {DEFAULT_C_BASELINE_RUNLOG}")
    ap.add_argument("--spent-shards-dir", default=None, help=f"default: {DEFAULT_SPENT_SHARDS_DIR}")
    ap.add_argument("--seed", type=int, default=PLACEHOLDER_SEED, help="PLACEHOLDER default; must be pinned in cell.yaml at sign")
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--slice-n", type=int, default=DEFAULT_SLICE_N, help="calibration mode only")
    ap.add_argument("--min-decoys", type=int, default=25, help="calibration mode only; warn-floor, not a cap")
    ap.add_argument("--extra-spent-dirs", nargs="*", default=[], help="additional directories of *_id_map.jsonl whose (row_key, arm) pairs join the spent-exclusion set (e.g. a voided attempt's shards)")
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.add_argument("--count-only", action="store_true", help="report feasibility counts only; write no pool, no shards, no text")
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
