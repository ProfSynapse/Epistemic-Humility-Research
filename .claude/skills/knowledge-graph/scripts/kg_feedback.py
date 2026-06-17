#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from kg_index import DEFAULT_DB, connect

VALID_EVENTS = ("read", "open", "edit", "test_pass", "test_fail", "requery")


def latest_search_id(conn: sqlite3.Connection, query: str) -> int | None:
    row = conn.execute(
        """
        SELECT id
        FROM search_log
        WHERE query = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (query,),
    ).fetchone()
    return int(row["id"]) if row else None


def record_feedback(
    db_path: Path,
    event_type: str,
    path: str,
    *,
    search_id: int | None = None,
    query: str | None = None,
    success: bool | None = None,
    command: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if event_type not in VALID_EVENTS:
        raise ValueError(f"unsupported event_type {event_type!r}; expected one of {', '.join(VALID_EVENTS)}")
    if not path:
        raise ValueError("path is required")
    if search_id is None and not query:
        raise ValueError("provide either search_id or query")

    conn = connect(db_path)
    try:
        if search_id is None and query is not None:
            search_id = latest_search_id(conn, query)
            if search_id is None:
                raise ValueError(f"no logged search found for query: {query}")
        success_value = None if success is None else int(success)
        cur = conn.execute(
            """
            INSERT INTO feedback_events(
              search_id,
              event_type,
              path,
              command,
              success,
              metadata_json,
              created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                search_id,
                event_type,
                path,
                command,
                success_value,
                json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True),
                time.time(),
            ),
        )
        conn.commit()
        return {
            "feedback_id": int(cur.lastrowid),
            "search_id": search_id,
            "event_type": event_type,
            "path": path,
            "success": success_value,
        }
    finally:
        conn.close()


def parse_metadata(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise argparse.ArgumentTypeError(f"invalid JSON metadata: {exc}") from exc
    if not isinstance(parsed, dict):
        raise argparse.ArgumentTypeError("metadata JSON must be an object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Record KG search feedback for the lane adapter.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite index path. Defaults to .kg/index.sqlite.")
    parser.add_argument("--query", help="Attach feedback to the latest logged search for this exact query.")
    parser.add_argument("--search-id", type=int, help="Attach feedback to a specific search_log id.")
    parser.add_argument("--event", required=True, choices=VALID_EVENTS, help="Feedback event type.")
    parser.add_argument("--path", required=True, help="Repository-relative path used after the search.")
    parser.add_argument("--command", default="", help="Command associated with the event, if any.")
    parser.add_argument("--metadata-json", type=parse_metadata, default={}, help="Optional JSON object metadata.")
    status = parser.add_mutually_exclusive_group()
    status.add_argument("--success", action="store_true", help="Mark the event as successful.")
    status.add_argument("--failure", action="store_true", help="Mark the event as unsuccessful.")
    args = parser.parse_args()

    if args.search_id is not None and args.query:
        print("error: provide --search-id or --query, not both", file=sys.stderr)
        return 2
    success = True if args.success else False if args.failure else None
    try:
        result = record_feedback(
            Path(args.db),
            args.event,
            args.path,
            search_id=args.search_id,
            query=args.query,
            success=success,
            command=args.command,
            metadata=args.metadata_json,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
