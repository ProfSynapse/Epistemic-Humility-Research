#!/usr/bin/env python3
"""Classify run records against a known table of dataset-build SHAs.

This folds the by-hand provenance audit of 2026-08-01 into a reusable check. The
audit that motivated the `headline-seed1-postfix-rerun` experiment asked one
question of every run record: which dataset BUILD did this cell actually consume,
the one predating the dev-split grouping fix (commit 3dc58e9b, 2026-06-14) or the
corrected one? Answering it by hand does not scale and does not leave an artifact.

The SHA table lives in `data_builds.yaml` beside this script, keyed by arm family,
so extending the audit to a new arm or a future build means adding a table entry
rather than editing code.

Usage
-----
    # audit the phase1 headline records against the shipped table
    python3 experiments/headline-seed1-postfix-rerun/scripts/audit_data_provenance.py \
        archive/experiment/phase1/run_records/*.json

    # audit a whole directory, machine-readable output
    python3 .../audit_data_provenance.py --json archive/experiment/phase1/run_records/

    # also verify the staged files still on disk hash to what the records claim
    python3 .../audit_data_provenance.py --verify-on-disk <records...>

    # compare two builds row-wise (what the fix actually did to the data)
    python3 .../audit_data_provenance.py --diff-builds PRE.jsonl POST.jsonl

    # reproduce the AMENDMENT.md section 4 churn figures (train/dev boundary move)
    python3 .../audit_data_provenance.py --diff-split \
        PRE_train.jsonl PRE_dev.jsonl POST_train.jsonl POST_dev.jsonl

Exit status is 1 when any record lands in a build marked `blocking: true` in the
table, or when `--verify-on-disk` finds a hash mismatch. Unknown SHAs are always
reported but are not by themselves an error: a new build is a table gap, not a
provenance failure, and the operator decides which.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_TABLE = Path(__file__).with_name("data_builds.yaml")


# --------------------------------------------------------------------------
# table loading
# --------------------------------------------------------------------------

def load_table(path: Path) -> dict:
    """Load the build table.

    PyYAML is not a hard dependency of this repo's CPU-side tooling, so fall back
    to a deliberately small parser that handles only the flat shape this table
    uses. If the table ever needs anchors or nested sequences, require PyYAML
    rather than growing the fallback.
    """
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
    except ImportError:
        return _parse_minimal_yaml(text)
    return yaml.safe_load(text)


def _parse_minimal_yaml(text: str) -> dict:
    """Parse the two-level `builds: {sha: {k: v}}` shape only."""
    root: dict = {}
    builds: dict = {}
    current: dict | None = None
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, value = line.strip().partition(":")
        value = value.strip().strip("'\"")
        if indent == 0:
            if key == "builds":
                root["builds"] = builds
                current = None
            else:
                root[key] = value
        elif indent == 2:
            current = {}
            builds[key] = current
        elif current is not None:
            if value in ("true", "false"):
                current[key] = value == "true"
            else:
                current[key] = value
    root.setdefault("builds", builds)
    return root


# --------------------------------------------------------------------------
# record walking
# --------------------------------------------------------------------------

def iter_records(paths: list[str]):
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for child in sorted(p.glob("*.json")):
                yield child
        elif p.suffix == ".json":
            yield p


def read_record(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  SKIP {path.name}: unreadable ({exc})", file=sys.stderr)
        return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(record: dict, builds: dict) -> dict:
    data = record.get("data") or {}
    sha = data.get("data_sha256")
    entry = builds.get(sha or "", {})
    return {
        "run_id": record.get("run_id", "?"),
        "arm": (record.get("coordinate") or {}).get("arm"),
        "seed": (record.get("coordinate") or {}).get("seed"),
        "cell_type": (record.get("coordinate") or {}).get("cell_type"),
        "data_sha256": sha,
        "build": entry.get("build", "UNKNOWN"),
        "blocking": bool(entry.get("blocking", False)),
        "note": entry.get("note", "sha not present in the build table"),
        "staged_data_file": data.get("staged_data_file"),
        "submodule_commit": record.get("submodule_commit"),
        "status": (record.get("outcome") or {}).get("status"),
    }


# --------------------------------------------------------------------------
# build diffing
# --------------------------------------------------------------------------

def read_jsonl_rows(path: Path) -> list[str]:
    """Return the raw JSONL rows of `path`, split on newlines ONLY.

    Do not use `str.splitlines()` here. It also breaks on U+0085 (NEL), U+2028,
    and U+2029, and at least one row of the phase1 DPO build carries a raw U+0085
    inside a JSON string value, so `splitlines()` silently reports one extra row
    and corrupts every downstream set comparison. JSONL is newline-delimited by
    definition, which is what the trainers consume.
    """
    with path.open(encoding="utf-8") as fh:
        return [line.rstrip("\n") for line in fh if line.strip()]


def diff_builds(pre: Path, post: Path) -> dict:
    """Row-set comparison of two JSONL builds.

    Reports whether the two builds draw on the same underlying row pool, which
    distinguishes a train/dev boundary reassignment from a genuine content change.
    """
    a = set(read_jsonl_rows(pre))
    b = set(read_jsonl_rows(post))
    shared = a & b
    return {
        "pre": str(pre),
        "post": str(post),
        "distinct_rows_pre": len(a),
        "distinct_rows_post": len(b),
        "shared": len(shared),
        "only_pre": len(a - b),
        "only_post": len(b - a),
        "pre_rows_absent_from_post_pct": round(len(a - b) / len(a) * 100, 2) if a else 0.0,
    }


def diff_split(pre_train: Path, pre_dev: Path, post_train: Path, post_dev: Path) -> dict:
    """Train/dev boundary comparison across two builds of the same corpus.

    This is the check that distinguishes a boundary REASSIGNMENT from a content
    change: if the union of train and dev is the same row set in both builds,
    then no row was added, removed, or edited and the rebuild only moved the
    split. It reproduces the churn figures quoted in AMENDMENT.md section 4.
    """
    a_tr, a_dev = set(read_jsonl_rows(pre_train)), set(read_jsonl_rows(pre_dev))
    b_tr, b_dev = set(read_jsonl_rows(post_train)), set(read_jsonl_rows(post_dev))
    return {
        "train_rows_pre": len(a_tr),
        "train_rows_post": len(b_tr),
        "dev_rows_pre": len(a_dev),
        "dev_rows_post": len(b_dev),
        "rows_moved_train_to_dev": len(a_tr & b_dev),
        "rows_moved_dev_to_train": len(a_dev & b_tr),
        "pre_fix_train_rows_absent_from_post_fix_pct":
            round(len(a_tr - b_tr) / len(a_tr) * 100, 2) if a_tr else 0.0,
        "union_train_dev_pool_identical": (a_tr | a_dev) == (b_tr | b_dev),
        "pool_size_pre": len(a_tr | a_dev),
        "pool_size_post": len(b_tr | b_dev),
    }


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", help="run-record .json files or directories")
    ap.add_argument("--table", type=Path, default=DEFAULT_TABLE,
                    help=f"build SHA table (default: {DEFAULT_TABLE.name})")
    ap.add_argument("--repo-root", type=Path, default=None,
                    help="repo root for resolving staged files under --verify-on-disk")
    ap.add_argument("--verify-on-disk", action="store_true",
                    help="rehash each record's staged file and compare to the record")
    ap.add_argument("--diff-builds", nargs=2, metavar=("PRE", "POST"), type=Path,
                    help="row-set comparison of two JSONL builds; skips record audit")
    ap.add_argument("--diff-split", nargs=4, type=Path,
                    metavar=("PRE_TRAIN", "PRE_DEV", "POST_TRAIN", "POST_DEV"),
                    help="train/dev boundary comparison across two builds; skips record audit")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = ap.parse_args(argv)

    if args.diff_split:
        result = diff_split(*args.diff_split)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for key, value in result.items():
                print(f"{key:46s} {value}")
            if not result["union_train_dev_pool_identical"]:
                print("\nWARNING: the two builds do NOT share a row pool. This is a "
                      "content change, not a split reassignment.")
        return 0

    if args.diff_builds:
        result = diff_builds(*args.diff_builds)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"pre  {result['pre']}: {result['distinct_rows_pre']} distinct rows")
            print(f"post {result['post']}: {result['distinct_rows_post']} distinct rows")
            print(f"shared {result['shared']}  only_pre {result['only_pre']}  "
                  f"only_post {result['only_post']}")
            print(f"{result['pre_rows_absent_from_post_pct']}% of pre rows absent from post")
        return 0

    if not args.paths:
        ap.error("give at least one run-record path, or use --diff-builds/--diff-split")

    table = load_table(args.table)
    builds = table.get("builds", {})
    root = args.repo_root or Path(__file__).resolve().parents[3]

    rows, failures = [], []
    for path in iter_records(args.paths):
        record = read_record(path)
        if record is None:
            continue
        row = classify(record, builds)

        if args.verify_on_disk and row["staged_data_file"]:
            # Records written on Windows carry backslash paths; normalize.
            rel = row["staged_data_file"].replace("\\", "/")
            candidate = root / "synaptic-tuner" / rel
            if candidate.exists():
                actual = sha256_file(candidate)
                row["on_disk_sha256"] = actual
                row["on_disk_match"] = (actual == row["data_sha256"])
                if not row["on_disk_match"]:
                    failures.append(f"{row['run_id']}: on-disk sha != recorded sha")
            else:
                row["on_disk_sha256"] = None
                row["on_disk_match"] = None

        if row["blocking"]:
            failures.append(f"{row['run_id']}: consumed {row['build']} ({row['note']})")
        rows.append(row)

    if args.json:
        print(json.dumps({"rows": rows, "failures": failures}, indent=2))
    else:
        width = max((len(r["run_id"]) for r in rows), default=10)
        print(f"{'run_id':<{width}}  {'sha[:16]':<16}  {'build':<26}  status")
        print("-" * (width + 60))
        for r in sorted(rows, key=lambda r: r["run_id"]):
            sha = (r["data_sha256"] or "")[:16] or "-"
            mark = "!" if r["blocking"] else " "
            extra = ""
            if r.get("on_disk_match") is False:
                extra = "  ON-DISK MISMATCH"
            elif r.get("on_disk_match") is True:
                extra = "  on-disk ok"
            print(f"{r['run_id']:<{width}}  {sha:<16}  {mark}{r['build']:<25}  "
                  f"{r['status']}{extra}")
        unknown = [r for r in rows if r["build"] == "UNKNOWN"]
        if unknown:
            print(f"\n{len(unknown)} record(s) carry a sha absent from the table; "
                  f"add them to {args.table.name} once their build is identified.")
        if failures:
            print("\nBLOCKING:")
            for f in failures:
                print(f"  - {f}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
