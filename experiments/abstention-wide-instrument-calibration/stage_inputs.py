#!/usr/bin/env python3
"""Stages every registered source runlog into this experiment's gitignored
analysis/staged_inputs/<cell>/ tree, and writes the COMMITTED, text-free
staging manifest (AMENDMENT.md "Staging").

Per source, records: cell, arm (and hs_index/dose stratum for QL), source
absolute path, dest relative path, sha256 of the staged bytes, row count.
No question/answer text, no row_key, ever enters the committed manifest --
only counts and hashes.

Run: `python3 stage_inputs.py`
"""

from __future__ import annotations

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sources

HERE = Path(__file__).resolve().parent


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def stage_one(entry: dict[str, Any]) -> dict[str, Any]:
    src = Path(entry["source_path"])
    if not src.is_file():
        raise SystemExit(f"missing source file: {src} (cell={entry['cell']} arm={entry['arm']})")
    dest = sources.staged_path(entry["cell"], entry["dest_name"])
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    row_count = sum(1 for line in dest.open(encoding="utf-8") if line.strip())
    record = {
        "cell": entry["cell"],
        "arm": entry["arm"],
        "hs_index": entry.get("hs_index"),
        "schema": entry["schema"],
        "source_path": str(src),
        "dest_path": str(dest.relative_to(HERE)),
        "sha256": sources.sha256_of_file(dest),
        "row_count": row_count,
    }
    return record


def main() -> int:
    entries = sources.source_manifest()
    records = [stage_one(e) for e in entries]
    manifest = {
        "staged_at": datetime.now(timezone.utc).isoformat(),
        "files": records,
    }
    write_json(sources.COMMITTED / "staging_manifest.json", manifest)
    print(json.dumps({"n_files": len(records), "total_rows": sum(r["row_count"] for r in records)}, indent=2), flush=True)
    for r in records:
        print(f"  {r['cell']:3s} {r['arm']:17s} hs={str(r['hs_index']):4s} n={r['row_count']:6d} sha256={r['sha256'][:8]} <- {r['source_path']}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
