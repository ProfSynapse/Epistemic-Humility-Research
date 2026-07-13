#!/usr/bin/env python3
"""Aggregate completed mechinterp causal-pilot sweep run manifests."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"


class AggregateError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise AggregateError(f"{path} did not load to a JSON object")
    return payload


def resolve_manifest_output_path(path_text: str) -> Path:
    docker_prefix = "/workspace/repo/"
    if path_text.startswith(docker_prefix):
        container_path = Path(path_text)
        if container_path.exists():
            return container_path
        return (REPO_ROOT / path_text[len(docker_prefix):]).resolve()
    return Path(path_text)


def _read_metric_file(path_text: str | None) -> dict[str, Any]:
    if not path_text:
        return {}
    path = resolve_manifest_output_path(path_text)
    if not path.is_file():
        return {}
    return load_json(path)


def _rows_from_metrics(manifest_path: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    candidate = manifest.get("candidate", {})
    outputs = manifest.get("outputs", {})
    metrics = _read_metric_file(outputs.get("metrics") or outputs.get("logit_metrics"))
    rows: list[dict[str, Any]] = []
    for arm_id, values in metrics.items():
        if not isinstance(values, dict):
            continue
        row = {
            "manifest": str(manifest_path),
            "output_root": str(manifest_path.parent),
            "mode": "logit_diagnostic"
            if manifest.get("logit_diagnostic_executed")
            else "generation",
            "candidate_label": candidate.get("label"),
            "candidate_direction_id": candidate.get("direction_id"),
            "candidate_role": candidate.get("role"),
            "candidate_layer": candidate.get("layer"),
            "arm_id": arm_id,
            "row_count": manifest.get("row_count"),
            "arm_count": manifest.get("arm_count"),
            "config_sha": manifest.get("config_sha"),
        }
        row.update(values)
        rows.append(row)
    return rows


def collect_rows(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        raise AggregateError(f"aggregate root does not exist: {root}")
    rows: list[dict[str, Any]] = []
    for manifest_path in sorted(root.rglob("run_manifest.json")):
        manifest = load_json(manifest_path)
        rows.extend(_rows_from_metrics(manifest_path, manifest))
    return rows


def _flatten(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    if value is None:
        return ""
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _flatten(row.get(key)) for key in fieldnames})


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--out", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        rows = collect_rows(args.root)
        result = {"root": str(args.root.resolve()), "rows": rows, "row_count": len(rows)}
        if args.out:
            write_csv(args.out, rows)
            result["out"] = str(args.out.resolve())
        print(json.dumps(result, indent=2, sort_keys=True))
    except AggregateError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
