#!/usr/bin/env python3
"""Aggregate Phase 3 logit diagnostics by behavior cell."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_sae_behavior_feature_analysis import row_matches_filter
from phase3_sae_smoke import repo_relative, resolve_path


ANALYSIS_TYPE = "phase3_logit_cell_analysis"
NOTICE = "LOGIT_CELL_ANALYSIS_ONLY"


class LogitCellAnalysisError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise LogitCellAnalysisError(f"{repo_relative(path)} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def load_rows(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if not isinstance(key, str) or not key:
                raise LogitCellAnalysisError(f"{repo_relative(path)}:{line_number} missing probe_pool_row_key")
            if key in rows:
                raise LogitCellAnalysisError(f"{repo_relative(path)}:{line_number} duplicate row key {key!r}")
            rows[key] = row
    if not rows:
        raise LogitCellAnalysisError(f"{repo_relative(path)} contained no rows")
    return rows


def parse_behavior_cells(config: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    behavior_cells = config.get("behavior_cells")
    if not isinstance(behavior_cells, dict):
        raise LogitCellAnalysisError("config must define behavior_cells")
    cells = behavior_cells.get("cells")
    if not isinstance(cells, list) or not cells:
        raise LogitCellAnalysisError("behavior_cells.cells must be a non-empty list")
    for cell in cells:
        if not isinstance(cell, dict):
            raise LogitCellAnalysisError("behavior_cells.cells entries must be mappings")
        if not isinstance(cell.get("label"), str) or not cell["label"]:
            raise LogitCellAnalysisError("each behavior cell must define label")
        if not isinstance(cell.get("filter"), dict):
            raise LogitCellAnalysisError(f"behavior cell {cell.get('label')!r} must define filter")
    fallback = behavior_cells.get("fallback_cell", "other")
    if not isinstance(fallback, str) or not fallback:
        raise LogitCellAnalysisError("behavior_cells.fallback_cell must be a non-empty string")
    return cells, fallback


def classify_row(row: dict[str, Any], *, arm: str, cells: list[dict[str, Any]], fallback: str) -> str:
    for cell in cells:
        if row_matches_filter(row, arm, cell["filter"]):
            return str(cell["label"])
    return fallback


def run_specs(config: dict[str, Any]) -> list[dict[str, Any]]:
    runs = config.get("runs")
    if isinstance(runs, list) and runs:
        out = []
        for index, run in enumerate(runs):
            if not isinstance(run, dict):
                raise LogitCellAnalysisError("runs entries must be mappings")
            path = run.get("diagnostics")
            if not isinstance(path, str) or not path:
                raise LogitCellAnalysisError(f"runs[{index}] must define diagnostics")
            label = run.get("label") or Path(path).parents[2].name
            if not isinstance(label, str) or not label:
                raise LogitCellAnalysisError(f"runs[{index}] label must be non-empty")
            out.append({"label": label, "path": resolve_path(path)})
        return out

    diagnostics_glob = config.get("diagnostics_glob")
    if not isinstance(diagnostics_glob, str) or not diagnostics_glob:
        raise LogitCellAnalysisError("config must define runs or diagnostics_glob")
    matches = sorted(resolve_path(".").glob(diagnostics_glob))
    if not matches:
        raise LogitCellAnalysisError(f"diagnostics_glob matched no files: {diagnostics_glob}")
    return [{"label": path.parents[2].name, "path": path} for path in matches]


def mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def pct(count: int, total: int) -> float:
    return round(100.0 * count / total, 6) if total else 0.0


def aggregate_rows(
    *,
    rows_by_key: dict[str, dict[str, Any]],
    runs: list[dict[str, Any]],
    arm: str,
    cells: list[dict[str, Any]],
    fallback: str,
    target_group: str,
) -> list[dict[str, Any]]:
    buckets: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for run in runs:
        path = Path(run["path"])
        with path.open(encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                row_key = row.get("probe_pool_row_key")
                source_row = rows_by_key.get(row_key)
                if source_row is None:
                    raise LogitCellAnalysisError(f"{repo_relative(path)}:{line_number} unknown row key {row_key!r}")
                target_metrics = row.get("logit_target_metrics", {}).get(target_group)
                if not isinstance(target_metrics, dict):
                    continue
                cell = classify_row(source_row, arm=arm, cells=cells, fallback=fallback)
                key = (
                    run["label"],
                    row.get("candidate_label"),
                    row.get("grid_coefficient"),
                    row.get("control"),
                    cell,
                )
                buckets.setdefault(key, []).append({**row, "_target": target_metrics})

    out: list[dict[str, Any]] = []
    for (run_label, candidate_label, coefficient, control, cell), items in sorted(buckets.items()):
        deltas = [float(item["_target"]["probability_sum_delta"]) for item in items]
        logit_deltas = [float(item["_target"]["logit_sum_delta"]) for item in items]
        out.append(
            {
                "analysis_type": ANALYSIS_TYPE,
                "notice": NOTICE,
                "run_label": run_label,
                "candidate_label": candidate_label,
                "grid_coefficient": coefficient,
                "control": control,
                "behavior_cell": cell,
                "target_group": target_group,
                "row_count": len(items),
                "probability_sum_delta_mean": mean(deltas),
                "probability_sum_delta_abs_mean": mean([abs(value) for value in deltas]),
                "logit_sum_delta_mean": mean(logit_deltas),
                "top1_changed_rate": pct(sum(bool(item.get("top1_changed")) for item in items), len(items)),
                "intervention_applied_count_total": sum(
                    int(item.get("intervention_applied_count", 0)) for item in items
                ),
            }
        )
    return out


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    source_rows = config.get("source_rows")
    behavior_arm = config.get("behavior_arm")
    output = config.get("output")
    target_group = config.get("target_group", "refusal_openers")
    if not isinstance(source_rows, str) or not source_rows:
        raise LogitCellAnalysisError("config must define source_rows")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise LogitCellAnalysisError("config must define behavior_arm")
    if not isinstance(target_group, str) or not target_group:
        raise LogitCellAnalysisError("target_group must be a non-empty string")
    if not isinstance(output, dict) or not output.get("root"):
        raise LogitCellAnalysisError("config must define output.root")

    cells, fallback = parse_behavior_cells(config)
    rows_by_key = load_rows(resolve_path(source_rows))
    runs = run_specs(config)
    summary_rows = aggregate_rows(
        rows_by_key=rows_by_key,
        runs=runs,
        arm=behavior_arm,
        cells=cells,
        fallback=fallback,
        target_group=target_group,
    )
    output_root = resolve_path(output["root"])
    csv_path = output_root / "cell_logit_summary.csv"
    summary_path = output_root / "summary.json"
    write_csv(csv_path, summary_rows)
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "behavior_arm": behavior_arm,
        "target_group": target_group,
        "run_count": len(runs),
        "summary_row_count": len(summary_rows),
        "output_root": repo_relative(output_root),
        "outputs": {
            "cell_logit_summary": repo_relative(csv_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except LogitCellAnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
