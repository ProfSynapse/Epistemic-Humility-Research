#!/usr/bin/env python3
"""Build exact row-key panels from behavior-labeled mechinterp rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"


class BehaviorPanelRowKeyError(RuntimeError):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (PROBE_DIR / path).resolve()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise BehaviorPanelRowKeyError("config must be a YAML mapping")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise BehaviorPanelRowKeyError(f"missing JSONL file: {rel(path)}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise BehaviorPanelRowKeyError(f"{rel(path)}:{line_number} row is not an object")
            rows.append(row)
    return rows


def row_key(row: dict[str, Any]) -> str:
    key = row.get("row_key") or row.get("probe_pool_row_key")
    if not isinstance(key, str) or not key:
        raise BehaviorPanelRowKeyError("row missing row_key/probe_pool_row_key")
    return key


def read_excluded_keys(paths: list[str]) -> set[str]:
    excluded: set[str] = set()
    for raw in paths:
        path = resolve_path(raw)
        if not path.exists():
            raise BehaviorPanelRowKeyError(f"exclude source missing: {rel(path)}")
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("{"):
                excluded.add(row_key(json.loads(stripped)))
            else:
                excluded.add(stripped)
    return excluded


def select_rows(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inputs = config.get("inputs", {})
    if not isinstance(inputs, dict) or not inputs.get("rows"):
        raise BehaviorPanelRowKeyError("config must define inputs.rows")
    rows_path = resolve_path(inputs["rows"])
    excluded = read_excluded_keys(inputs.get("exclude_row_keys_sources", []))
    quotas = config.get("quotas", {})
    if not isinstance(quotas, dict) or not quotas:
        raise BehaviorPanelRowKeyError("config must define quotas")
    require_quotas = bool(config.get("require_quotas", True))

    buckets: dict[str, list[dict[str, Any]]] = {str(cell): [] for cell in quotas}
    for row in load_jsonl(rows_path):
        key = row_key(row)
        if key in excluded:
            continue
        cell = row.get("behavior_cell")
        if cell in buckets:
            buckets[str(cell)].append(row)

    selected: list[dict[str, Any]] = []
    bucket_summaries: dict[str, dict[str, int]] = {}
    for cell, quota_raw in quotas.items():
        if not isinstance(quota_raw, int) or isinstance(quota_raw, bool) or quota_raw < 0:
            raise BehaviorPanelRowKeyError(f"quota for {cell!r} must be a non-negative integer")
        available = buckets.get(str(cell), [])
        if require_quotas and len(available) < quota_raw:
            raise BehaviorPanelRowKeyError(
                f"cell {cell!r} has {len(available)} rows after exclusions, quota is {quota_raw}"
            )
        take = available[:quota_raw]
        selected.extend({**row, "target_behavior_cell": str(cell)} for row in take)
        bucket_summaries[str(cell)] = {
            "available": len(available),
            "selected": len(take),
            "quota": quota_raw,
        }

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in selected:
        key = row_key(row)
        if key in seen:
            raise BehaviorPanelRowKeyError(f"duplicate selected row key: {key}")
        seen.add(key)
        deduped.append(row)

    manifest = {
        "schema_version": "mechinterp-behavior-panel-row-keys/v1",
        "purpose": config.get("purpose"),
        "inputs": {
            "rows": rel(rows_path),
            "rows_sha256": file_sha256(rows_path),
            "excluded_source_count": len(excluded),
        },
        "quotas": quotas,
        "bucket_summaries": bucket_summaries,
        "total_selected": len(deduped),
        "selected_label_counts": dict(Counter(str(row.get("label")) for row in deduped)),
        "selected_behavior_cell_counts": dict(
            Counter(str(row.get("target_behavior_cell")) for row in deduped)
        ),
    }
    return deduped, manifest


def write_outputs(config: dict[str, Any], rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[Path, Path, Path]:
    output = config.get("output", {})
    for key in ("row_keys_file", "rows_jsonl", "manifest"):
        if not isinstance(output.get(key), str):
            raise BehaviorPanelRowKeyError(f"config must define output.{key}")
    row_keys_path = resolve_path(output["row_keys_file"])
    rows_path = resolve_path(output["rows_jsonl"])
    manifest_path = resolve_path(output["manifest"])
    row_keys_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    row_keys_path.write_text("".join(f"{row_key(row)}\n" for row in rows), encoding="utf-8")
    with rows_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return row_keys_path, rows_path, manifest_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    rows, manifest = select_rows(config)
    row_keys_path, rows_path, manifest_path = write_outputs(config, rows, manifest)
    print(f"selected {len(rows)} row keys")
    print(f"wrote {rel(row_keys_path)}")
    print(f"wrote {rel(rows_path)}")
    print(f"wrote {rel(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
