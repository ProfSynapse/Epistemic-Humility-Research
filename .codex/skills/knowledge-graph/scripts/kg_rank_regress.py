#!/usr/bin/env python3
"""Ranking regression harness for the KG search scorer.

Runs every case in `tests/ranking_regressions.yaml` against the live index and
asserts the expected note lands within its declared top-k band. Any change to
the scoring path in `kg_search.py` must leave this green.

    python3 .skills/knowledge-graph/scripts/kg_rank_regress.py
    python3 .skills/knowledge-graph/scripts/kg_rank_regress.py --save before.json
    python3 .skills/knowledge-graph/scripts/kg_rank_regress.py --compare before.json

Exit code is 1 if any case fails, so it can gate a commit hook or CI step.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import yaml

from kg_index import DEFAULT_DB, REPO_ROOT, connect
from kg_search import search

DEFAULT_SPEC = Path(__file__).resolve().parent.parent / "tests" / "ranking_regressions.yaml"
# Match the `bin/search` default. The FTS seed set is sized off `limit`, so a
# different probe limit exercises a different graph expansion and would measure
# a ranking nobody actually sees.
PROBE_LIMIT = 10


def resolve_node_path(conn: sqlite3.Connection, node_id: str) -> str | None:
    row = conn.execute("SELECT path FROM nodes WHERE node_id = ? LIMIT 1", (node_id,)).fetchone()
    return str(row["path"]) if row else None


def expected_paths(conn: sqlite3.Connection, case: dict) -> list[str]:
    wanted: list[str] = []
    if case.get("expect"):
        wanted.append(str(case["expect"]))
    for item in case.get("expect_any", []) or []:
        wanted.append(str(item))
    if case.get("expect_node"):
        path = resolve_node_path(conn, str(case["expect_node"]))
        if path is None:
            raise SystemExit(
                f"case {case.get('id')!r}: expect_node {case['expect_node']!r} is not in the index. "
                "Reindex with kg_index.py, or fix the spec."
            )
        wanted.append(path)
    if not wanted:
        raise SystemExit(f"case {case.get('id')!r}: needs one of expect / expect_any / expect_node")
    return wanted


def rank_of(results, wanted: list[str]) -> tuple[int | None, str]:
    """First 1-based rank whose path matches any wanted path fragment."""
    for idx, item in enumerate(results, start=1):
        for target in wanted:
            if target in item.path:
                return idx, item.path
    return None, ""


def run_case(conn: sqlite3.Connection, db_path: Path, case: dict, probe_limit: int) -> dict:
    wanted = expected_paths(conn, case)
    results = search(db_path, str(case["query"]), limit=probe_limit)
    rank, hit_path = rank_of(results, wanted)
    within = int(case.get("within_top_k", 5))
    kind = str(case.get("kind", "guard"))
    met = rank is not None and rank <= within
    return {
        "id": str(case.get("id", case["query"])),
        "kind": kind,
        "query": str(case["query"]),
        "expect": wanted,
        "within_top_k": within,
        "rank": rank,
        "hit_path": hit_path,
        "top1": results[0].path if results else "",
        "note": str(case.get("note", "")).strip(),
        # A `blocked` case records a query the ranker cannot satisfy because the
        # target note lacks the query's vocabulary. It is reported, never
        # silently dropped, but it does not gate the suite - the fix belongs in
        # the note, not the scorer.
        "passed": met or kind == "blocked",
        "met": met,
    }


def format_table(rows: list[dict], baseline: dict[str, dict] | None = None) -> str:
    header = f"{'':1} {'case':<34} {'k':>2} {'rank':>5}"
    if baseline is not None:
        header += f" {'was':>5} {'move':>6}"
    lines = [header, "-" * len(header)]
    for row in rows:
        if row["kind"] == "blocked":
            mark = "~"
        else:
            mark = "." if row["passed"] else "X"
        rank = str(row["rank"]) if row["rank"] is not None else "MISS"
        line = f"{mark} {row['id']:<34} {row['within_top_k']:>2} {rank:>5}"
        if baseline is not None:
            prior = baseline.get(row["id"])
            was = "-"
            move = "-"
            if prior is not None:
                was = str(prior["rank"]) if prior["rank"] is not None else "MISS"
                if prior["rank"] is None and row["rank"] is None:
                    move = "same"
                elif prior["rank"] is None:
                    move = "new"
                elif row["rank"] is None:
                    move = "lost"
                else:
                    delta = prior["rank"] - row["rank"]
                    move = "same" if delta == 0 else f"{delta:+d}"
            line += f" {was:>5} {move:>6}"
        lines.append(line)
    failures = [row for row in rows if not row["passed"]]
    blocked = [row for row in rows if row["kind"] == "blocked"]
    lines.append("")
    lines.append(f"{len(rows) - len(failures) - len(blocked)}/{len(rows) - len(blocked)} passed")
    for row in blocked:
        state = "now ranks" if row["met"] else "still unreachable"
        lines.append(f"  ~ BLOCKED {row['id']}: {row['query']!r} ({state})")
        if row["note"]:
            lines.append(f"       {row['note']}")
    for row in failures:
        lines.append(f"  FAIL {row['id']}: {row['query']!r}")
        lines.append(f"       want {row['expect']} within top {row['within_top_k']}, got rank {row['rank']}")
        lines.append(f"       top1 was {row['top1']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KG search ranking regressions.")
    parser.add_argument("--spec", default=str(DEFAULT_SPEC), help="Ranking spec YAML.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite index path.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root (unused; kept for symmetry).")
    parser.add_argument("--probe-limit", type=int, default=PROBE_LIMIT, help="Results fetched per query.")
    parser.add_argument("--save", help="Write results to this JSON file (use to record a BEFORE table).")
    parser.add_argument("--compare", help="Compare against a JSON file written by --save.")
    parser.add_argument("--only", help="Run only cases whose id contains this substring.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table.")
    args = parser.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
    cases = spec.get("cases", [])
    if args.only:
        cases = [case for case in cases if args.only in str(case.get("id", ""))]
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 1

    db_path = Path(args.db)
    conn = connect(db_path)
    try:
        rows = [run_case(conn, db_path, case, args.probe_limit) for case in cases]
    finally:
        conn.close()

    baseline = None
    if args.compare:
        prior = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        baseline = {row["id"]: row for row in prior}

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(format_table(rows, baseline))

    if args.save:
        Path(args.save).write_text(json.dumps(rows, indent=2), encoding="utf-8")

    return 0 if all(row["passed"] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
