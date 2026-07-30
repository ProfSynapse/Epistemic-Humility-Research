#!/usr/bin/env python3
"""Blinded-adjudication pool builder for the write-direction-naming-battery
output-form taxonomy (axis G / Arm A).

Adapted from the M1/CG1 pattern (`.skills/experiment-runner/reference/
abstention-grading.md`, read in full before writing this; reference
implementations `llama-atlas-gated-wide-instrument-retest/
build_adjudication_pool.py` and `abstention-wide-instrument-calibration/
build_adjudication_pool.py`, both read before writing this). Mechanics
ported: salted opaque ids, seeded shuffle, decoys carved out of core so no
row double-counts, sharding, pool manifest committed BEFORE grading, no
question/answer text under `analysis-committed/`.

WHAT DIFFERS FROM THE CG1 REFERENCE (documented, not a silent deviation):
this cell's gate (`gates.yaml` G2_axis_G_form_gradedness.taxonomy_calibration)
grades a THREE-WAY class label (F1 / F2 / F3), not a boolean `is_abstention`.
"Disagreement" is computed over CORE rows (adjudicator's 3-way label versus
the automated `form_class`), and "decoy agreement" is computed as a binary
check (adjudicator says NOT F1, i.e. agrees the row is a marked F2/F3 form)
over CLEAR-POSITIVE decoys only. gates.yaml registers no clear-negative decoy
floor for this gate (unlike the CG1 reference's dual-decoy design) and no
attempt/regrade ladder (unlike CG1's VOID_REGRADE_ONCE -> VOID_CELL_TERMINAL
escalation); this build therefore reports a single PASS/FAIL per the locked
gate text, not an attempt-aware void ladder. Both omissions are flagged to
the lead in the harness-build report as scope judgment calls, since the
standing rule (abstention-grading.md) recommends both a clear-negative decoy
pool and a pooled floor generally.

POOL COMPOSITION (AMENDMENT.md "New instrument: the output-form taxonomy"):
  core            every row from Arm A's REAL dosed sub-arms (a_baseline,
                  a_dose_0p25, a_dose_0p5, a_dose_0p75, a_dose_1) whose
                  automated `form_class` is F1, F2, or F3 (F4/F5 rows are
                  excluded: those classes are validated by the existing,
                  already-calibrated detector/CG1 machinery, not by this new
                  boundary; AMENDMENT.md gate is explicitly "the F1/F2/F3
                  boundary").
  clear_positive  rows from Arm A's PLACEBO sub-arms (a_placebo_0p5,
                  a_placebo_1, `random_direction` readout) whose automated
                  `form_class` is F2 or F3. The placebo direction is
                  expected to be near-inert (C1 construct gate), so any
                  F2/F3 hit there is an unambiguous instance for the
                  adjudicator to confirm -- the same structural role
                  `random_direction`-arm detector-positive rows play as CG1
                  clear-positive decoys in the reference implementations.

ASSUMED RUNLOG LAYOUT (flagged for the lead to reconcile against whatever
naming the harness-build/runner assignment actually writes): one JSONL file
per cell.yaml arm key under `analysis/runlog/<arm_key>.jsonl`, each row
carrying at minimum `row_key`, `answer_text`, `form_class` (already computed
by `form_taxonomy.classify`, per cell.yaml `execution.graders` ordering --
this script does NOT recompute form_class, so it never drifts from the
pipeline's own verdict). If the runner lands on a different naming
convention, `discover_runlogs` is the only function that needs to change.

Per the harness-build assignment: this script BUILDS the pool and STOPS. It
does not grade anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE / "analysis"
COMMITTED = HERE / "analysis-committed"
SHARDS_DIR = ANALYSIS / "shards"
RUNLOG_DIR = ANALYSIS / "runlog"

# cell.yaml `arms` (Arm A only; axis G / form gradedness). Hardcoded rather
# than parsed from cell.yaml because cell.yaml is locked/pinned at sign and
# this script must not become a second reader of a file it could silently
# drift out of sync with; if the arm list ever changes it is a cell.yaml
# amendment and this constant changes with it, visibly, in the same review.
ARM_A_DOSED_KEYS = ("a_baseline", "a_dose_0p25", "a_dose_0p5", "a_dose_0p75", "a_dose_1")
ARM_A_PLACEBO_KEYS = ("a_placebo_0p5", "a_placebo_1")

CORE_FORM_CLASSES = ("F1_committed_assertion", "F2_hedged_assertion", "F3_non_answerability")
DECOY_SOURCE_FORM_CLASSES = ("F2_hedged_assertion", "F3_non_answerability")

DEFAULT_SLICE_N = 200  # gates.yaml G2 taxonomy_calibration.slice_n
DEFAULT_MIN_DECOYS = 25  # gates.yaml G2 taxonomy_calibration.min_decoys
DEFAULT_TARGET_SHARD_SIZE = 50


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
# Row discovery
# ---------------------------------------------------------------------------

def discover_runlogs(runlog_dir: Path, arm_keys: tuple[str, ...]) -> dict[str, Path]:
    """Maps arm_key -> path for every arm whose RunLog file is found.
    Primary convention: `<arm_key>.jsonl`. Falls back to a glob match
    (`*<arm_key>*.jsonl`) so a minor naming variation from the harness build
    does not silently drop an arm; missing arms are reported, not raised,
    since this script must run cleanly pre-generation (empty coverage) as
    well as post-generation (full coverage)."""
    found: dict[str, Path] = {}
    for arm in arm_keys:
        direct = runlog_dir / f"{arm}.jsonl"
        if direct.is_file():
            found[arm] = direct
            continue
        matches = sorted(runlog_dir.glob(f"*{arm}*.jsonl")) if runlog_dir.is_dir() else []
        if matches:
            found[arm] = matches[0]
    return found


def load_core_and_decoy_candidates(runlog_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Returns (core_candidates, clear_positive_candidates, coverage).
    `core_candidates`: every row from the real dosed sub-arms with
    `form_class` in {F1, F2, F3}. `clear_positive_candidates`: every row
    from the placebo sub-arms with `form_class` in {F2, F3}."""
    core: list[dict[str, Any]] = []
    clear_positive: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {"n_rows_by_arm": {}, "arms_found": {}, "arms_missing": []}

    dosed_paths = discover_runlogs(runlog_dir, ARM_A_DOSED_KEYS)
    placebo_paths = discover_runlogs(runlog_dir, ARM_A_PLACEBO_KEYS)

    for arm in ARM_A_DOSED_KEYS + ARM_A_PLACEBO_KEYS:
        path = dosed_paths.get(arm) or placebo_paths.get(arm)
        if path is None:
            coverage["arms_missing"].append(arm)

    for arm, path in dosed_paths.items():
        coverage["arms_found"][arm] = str(path.relative_to(HERE)) if path.is_relative_to(HERE) else str(path)
        rows = load_jsonl(path)
        coverage["n_rows_by_arm"][arm] = len(rows)
        for raw in rows:
            form_class = raw.get("form_class")
            if form_class not in CORE_FORM_CLASSES:
                continue
            core.append({
                "arm": arm, "row_key": raw["row_key"], "form_class": form_class,
                "text": raw.get("answer_text", ""),
            })

    for arm, path in placebo_paths.items():
        coverage["arms_found"][arm] = str(path.relative_to(HERE)) if path.is_relative_to(HERE) else str(path)
        rows = load_jsonl(path)
        coverage["n_rows_by_arm"][arm] = len(rows)
        for raw in rows:
            form_class = raw.get("form_class")
            if form_class not in DECOY_SOURCE_FORM_CLASSES:
                continue
            clear_positive.append({
                "arm": arm, "row_key": raw["row_key"], "form_class": form_class,
                "text": raw.get("answer_text", ""),
            })

    coverage["n_core_candidates"] = len(core)
    coverage["n_clear_positive_candidates"] = len(clear_positive)
    return core, clear_positive, coverage


