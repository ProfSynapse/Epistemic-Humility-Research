#!/usr/bin/env python3
"""Materialize behavior-labeled rows from gold-backed generation scores."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from phase3_sae_smoke import repo_relative, resolve_path


ANALYSIS_TYPE = "phase3_gold_behavior_panel"
NOTICE = "GOLD_BACKED_GENERATED_BEHAVIOR_LABELS"
DEFAULT_CONTROL = "no_vector_baseline"


class GoldBehaviorPanelError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise GoldBehaviorPanelError(f"{repo_relative(path)} did not load to a YAML mapping")
    return payload


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise GoldBehaviorPanelError(f"missing JSONL file: {repo_relative(path)}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise GoldBehaviorPanelError(f"{repo_relative(path)}:{line_number} row is not an object")
            rows.append(row)
    return rows


def row_key(row: dict[str, Any]) -> str:
    value = row.get("row_key") or row.get("probe_pool_row_key")
    if not isinstance(value, str) or not value:
        raise GoldBehaviorPanelError("row missing row_key/probe_pool_row_key")
    return value


def generation_behavior_cell(row: dict[str, Any]) -> str:
    label = row.get("label")
    refused = bool(row.get("refused"))
    correct = bool(row.get("correct"))
    if label == "known":
        if refused:
            return "known_refused"
        if correct:
            return "known_correct_answered"
        return "known_answered_wrong"
    if label == "unknown":
        if refused:
            return "unknown_refused"
        if correct:
            return "unknown_answered_correct"
        return "unknown_answered_wrong"
    raise GoldBehaviorPanelError(f"unsupported label {label!r}")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def write_key_file(path: Path, keys: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"{key}\n" for key in keys), encoding="utf-8")


def scored_rows_by_key(
    scored_rows: list[dict[str, Any]],
    *,
    control: str,
    arm_id: str | None,
) -> dict[str, dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in scored_rows:
        if row.get("control") != control:
            continue
        if arm_id is not None and row.get("arm_id") != arm_id:
            continue
        key = row_key(row)
        if key in selected:
            duplicates.append(key)
        selected[key] = row
    if duplicates:
        raise GoldBehaviorPanelError(f"duplicate scored rows for keys: {duplicates[:5]}")
    return selected


def materialize_panel(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    source_rows_path = resolve_path(config["source_rows"])
    scored_rows_path = resolve_path(config["scored_rows"])
    behavior_arm = config.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise GoldBehaviorPanelError("config must define behavior_arm")
    control = str(config.get("control", DEFAULT_CONTROL))
    arm_id = config.get("arm_id")
    if arm_id is not None and not isinstance(arm_id, str):
        raise GoldBehaviorPanelError("arm_id must be a string when provided")
    output = config.get("output", {})
    if not isinstance(output, dict) or not output.get("root"):
        raise GoldBehaviorPanelError("config must define output.root")
    output_root = resolve_path(output["root"])
    require_all_rows = bool(config.get("require_all_rows", True))

    source_rows = load_jsonl(source_rows_path)
    scored_rows = scored_rows_by_key(load_jsonl(scored_rows_path), control=control, arm_id=arm_id)

    materialized: list[dict[str, Any]] = []
    missing: list[str] = []
    cell_keys: dict[str, list[str]] = {}
    label_counts: Counter[str] = Counter()
    cell_counts: Counter[str] = Counter()
    for source_row in source_rows:
        key = row_key(source_row)
        scored = scored_rows.get(key)
        if scored is None:
            missing.append(key)
            continue
        row = dict(source_row)
        row["row_key"] = key
        if "aliases" in scored:
            row["aliases"] = scored.get("aliases", [])
        if "answer_value" in scored:
            row["answer_value"] = scored.get("answer_value")
        cell = generation_behavior_cell(scored)
        row["behavior_cell"] = cell
        source_arms = dict(row.get("source_arms", {}))
        source_arms[behavior_arm] = {
            "answer_text": scored.get("generated_answer", ""),
            "generated_answer": scored.get("generated_answer", ""),
            "refused": bool(scored.get("refused")),
            "correct": bool(scored.get("correct")),
            "truthful": bool(scored.get("truthful")),
            "behavior_cell": cell,
            "method": "baseline_generation_score",
            "control": control,
            "arm_id": scored.get("arm_id"),
            "candidate_label": scored.get("candidate_label"),
        }
        row["source_arms"] = source_arms
        materialized.append(row)
        label_counts[str(row.get("label"))] += 1
        cell_counts[cell] += 1
        cell_keys.setdefault(cell, []).append(key)

    if missing and require_all_rows:
        raise GoldBehaviorPanelError(f"missing scored rows for {len(missing)} source rows; first={missing[:5]}")

    rows_out = output_root / "rows.jsonl"
    summary_out = output_root / "summary.json"
    write_jsonl(rows_out, materialized)
    key_outputs: dict[str, str] = {}
    for cell, keys in sorted(cell_keys.items()):
        path = output_root / "row_keys" / f"{cell}_row_keys.txt"
        write_key_file(path, keys)
        key_outputs[cell] = repo_relative(path)

    balanced = config.get("balanced_panel", {})
    balanced_outputs: dict[str, str] = {}
    if isinstance(balanced, dict) and balanced.get("cells"):
        cells = [str(cell) for cell in balanced["cells"]]
        max_per_cell = min(len(cell_keys.get(cell, [])) for cell in cells)
        requested = balanced.get("rows_per_cell")
        if requested is not None:
            max_per_cell = min(max_per_cell, int(requested))
        selected_keys: list[str] = []
        for cell in cells:
            selected_keys.extend(cell_keys.get(cell, [])[:max_per_cell])
        name = str(balanced.get("name", "balanced_available"))
        path = output_root / "row_keys" / f"{name}_row_keys.txt"
        write_key_file(path, selected_keys)
        balanced_outputs[name] = repo_relative(path)

    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "source_rows": repo_relative(source_rows_path),
        "scored_rows": repo_relative(scored_rows_path),
        "behavior_arm": behavior_arm,
        "control": control,
        "arm_id": arm_id,
        "source_row_count": len(source_rows),
        "materialized_row_count": len(materialized),
        "missing_source_row_count": len(missing),
        "label_counts": dict(sorted(label_counts.items())),
        "behavior_cell_counts": dict(sorted(cell_counts.items())),
        "outputs": {
            "rows": repo_relative(rows_out),
            "summary": repo_relative(summary_out),
            "row_key_files": key_outputs,
            "balanced_row_key_files": balanced_outputs,
        },
    }
    write_json(summary_out, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = materialize_panel(resolve_path(args.config))
    except GoldBehaviorPanelError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
