#!/usr/bin/env python3
"""Materialize the LOCAL, gitignored full row pool
(`analysis/rows_with_text.jsonl`) that `capture_family_atlas_cell.py`'s
`--row-pool` argument reads, by joining this cell's COMMITTED ID-only split
manifest (row_key/role/split -- NO question text) against question text from
the doubt-snap qwen35_4b PRIVATE pool `split_rows_private.jsonl`.

This repo is PUBLIC. Dataset/pool/question-text row content is never committed
(see `.skills/pr-workflow/SKILL.md` "Datasets are never committed"). The OUTPUT
of this script, and every intermediate holding question text, stays under this
experiment's own gitignored `analysis/` (see `.gitignore`: `analysis/`). This
script itself contains no row text and is safe to commit.

Row-key source (ID-only, committed in this repo):
  - `experiments/common/qwen35-4b-doubt-snap-split/split_manifest.json`
    (promoted byte-identical from
    `experiments/doubt-snap-cross-family-confirmatory/analysis-committed/qwen35_4b/split_manifest.json`;
    all three roles carry row-level IDs -- confab 2219, known_correct_answered
    600, unknown_refused 181).

Question-text source (fetched at run time from a read-only Modal volume, never
committed):
  - `split_rows_private.jsonl`, sha256
    `42659f4019d0cbe0178bddd6a7e6323299555092ecd8da4c9ac5d58e42b15a58`, on the
    Modal volume `eh-doubt-snap-cross-family` at path
    `doubt-snap-cross-family-r1/qwen35_4b/analysis/split_rows_private.jsonl`.
    Each private row carries `row_key`, `source`, `category_canon`,
    `question`, `role`, `split` (written by
    `doubt-snap-cross-family-confirmatory/prep_tuner_cell.py`), so it is a
    text-carrying SUPERSET of the committed manifest. This script joins its
    `question` onto the committed manifest's authoritative row_key/role/split.

FAIL-CLOSED discipline (hard, nonzero exit before any capture can run):
  - sha256 of the fetched private pool MUST equal the pinned hash above;
    a mismatch aborts (wrong/updated/tampered pool).
  - every committed row_key MUST resolve to a question in the private pool.
  - the private pool's role/split for a row_key MUST agree with the committed
    manifest's (guards against a stale private pool from a different split).
  - the materialized role counts MUST equal the expected (3000 total;
    confab 2219, known_correct_answered 600, unknown_refused 181).
Any violation aborts with a nonzero exit; the cell must NOT proceed to capture
while any check fails.

Fetching the private pool is a deliberate operator step (it moves restricted
data). By default this script expects the pool already present at
`--private-pool` (default `analysis/split_rows_private.jsonl`); pass `--fetch`
to shell out to `modal volume get` (read-only) for it. The script always
verifies the sha before use, whether fetched or pre-placed.

Usage:
  # 1) fetch the private pool (either let this script do it, or run the
  #    modal command yourself and drop the file at analysis/):
  python materialize_rows.py --fetch
  # or, if already fetched:
  python materialize_rows.py --private-pool analysis/split_rows_private.jsonl
  # -> writes analysis/rows_with_text.jsonl (gitignored)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
ANALYSIS = HERE / "analysis"

COMMITTED_MANIFEST = (
    REPO_ROOT
    / "experiments/common/qwen35-4b-doubt-snap-split/split_manifest.json"
)
OUT_PATH = ANALYSIS / "rows_with_text.jsonl"

PRIVATE_POOL_SHA256 = "42659f4019d0cbe0178bddd6a7e6323299555092ecd8da4c9ac5d58e42b15a58"
MODAL_VOLUME = "eh-doubt-snap-cross-family"
MODAL_POOL_PATH = "doubt-snap-cross-family-r1/qwen35_4b/analysis/split_rows_private.jsonl"

EXPECTED_ROLE_COUNTS = {
    "confab": 2219,
    "known_correct_answered": 600,
    "unknown_refused": 181,
}
EXPECTED_TOTAL = sum(EXPECTED_ROLE_COUNTS.values())  # 3000


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in p.open(encoding="utf-8") if ln.strip()]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_private_pool(dest: Path) -> None:
    """Read-only `modal volume get` for the private pool. Deliberate operator
    action: moves restricted data onto the local (gitignored) analysis dir."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["modal", "volume", "get", MODAL_VOLUME, MODAL_POOL_PATH, str(dest)]
    print(f"[materialize] $ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(
            f"[materialize] ERROR: `modal volume get` failed (exit "
            f"{result.returncode}). Authenticate to Modal and confirm access "
            f"to volume {MODAL_VOLUME!r}."
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--private-pool",
        default=str(ANALYSIS / "split_rows_private.jsonl"),
        help="Local path to the (gitignored) private pool split_rows_private.jsonl.",
    )
    ap.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch the private pool via `modal volume get` before joining.",
    )
    args = ap.parse_args()

    private_pool = Path(args.private_pool)

    if args.fetch:
        fetch_private_pool(private_pool)

    if not COMMITTED_MANIFEST.is_file():
        print(f"[materialize] ERROR: committed manifest not found at "
              f"{COMMITTED_MANIFEST}.", file=sys.stderr)
        return 1
    if not private_pool.is_file():
        print(f"[materialize] ERROR: private pool not found at {private_pool}. "
              f"Fetch it first:\n"
              f"  modal volume get {MODAL_VOLUME} {MODAL_POOL_PATH} {private_pool}\n"
              f"or re-run with --fetch.", file=sys.stderr)
        return 1

    # Fail-closed: sha of the private pool must match the pinned hash.
    actual_sha = sha256_file(private_pool)
    if actual_sha != PRIVATE_POOL_SHA256:
        print(f"[materialize] ERROR: private pool sha256 mismatch.\n"
              f"  expected {PRIVATE_POOL_SHA256}\n"
              f"  actual   {actual_sha}\n"
              f"Refusing to proceed with a wrong/updated/tampered pool.",
              file=sys.stderr)
        return 1

    committed = json.loads(COMMITTED_MANIFEST.read_text())["rows"]
    private_rows = load_jsonl(private_pool)

    # Build lookups from the private pool.
    q_by_key: dict[str, str] = {}
    role_split_by_key: dict[str, tuple] = {}
    for r in private_rows:
        rk = r.get("row_key")
        if rk is None:
            continue
        q = r.get("question")
        if q:
            q_by_key[rk] = q
        role_split_by_key[rk] = (r.get("role"), r.get("split"))

    ANALYSIS.mkdir(parents=True, exist_ok=True)

    n_missing_q = 0
    missing_by_role: Counter = Counter()
    n_role_split_mismatch = 0
    role_counts: Counter = Counter()

    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for rec in committed:
            rk = rec["row_key"]
            role = rec["role"]
            split = rec["split"]
            role_counts[role] += 1

            question = q_by_key.get(rk)
            if not question:
                n_missing_q += 1
                missing_by_role[role] += 1

            priv_rs = role_split_by_key.get(rk)
            if priv_rs is not None and priv_rs != (role, split):
                n_role_split_mismatch += 1

            out_rec = {
                "row_key": rk,
                "role": role,
                "split": split,
                "source": rec.get("source"),
                "category_canon": rec.get("category_canon"),
                "question": question,
            }
            fh.write(json.dumps(out_rec, ensure_ascii=False) + "\n")

    print(f"[materialize] WROTE {OUT_PATH} ({len(committed)} rows); "
          f"role_counts={dict(role_counts)} missing_question={n_missing_q} "
          f"missing_by_role={dict(missing_by_role)} "
          f"role_split_mismatch={n_role_split_mismatch}")

    ok = True
    if len(committed) != EXPECTED_TOTAL:
        print(f"[materialize] ERROR: expected {EXPECTED_TOTAL} committed rows, "
              f"got {len(committed)}.", file=sys.stderr)
        ok = False
    if dict(role_counts) != EXPECTED_ROLE_COUNTS:
        print(f"[materialize] ERROR: role counts {dict(role_counts)} != expected "
              f"{EXPECTED_ROLE_COUNTS}.", file=sys.stderr)
        ok = False
    if n_missing_q:
        print(f"[materialize] ERROR: {n_missing_q} rows have no question text "
              f"after the join. Cell cannot proceed to capture until this is "
              f"closed.", file=sys.stderr)
        ok = False
    if n_role_split_mismatch:
        print(f"[materialize] ERROR: {n_role_split_mismatch} row_keys disagree on "
              f"role/split between the committed manifest and the private pool "
              f"(stale/wrong pool).", file=sys.stderr)
        ok = False

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
