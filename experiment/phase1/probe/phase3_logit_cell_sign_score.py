#!/usr/bin/env python3
"""Rank logit-cell diagnostics against declared behavior-cell sign goals."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from phase3_sae_smoke import repo_relative, resolve_path


ANALYSIS_TYPE = "phase3_logit_cell_sign_score"
NOTICE = "LOGIT_CELL_SIGN_SCORE_ONLY"
DEFAULT_GROUP_BY = ["run_label", "candidate_label", "grid_coefficient", "control", "target_group"]
VALID_MODES = {"increase", "decrease", "preserve_nonpositive", "preserve_nonnegative"}


class LogitCellSignScoreError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise LogitCellSignScoreError(f"{repo_relative(path)} did not load to a YAML object")
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def parse_inputs(config: dict[str, Any]) -> list[dict[str, Any]]:
    inputs = config.get("input_summaries")
    if isinstance(inputs, list) and inputs:
        out = []
        for index, item in enumerate(inputs):
            if not isinstance(item, dict):
                raise LogitCellSignScoreError("input_summaries entries must be mappings")
            path = item.get("path")
            if not isinstance(path, str) or not path:
                raise LogitCellSignScoreError(f"input_summaries[{index}] must define path")
            label = item.get("label") or Path(path).parents[1].name
            if not isinstance(label, str) or not label:
                raise LogitCellSignScoreError(f"input_summaries[{index}] label must be non-empty")
            out.append({"label": label, "path": resolve_path(path)})
        return out

    summary_glob = config.get("summary_glob")
    if not isinstance(summary_glob, str) or not summary_glob:
        raise LogitCellSignScoreError("config must define input_summaries or summary_glob")
    matches = sorted(resolve_path(".").glob(summary_glob))
    if not matches:
        raise LogitCellSignScoreError(f"summary_glob matched no files: {summary_glob}")
    return [{"label": path.parents[1].name, "path": path} for path in matches]


def parse_goals(config: dict[str, Any]) -> list[dict[str, Any]]:
    score = config.get("score")
    if not isinstance(score, dict):
        raise LogitCellSignScoreError("config must define score")
    goals = score.get("cell_goals")
    if not isinstance(goals, list) or not goals:
        raise LogitCellSignScoreError("score.cell_goals must be a non-empty list")
    out = []
    for index, goal in enumerate(goals):
        if not isinstance(goal, dict):
            raise LogitCellSignScoreError("score.cell_goals entries must be mappings")
        cell = goal.get("behavior_cell")
        mode = goal.get("mode")
        if not isinstance(cell, str) or not cell:
            raise LogitCellSignScoreError(f"score.cell_goals[{index}] must define behavior_cell")
        if mode not in VALID_MODES:
            raise LogitCellSignScoreError(
                f"score.cell_goals[{index}] mode must be one of {sorted(VALID_MODES)}"
            )
        weight = goal.get("weight", 1.0)
        try:
            weight_float = float(weight)
        except (TypeError, ValueError) as exc:
            raise LogitCellSignScoreError(f"score.cell_goals[{index}] weight must be numeric") from exc
        out.append({"behavior_cell": cell, "mode": mode, "weight": weight_float})
    return out


def goal_contribution(value: float, *, mode: str) -> tuple[float, bool]:
    if mode == "increase":
        return value, value > 0.0
    if mode == "decrease":
        return -value, value < 0.0
    if mode == "preserve_nonpositive":
        return -max(value, 0.0), value <= 0.0
    if mode == "preserve_nonnegative":
        return min(value, 0.0), value >= 0.0
    raise LogitCellSignScoreError(f"unsupported goal mode {mode!r}")


def group_rows(
    *,
    inputs: list[dict[str, Any]],
    group_by: list[str],
    target_metric: str,
) -> dict[tuple[Any, ...], dict[str, Any]]:
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for input_spec in inputs:
        path = Path(input_spec["path"])
        for row_number, row in enumerate(read_csv_rows(path), start=2):
            cell = row.get("behavior_cell")
            if not cell:
                raise LogitCellSignScoreError(f"{repo_relative(path)}:{row_number} missing behavior_cell")
            if target_metric not in row:
                raise LogitCellSignScoreError(f"{repo_relative(path)}:{row_number} missing {target_metric}")
            key_parts = [input_spec["label"]]
            for field in group_by:
                if field not in row:
                    raise LogitCellSignScoreError(f"{repo_relative(path)}:{row_number} missing {field}")
                key_parts.append(row[field])
            key = tuple(key_parts)
            group = groups.setdefault(
                key,
                {
                    "input_label": input_spec["label"],
                    **{field: row[field] for field in group_by},
                    "cells": {},
                    "cell_row_counts": {},
                },
            )
            try:
                value = float(row[target_metric])
            except ValueError as exc:
                raise LogitCellSignScoreError(
                    f"{repo_relative(path)}:{row_number} {target_metric} is not numeric"
                ) from exc
            group["cells"][cell] = value
            if "row_count" in row:
                group["cell_row_counts"][cell] = row["row_count"]
    return groups


def score_groups(
    *,
    groups: dict[tuple[Any, ...], dict[str, Any]],
    goals: list[dict[str, Any]],
    target_metric: str,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for group in groups.values():
        score = 0.0
        passed = 0
        missing: list[str] = []
        cell_values: dict[str, float | None] = {}
        cell_passes: dict[str, bool | None] = {}
        for goal in goals:
            cell = goal["behavior_cell"]
            value = group["cells"].get(cell)
            cell_values[cell] = value
            if value is None:
                missing.append(cell)
                cell_passes[cell] = None
                continue
            contribution, is_pass = goal_contribution(value, mode=goal["mode"])
            score += goal["weight"] * contribution
            passed += int(is_pass)
            cell_passes[cell] = is_pass
        out = {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "input_label": group["input_label"],
            "run_label": group.get("run_label", ""),
            "candidate_label": group.get("candidate_label", ""),
            "grid_coefficient": group.get("grid_coefficient", ""),
            "control": group.get("control", ""),
            "target_group": group.get("target_group", ""),
            "target_metric": target_metric,
            "sign_score": score,
            "passed_goal_count": passed,
            "goal_count": len(goals),
            "all_goals_passed": passed == len(goals) and not missing,
            "missing_goal_cells": ";".join(missing),
        }
        for goal in goals:
            cell = goal["behavior_cell"]
            safe = cell.replace("-", "_")
            out[f"{safe}_value"] = cell_values[cell]
            out[f"{safe}_passed"] = cell_passes[cell]
            out[f"{safe}_row_count"] = group["cell_row_counts"].get(cell, "")
        scored.append(out)
    scored.sort(key=lambda row: (float(row["sign_score"]), int(row["passed_goal_count"])), reverse=True)
    for index, row in enumerate(scored, start=1):
        row["rank"] = index
    if scored:
        keys = ["rank"] + [key for key in scored[0].keys() if key != "rank"]
        return [{key: row.get(key, "") for key in keys} for row in scored]
    return scored


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    if not isinstance(output, dict) or not output.get("root"):
        raise LogitCellSignScoreError("config must define output.root")
    score_cfg = config.get("score", {})
    if not isinstance(score_cfg, dict):
        raise LogitCellSignScoreError("score must be a mapping")
    group_by = score_cfg.get("group_by", DEFAULT_GROUP_BY)
    if not isinstance(group_by, list) or not all(isinstance(item, str) and item for item in group_by):
        raise LogitCellSignScoreError("score.group_by must be a list of non-empty strings")
    target_metric = score_cfg.get("target_metric", "probability_sum_delta_mean")
    if not isinstance(target_metric, str) or not target_metric:
        raise LogitCellSignScoreError("score.target_metric must be a non-empty string")

    inputs = parse_inputs(config)
    goals = parse_goals(config)
    groups = group_rows(inputs=inputs, group_by=group_by, target_metric=target_metric)
    scored = score_groups(groups=groups, goals=goals, target_metric=target_metric)

    output_root = resolve_path(output["root"])
    csv_path = output_root / "cell_sign_scores.csv"
    summary_path = output_root / "summary.json"
    write_csv(csv_path, scored)
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "input_count": len(inputs),
        "group_count": len(groups),
        "scored_row_count": len(scored),
        "target_metric": target_metric,
        "output_root": repo_relative(output_root),
        "outputs": {
            "cell_sign_scores": repo_relative(csv_path),
            "summary": repo_relative(summary_path),
        },
        "top_score": scored[0] if scored else None,
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
    except LogitCellSignScoreError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
