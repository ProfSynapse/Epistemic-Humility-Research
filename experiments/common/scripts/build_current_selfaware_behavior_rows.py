#!/usr/bin/env python3
"""Materialize current clean-arm SelfAware behavior rows for Phase 3 scans."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
# The generated overlay remains at the legacy probe path because many Phase 3
# configs consume it directly. Move the output only with a coordinated config
# migration.
OUT_ROOT = ROOT / "experiment" / "phase1" / "probe" / "analysis" / "current_selfaware_behavior_rows"


PANELS = [
    {
        "behavior_arm": "clean_sft_merged",
        "source_rows": ROOT / "experiment" / "phase1" / "probe" / "qwen3-4b-clean-sft-seed1-selfaware" / "hidden_states_selfaware_clean_sft_full" / "extraction__8dbd3f623393" / "rows.jsonl",
        "scored_rows": ROOT / "experiment" / "phase1" / "eval" / "results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b" / "clean_schema_sft_merged_seed1__selfaware" / "scored_rows.jsonl",
    },
    {
        "behavior_arm": "clean_sft_grpo_v2",
        "source_rows": ROOT / "experiment" / "phase1" / "probe" / "qwen3-4b-clean-sft-grpo-v2-seed1-selfaware" / "hidden_states_selfaware_clean_sft_grpo_v2_full" / "extraction__55254a04aa1f" / "rows.jsonl",
        "scored_rows": ROOT / "experiment" / "phase1" / "eval" / "results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b" / "clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware" / "scored_rows.jsonl",
    },
    {
        "behavior_arm": "clean_sft_grpo_dpo",
        "source_rows": ROOT / "experiment" / "phase1" / "probe" / "qwen3-4b-clean-sft-grpo-dpo-seed1-selfaware" / "hidden_states_selfaware_clean_sft_grpo_dpo_full" / "extraction__00af99a2efe7" / "rows.jsonl",
        "scored_rows": ROOT / "experiment" / "phase1" / "eval" / "results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b" / "clean_sft_grpo_dpo_seed1__selfaware" / "scored_rows.jsonl",
    },
]


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def stable_row_key(row: dict[str, Any]) -> str:
    row_key = row.get("row_key") or row.get("probe_pool_row_key")
    if isinstance(row_key, str) and row_key:
        return row_key
    return f"selfaware::{row['eval_set']}::{int(row['row_index']):06d}::{row['id']}"


def behavior_cell(row: dict[str, Any]) -> str:
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
    raise ValueError(f"unsupported label {label!r}")


def materialize(panel: dict[str, Any]) -> dict[str, Any]:
    behavior_arm = panel["behavior_arm"]
    source_rows = load_jsonl(panel["source_rows"])
    scored_by_key = {stable_row_key(row): row for row in load_jsonl(panel["scored_rows"])}

    rows: list[dict[str, Any]] = []
    missing: list[str] = []
    cell_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    confidence_values: list[float] = []
    for source in source_rows:
        key = stable_row_key(source)
        scored = scored_by_key.get(key)
        if scored is None:
            missing.append(key)
            continue
        row = dict(source)
        row["row_key"] = key
        if "aliases" in scored:
            row["aliases"] = scored.get("aliases") or []
        if "answer_value" in scored:
            row["answer_value"] = scored.get("answer_value")
        cell = behavior_cell(scored)
        source_arms = dict(row.get("source_arms") or {})
        source_arms[behavior_arm] = {
            "answer_text": scored.get("answer_text"),
            "generated_answer": scored.get("generated_answer"),
            "refused": bool(scored.get("refused")),
            "correct": bool(scored.get("correct")),
            "truthful": bool(scored.get("truthful")),
            "stated_confidence": scored.get("stated_confidence"),
            "behavior_cell": cell,
            "config_sha": scored.get("config_sha"),
            "method": scored.get("method"),
            "model": scored.get("model"),
            "enable_thinking": scored.get("enable_thinking"),
            "generation_attempts": scored.get("generation_attempts"),
            "stated_confidence_retry_count": scored.get("stated_confidence_retry_count"),
            "stated_confidence_retry_exhausted": scored.get("stated_confidence_retry_exhausted"),
        }
        row["source_arms"] = source_arms
        row["behavior_cell"] = cell
        rows.append(row)
        cell_counts[cell] += 1
        label_counts[str(row.get("label"))] += 1
        confidence = scored.get("stated_confidence")
        if confidence is not None:
            confidence_values.append(float(confidence))

    if missing:
        raise ValueError(f"{behavior_arm}: missing scored rows for {len(missing)} keys; first={missing[:5]}")

    output = OUT_ROOT / behavior_arm
    output.mkdir(parents=True, exist_ok=True)
    rows_path = output / "rows.jsonl"
    summary_path = output / "summary.json"
    with rows_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    summary = {
        "behavior_arm": behavior_arm,
        "source_rows": rel(panel["source_rows"]),
        "scored_rows": rel(panel["scored_rows"]),
        "rows": rel(rows_path),
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "behavior_cell_counts": dict(sorted(cell_counts.items())),
        "mean_stated_confidence": sum(confidence_values) / len(confidence_values) if confidence_values else None,
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> int:
    summaries = [materialize(panel) for panel in PANELS]
    manifest = {
        "panels": summaries,
        "outputs": [summary["rows"] for summary in summaries],
    }
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    (OUT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
