#!/usr/bin/env python3
"""Compare thinking-on Amendment B eval results against source non-thinking runs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import yaml

from materialize_thinking_eval_configs import CONFIG_DIR, EVAL_DIR, SOURCE_CONFIGS, thinking_config_name


DEFAULT_OUTPUT = EVAL_DIR / "analysis" / "thinking_comparison" / "thinking_vs_nonthinking_summary.csv"
METRIC_KEYS = (
    "truthful_pct",
    "refusal_recall_pct",
    "answer_on_unknown_pct",
    "over_refusal_pct",
    "refusal_rate_pct",
    "correct_on_known_pct",
)
CONFIDENCE_KEYS = (
    "coverage_pct",
    "mean_stated_confidence",
    "mae_vs_known_label",
    "brier_vs_known_label",
    "mae_vs_answer_correctness",
    "brier_vs_answer_correctness",
)


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_metrics(result_root: Path, arm: str, eval_set: str) -> dict | None:
    path = result_root / f"{arm}__{eval_set}" / "metrics.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def metric_payload(metrics: dict | None, *, prefix: str) -> dict[str, object]:
    out: dict[str, object] = {}
    if metrics is None:
        for key in (*METRIC_KEYS, *CONFIDENCE_KEYS):
            out[f"{prefix}_{key}"] = ""
        return out
    for key in METRIC_KEYS:
        out[f"{prefix}_{key}"] = metrics["metrics"].get(key, "")
    stated = metrics.get("stated_confidence", {})
    for key in CONFIDENCE_KEYS:
        out[f"{prefix}_{key}"] = stated.get(key, "")
    return out


def numeric_delta(row: dict[str, object], key: str) -> object:
    before = row.get(f"nonthinking_{key}", "")
    after = row.get(f"thinking_{key}", "")
    if before == "" or after == "":
        return ""
    return round(float(after) - float(before), 6)


def compare_pair(source_config: Path, thinking_config: Path) -> list[dict[str, object]]:
    source = load_yaml(source_config)
    thinking = load_yaml(thinking_config)
    source_results = EVAL_DIR / source["results_dir"]
    thinking_results = EVAL_DIR / thinking["results_dir"]
    rows: list[dict[str, object]] = []
    for arm in thinking["arms"]:
        arm_name = arm["name"]
        for eval_set in thinking["eval_sets"]:
            nonthinking_metrics = load_metrics(source_results, arm_name, eval_set)
            thinking_metrics = load_metrics(thinking_results, arm_name, eval_set)
            row: dict[str, object] = {
                "source_config": source_config.name,
                "thinking_config": thinking_config.name,
                "arm": arm_name,
                "method": arm.get("method", ""),
                "model": arm.get("model", ""),
                "eval_set": eval_set,
                "nonthinking_result_present": nonthinking_metrics is not None,
                "thinking_result_present": thinking_metrics is not None,
            }
            row.update(metric_payload(nonthinking_metrics, prefix="nonthinking"))
            row.update(metric_payload(thinking_metrics, prefix="thinking"))
            for key in (*METRIC_KEYS, *CONFIDENCE_KEYS):
                row[f"delta_{key}"] = numeric_delta(row, key)
            rows.append(row)
    return rows


def write_outputs(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else [
        "source_config",
        "thinking_config",
        "arm",
        "method",
        "model",
        "eval_set",
        "nonthinking_result_present",
        "thinking_result_present",
    ]
    with output.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare thinking-on result dirs to their non-thinking sources."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--config",
        action="append",
        help="Compare only this non-thinking source config filename. May be repeated.",
    )
    args = parser.parse_args()

    source_names = tuple(args.config) if args.config else SOURCE_CONFIGS
    rows: list[dict[str, object]] = []
    for source_name in source_names:
        source_config = CONFIG_DIR / source_name
        thinking_config = CONFIG_DIR / thinking_config_name(source_name)
        if not thinking_config.exists():
            continue
        rows.extend(compare_pair(source_config, thinking_config))

    write_outputs(rows, args.output)
    print(args.output)
    print(f"rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
