#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from kg_index import DEFAULT_DB, connect, index_root

TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,}")
DATA_QUERY_TERMS = {
    "column",
    "columns",
    "csv",
    "data",
    "dataset",
    "datasets",
    "fixture",
    "fixtures",
    "gold",
    "jsonl",
    "record",
    "records",
    "row",
    "rows",
    "sample",
    "schema",
}


@dataclass
class SearchResult:
    path: str
    kind: str
    title: str
    symbol: str
    symbol_type: str
    start_line: int
    end_line: int
    score: float
    snippet: str
    neighbors: list[str]


EDGE_WEIGHTS = {
    "contains": 2.0,
    "defined_in": 2.0,
    "contains_key": 2.0,
    "references_path": 2.5,
    "calls": 1.5,
    "imports": 1.0,
    "describes": 2.0,
    "uses": 1.25,
    "proposes": 1.25,
    "supports": 1.25,
    "supported_by": 1.25,
    "evaluates_on": 1.25,
    "measures": 1.25,
    "studies": 1.25,
}


def fts_phrase(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def build_match_query(query: str, mode: str = "and") -> str:
    tokens = TOKEN_RE.findall(query)
    if not tokens:
        return fts_phrase(query)
    op = " AND " if mode == "and" else " OR "
    return op.join(fts_phrase(token) for token in tokens[:12])


def clean_snippet(value: str, limit: int = 420) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if len(text) > limit:
        return text[: limit - 3].rstrip() + "..."
    return text


def exact_boost(row: sqlite3.Row, query: str) -> float:
    q = query.casefold()
    query_tokens = TOKEN_RE.findall(q)
    haystacks = [
        str(row["path"]).casefold(),
        str(row["title"]).casefold(),
        str(row["symbol"]).casefold(),
    ]
    boost = 0.0
    path = haystacks[0]
    title = haystacks[1]
    symbol = haystacks[2]
    if q and q in symbol:
        boost += 14.0
    elif q and q in title:
        boost += 10.0
    elif q and q in path:
        boost += 8.0
    for token in query_tokens:
        if token == symbol or symbol.endswith("." + token):
            boost += 8.0
        elif token in symbol:
            boost += 4.0
        elif token in title:
            boost += 2.0
        elif token in path:
            boost += 1.5
    if row["kind"] in {"python", "config", "kg_note"}:
        boost += 0.5
    if row["symbol_type"] in {"code_function", "code_class", "config_keys"}:
        boost += 1.0
    skill_or_agent = path.startswith(".agents/skills/")
    skill_terms = {"skill", "runbook", "agent", "matrix", "prereq", "lane", "pact"}
    if skill_or_agent and not any(token in skill_terms for token in query_tokens):
        boost -= 4.0
    return boost


def final_rank_adjustment(row: sqlite3.Row, query: str) -> float:
    query_tokens = set(TOKEN_RE.findall(query.casefold()))
    if query_tokens & DATA_QUERY_TERMS:
        return 0.0
    path = str(row["path"]).casefold()
    suffix = Path(path).suffix
    if row["kind"] in {"data", "data_fixture"} or row["symbol_type"] in {"data_metadata"}:
        return -22.0
    if "/fixtures/" in path and suffix in {".json", ".jsonl", ".csv"}:
        return -18.0
    return 0.0


def graph_neighbors(conn: sqlite3.Connection, path: str, limit: int = 8) -> list[str]:
    node_rows = conn.execute("SELECT node_id FROM nodes WHERE path = ? LIMIT 20", (path,)).fetchall()
    node_ids = [row["node_id"] for row in node_rows]
    if not node_ids:
        return []
    placeholders = ",".join("?" for _ in node_ids)
    rows = conn.execute(
        f"""
        SELECT edge_type, source_id, target_id
        FROM edges
        WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
        LIMIT ?
        """,
        [*node_ids, *node_ids, limit],
    ).fetchall()
    out = []
    for row in rows:
        out.append(f"{row['source_id']} -[{row['edge_type']}]-> {row['target_id']}")
    return out


def seed_node_scores(conn: sqlite3.Connection, query: str, limit: int = 25) -> dict[str, float]:
    q = query.casefold()
    if not q:
        return {}
    tokens = TOKEN_RE.findall(q)
    rows = conn.execute(
        """
        SELECT node_id, path, label, node_type
        FROM nodes
        WHERE lower(node_id) LIKE ? OR lower(path) LIKE ? OR lower(label) LIKE ?
        LIMIT ?
        """,
        (f"%{q}%", f"%{q}%", f"%{q}%", limit),
    ).fetchall()
    scores: dict[str, float] = {}
    for row in rows:
        hay = " ".join(str(row[key]).casefold() for key in ("node_id", "path", "label", "node_type"))
        scores[row["node_id"]] = 6.0 + sum(1.0 for token in tokens if token in hay)
    return scores


def path_for_node(conn: sqlite3.Connection, node_id: str) -> str | None:
    if node_id.startswith("external:"):
        return None
    row = conn.execute("SELECT path FROM nodes WHERE node_id = ?", (node_id,)).fetchone()
    if row:
        return str(row["path"])
    if node_id.startswith("file:"):
        return node_id[5:]
    return None


def expand_graph(
    conn: sqlite3.Connection,
    seed_paths: dict[str, float],
    seed_nodes: dict[str, float],
    depth: int,
) -> dict[str, float]:
    frontier: dict[str, float] = dict(seed_nodes)
    for path, score in seed_paths.items():
        rows = conn.execute("SELECT node_id FROM nodes WHERE path = ? LIMIT 50", (path,)).fetchall()
        for row in rows:
            if str(row["node_id"]).startswith("external:"):
                continue
            frontier[row["node_id"]] = max(frontier.get(row["node_id"], 0.0), score)

    path_scores: dict[str, float] = dict(seed_paths)
    seen = set(frontier)
    for step in range(max(0, depth)):
        if not frontier:
            break
        placeholders = ",".join("?" for _ in frontier)
        rows = conn.execute(
            f"""
            SELECT source_id, target_id, edge_type
            FROM edges
            WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
            """,
            [*frontier, *frontier],
        ).fetchall()
        next_frontier: dict[str, float] = {}
        decay = 1.0 / (step + 2)
        for row in rows:
            src = row["source_id"]
            dst = row["target_id"]
            base = max(frontier.get(src, 0.0), frontier.get(dst, 0.0))
            score = base + EDGE_WEIGHTS.get(row["edge_type"], 0.75) * decay
            for node_id in (src, dst):
                path = path_for_node(conn, node_id)
                if path:
                    path_scores[path] = max(path_scores.get(path, 0.0), score)
                if node_id.startswith("external:"):
                    continue
                if node_id not in seen:
                    seen.add(node_id)
                    next_frontier[node_id] = max(next_frontier.get(node_id, 0.0), score)
        frontier = next_frontier
    return path_scores


def best_chunk_for_path(conn: sqlite3.Connection, path: str, query: str = "") -> sqlite3.Row | None:
    tokens = TOKEN_RE.findall(query.casefold())
    rows = conn.execute(
        """
        SELECT id, path, kind, title, symbol, symbol_type, start_line, end_line, text, 0.0 AS bm25_score
        FROM chunks
        WHERE path = ?
        """,
        (path,),
    ).fetchall()
    if not rows:
        return None

    def chunk_score(row: sqlite3.Row) -> tuple[float, int]:
        hay_symbol = str(row["symbol"]).casefold()
        hay_title = str(row["title"]).casefold()
        score = 0.0
        for token in tokens:
            if token == hay_symbol or hay_symbol.endswith("." + token):
                score += 20.0
            elif token in hay_symbol:
                score += 8.0
            elif token in hay_title:
                score += 4.0
        if row["symbol_type"] == "file":
            score -= 2.0
        return score, int(row["end_line"]) - int(row["start_line"])

    return max(rows, key=chunk_score)


def first_chunk_for_path(conn: sqlite3.Connection, path: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, path, kind, title, symbol, symbol_type, start_line, end_line, text, 0.0 AS bm25_score
        FROM chunks
        WHERE path = ?
        ORDER BY
          CASE symbol_type
            WHEN 'file' THEN 2
            WHEN 'section' THEN 1
            ELSE 0
          END,
          length(text) DESC
        LIMIT 1
        """,
        (path,),
    ).fetchone()


def search(db_path: Path, query: str, limit: int = 10, traverse_depth: int = 2) -> list[SearchResult]:
    conn = connect(db_path)
    try:
        candidates: dict[int, sqlite3.Row] = {}
        scores: dict[int, float] = {}
        seed_paths: dict[str, float] = {}
        for mode in ("and", "or"):
            match_query = build_match_query(query, mode=mode)
            rows = conn.execute(
                """
                SELECT
                  chunks.id,
                  chunks.path,
                  chunks.kind,
                  chunks.title,
                  chunks.symbol,
                  chunks.symbol_type,
                  chunks.start_line,
                  chunks.end_line,
                  chunks.text,
                  bm25(chunks_fts) AS bm25_score
                FROM chunks_fts
                JOIN chunks ON chunks.id = chunks_fts.rowid
                WHERE chunks_fts MATCH ?
                ORDER BY bm25_score
                LIMIT ?
                """,
                (match_query, max(limit * 4, 20)),
            ).fetchall()
            for row in rows:
                rowid = int(row["id"])
                # bm25 is lower-is-better and often negative. Convert to a simple
                # higher-is-better score, then add deterministic structural boosts.
                score = -float(row["bm25_score"]) + exact_boost(row, query) + final_rank_adjustment(row, query)
                if rowid not in scores or score > scores[rowid]:
                    scores[rowid] = score
                    candidates[rowid] = row
                seed_paths[row["path"]] = max(seed_paths.get(row["path"], 0.0), score)
            if candidates:
                break

        seed_nodes = seed_node_scores(conn, query)
        for node_id, score in seed_nodes.items():
            path = path_for_node(conn, node_id)
            if path:
                seed_paths[path] = max(seed_paths.get(path, 0.0), score)

        graph_scores = expand_graph(conn, seed_paths, seed_nodes, traverse_depth)
        for path, graph_score in graph_scores.items():
            row = best_chunk_for_path(conn, path, query)
            if row is None:
                continue
            rowid = int(row["id"])
            score = scores.get(rowid, graph_score + final_rank_adjustment(row, query)) + graph_score
            if rowid not in scores or score > scores[rowid]:
                scores[rowid] = score
                candidates[rowid] = row

        ranked = sorted(candidates.values(), key=lambda row: scores[int(row["id"])], reverse=True)[:limit]
        results = []
        for row in ranked:
            results.append(
                SearchResult(
                    path=row["path"],
                    kind=row["kind"],
                    title=row["title"],
                    symbol=row["symbol"],
                    symbol_type=row["symbol_type"],
                    start_line=int(row["start_line"]),
                    end_line=int(row["end_line"]),
                    score=round(scores[int(row["id"])], 4),
                    snippet=clean_snippet(row["text"]),
                    neighbors=graph_neighbors(conn, row["path"]),
                )
            )
        conn.execute(
            "INSERT INTO search_log(query, results_json, created_at) VALUES (?, ?, ?)",
            (query, json.dumps([asdict(item) for item in results], ensure_ascii=False), time.time()),
        )
        conn.commit()
        return results
    finally:
        conn.close()


def format_results(results: list[SearchResult], query: str) -> str:
    if not results:
        return f"No indexed matches for: {query}"
    lines = [f"KG search results for: {query}", ""]
    paths: list[str] = []
    for idx, item in enumerate(results, start=1):
        loc = f"{item.path}:{item.start_line}" if item.start_line else item.path
        lines.append(f"{idx}. {loc} [{item.kind}/{item.symbol_type}] score={item.score}")
        lines.append(f"   {item.title}")
        if item.snippet:
            lines.append(f"   {item.snippet}")
        if item.neighbors:
            lines.append("   graph:")
            for neighbor in item.neighbors[:3]:
                lines.append(f"   - {neighbor}")
        lines.append("")
        if item.path not in paths:
            paths.append(item.path)
    scoped = " ".join(json.dumps(path) for path in paths[:6])
    lines.append("Scoped fallback:")
    lines.append(f"  rg -n {json.dumps(query)} {scoped}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search the local code/config/research KG index.")
    parser.add_argument("query", help="Search query.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite index path. Defaults to .kg/index.sqlite.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results to show.")
    parser.add_argument("--traverse-depth", type=int, default=2, help="Graph traversal depth from seed files/nodes.")
    parser.add_argument("--no-update", action="store_true", help="Skip lazy changed-file indexing before search.")
    parser.add_argument("--json", action="store_true", help="Emit JSON results.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    db_path = Path(args.db)
    if not args.no_update:
        try:
            index_root(root, db_path)
        except FileNotFoundError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
    results = search(db_path, args.query, limit=args.limit, traverse_depth=args.traverse_depth)
    if args.json:
        print(json.dumps([asdict(item) for item in results], ensure_ascii=False, indent=2))
    else:
        print(format_results(results, args.query))
    return 0


if __name__ == "__main__":
    sys.exit(main())