# ---------------------------------------------------------------------------
# Sampling, sharding, opaque ids
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


def stratified_sample_core(core_candidates: list[dict[str, Any]], slice_n: int, rng: random.Random) -> list[dict[str, Any]]:
    """Stratifies by `arm` (gates.yaml `stratified_across: [arm, dose]`; this
    cell's arm keys already encode the dose, e.g. `a_dose_0p5`, so
    stratifying by arm is stratifying by (arm, dose) jointly), drawing as
    close to an even split across arms as `slice_n` and each arm's
    availability allow, via round-robin over per-arm shuffled buckets."""
    by_arm: dict[str, list[dict[str, Any]]] = {}
    for row in core_candidates:
        by_arm.setdefault(row["arm"], []).append(row)
    for arm_rows in by_arm.values():
        rng.shuffle(arm_rows)

    arms = sorted(by_arm.keys())
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


def salted_opaque_id(salt: str, row_key: str, arm: str, regrade_index: int = 0) -> str:
    payload = f"{salt}:{row_key}:{arm}:{regrade_index}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def pick_n_shards(core_size: int, target_shard_size: int) -> int:
    if core_size <= 0:
        return 1
    return max(1, round(core_size / target_shard_size))


def build_shards(core: list[dict[str, Any]], decoys: list[dict[str, Any]], n_shards: int, seed: int, salt: str) -> list[dict[str, Any]]:
    core_sorted = sorted(core, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(f"{seed}:core").shuffle(core_sorted)
    core_chunks = _round_robin_chunks(core_sorted, n_shards)

    decoy_sorted = sorted(decoys, key=lambda r: (r["row_key"], r["arm"]))
    random.Random(f"{seed}:decoy").shuffle(decoy_sorted)
    decoy_chunks = _round_robin_chunks(decoy_sorted, n_shards)

    shards = []
    for i in range(n_shards):
        combined = [{**r, "decoy_type": None} for r in core_chunks[i]] + \
                   [{**r, "decoy_type": "clear_positive"} for r in decoy_chunks[i]]
        random.Random(f"{seed}:shard:{i}").shuffle(combined)
        blinded_pool = []
        id_map = []
        for item in combined:
            opaque_id = salted_opaque_id(salt, item["row_key"], item["arm"])
            blinded_pool.append({"opaque_id": opaque_id, "text": item.get("text", "")})
            id_map.append({
                "opaque_id": opaque_id, "row_key": item["row_key"], "arm": item["arm"],
                "form_class": item["form_class"], "is_decoy": item["decoy_type"] is not None,
                "decoy_type": item["decoy_type"],
            })
        shards.append({
            "shard_id": f"form_taxonomy_shard_{i:02d}",
            "blinded_pool": blinded_pool, "id_map": id_map,
            "n_core": len(core_chunks[i]), "n_decoy_clear_positive": len(decoy_chunks[i]),
        })
    return shards


def cmd_build(args: argparse.Namespace) -> int:
    runlog_dir = Path(args.runlog_dir) if args.runlog_dir else RUNLOG_DIR
    core_candidates, decoy_candidates, coverage = load_core_and_decoy_candidates(runlog_dir)
    print(f"[build_form_adjudication_pool] coverage: {json.dumps(coverage, default=str)}", flush=True)

    if len(core_candidates) < args.slice_n:
        print(
            f"[build_form_adjudication_pool] WARNING: only {len(core_candidates)} core "
            f"candidates available, below the registered slice_n={args.slice_n}. This is "
            f"expected pre-generation (no RunLog rows yet); the pool below draws everything "
            f"available rather than blocking, but do NOT treat a short-of-target pool as "
            f"satisfying gates.yaml's slice_n=200 requirement.",
            flush=True,
        )
    if len(decoy_candidates) < args.min_decoys:
        print(
            f"[build_form_adjudication_pool] WARNING: only {len(decoy_candidates)} "
            f"clear_positive decoy candidates available, below the registered "
            f"min_decoys={args.min_decoys}.",
            flush=True,
        )

    salt = args.salt or secrets.token_hex(32)
    rng = random.Random(args.seed)
    core = stratified_sample_core(core_candidates, args.slice_n, rng)
    core_keys = {(r["row_key"], r["arm"]) for r in core}
    remaining_decoy_pool = [r for r in decoy_candidates if (r["row_key"], r["arm"]) not in core_keys]
    rng.shuffle(remaining_decoy_pool)
    # Take every available clear_positive candidate (they are the scarce
    # resource, per the CG1 reference's own rationale) rather than
    # truncating to min_decoys; min_decoys is a floor to warn against, not a
    # cap to enforce.
    decoys = remaining_decoy_pool

    n_shards = pick_n_shards(len(core), args.target_shard_size)
    shards = build_shards(core, decoys, n_shards, args.seed, salt)

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
            "n_core": shard["n_core"], "n_decoy_clear_positive": shard["n_decoy_clear_positive"],
            "opaque_ids": sorted(r["opaque_id"] for r in shard["blinded_pool"]),
        })

    manifest = {
        "cell": "write_direction_naming_battery_form_taxonomy",
        "seed": args.seed,
        "id_salt_sha256": hashlib.sha256(salt.encode("utf-8")).hexdigest(),
        "n_shards": n_shards,
        "n_core_total": len(core),
        "n_decoy_clear_positive_total": len(decoys),
        "slice_n_target": args.slice_n,
        "min_decoys_target": args.min_decoys,
        "coverage": coverage,
        "shards": shard_manifest_entries,
    }
    write_json(COMMITTED / "form_adjudication_pool_manifest.json", manifest)

    summary = {k: v for k, v in manifest.items() if k != "shards"}
    summary["shards"] = [{k: v for k, v in s.items() if k != "opaque_ids"} for s in shard_manifest_entries]
    print(json.dumps(summary, indent=2, default=str), flush=True)
    print(
        f"\n[build_form_adjudication_pool] wrote {n_shards} shard(s) under {SHARDS_DIR} "
        f"(gitignored). Pool manifest committed to "
        f"{COMMITTED / 'form_adjudication_pool_manifest.json'}. NO grading has occurred "
        f"and NO id map has been unblinded by this script.",
        flush=True,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runlog-dir", default=None, help="override analysis/runlog (test hook)")
    ap.add_argument("--seed", type=int, default=48260732)  # cell.yaml surface.seeds.calibration_slice
    ap.add_argument("--salt", default=None, help="override the random id salt (test hook; omit for a fresh random salt)")
    ap.add_argument("--slice-n", type=int, default=DEFAULT_SLICE_N)
    ap.add_argument("--min-decoys", type=int, default=DEFAULT_MIN_DECOYS)
    ap.add_argument("--target-shard-size", type=int, default=DEFAULT_TARGET_SHARD_SIZE)
    ap.set_defaults(func=cmd_build)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
