"""Build durable SelfAware full-run comparison CSVs.

This intentionally aggregates only full 3,369-row SelfAware runs used in the
Phase 1 local analysis. Smokes, OOD-only slices, thinking-on duplicates, and
known-bad sanity checks are excluded by construction.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = Path(__file__).resolve().parent

PER_RUN_OUT = OUT_DIR / "selfaware_full_run_comparison.csv"
GROUPED_OUT = OUT_DIR / "selfaware_full_run_comparison_grouped.csv"


def _selected_metric_paths() -> list[tuple[str, Path]]:
    selected: list[tuple[str, Path]] = []

    for result_dir in sorted(ROOT.glob("results_selfaware_full_seed*_all_arms_4b_*")):
        if "thinking" in result_dir.name:
            continue
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Original cold-start", path))

    amendment_a_dirs = [
        "results_amendment_a_selfaware_full_local_4b",
        "results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b",
        "results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b",
        "results_amendment_a_selfaware_full_seed3_sft_dpo_local_4b",
    ]
    for name in amendment_a_dirs:
        for path in (ROOT / name).glob("*__selfaware/metrics.json"):
            selected.append(("Amendment A SFT-warmed sequential", path))

    for result_dir in sorted(
        ROOT.glob(
            "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_"
            "selfaware_seed*_all_arms_4b"
        )
    ):
        if "thinking" in result_dir.name:
            continue
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Amendment B answer-confidence cold-start", path))

    for result_dir in sorted(
        ROOT.glob(
            "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_"
            "selfaware_seq*_4b"
        )
    ):
        if "thinking" in result_dir.name:
            continue
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Amendment B answer-confidence SFT-warmed sequential", path))

    for result_dir in sorted(ROOT.glob("results_amendment_d_response_confidence_selfaware_*_full_4b")):
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Amendment D response-confidence", path))

    for result_dir in sorted(ROOT.glob("results_amendment_e_response_confidence_selfaware_*_full_4b")):
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Amendment E clean response-confidence", path))

    for result_dir in sorted(ROOT.glob("results_amendment_f_response_confidence_selfaware_*_full_4b")):
        for path in result_dir.glob("*__selfaware/metrics.json"):
            selected.append(("Amendment F GRPO-centered stacking", path))

    return selected


def _infer_seed(*parts: str) -> str:
    for part in parts:
        match = re.search(r"seed(\d+)", part or "")
        if match:
            return match.group(1)
    return ""


def _normalized_arm(family: str, arm: str) -> str:
    normalized = re.sub(r"_seed\d+(_lowmem|_corrected_base)?", "", arm)
    normalized = re.sub(r"seed\d+", "seed", normalized)

    if "clean_sft_dpo_grpo" in normalized:
        normalized = "clean_sft_dpo_grpo"
    elif "clean_sft_kto_grpo" in normalized:
        normalized = "clean_sft_kto_grpo"
    elif "clean_sft_grpo_dpo" in normalized:
        normalized = "clean_sft_grpo_dpo"
    elif "clean_sft_grpo_kto" in normalized:
        normalized = "clean_sft_grpo_kto"
    elif "clean_schema_sft_grpo_v2" in normalized:
        normalized = "clean_sft_grpo_v2"
    elif "clean_schema_sft_grpo" in normalized:
        normalized = "clean_sft_grpo_v1"
    elif "clean_schema_sft_dpo" in normalized:
        normalized = "clean_sft_dpo"
    elif "clean_schema_sft_kto" in normalized:
        normalized = "clean_sft_kto"
    elif "clean_schema_sft_merged" in normalized:
        normalized = "clean_sft_merged"
    elif "sft_merged" in normalized:
        normalized = "sft_merged"
    elif "sft_dpo" in normalized:
        normalized = "sft_dpo"
    elif "sft_kto" in normalized:
        normalized = "sft_kto"
    elif "schema_sft_grpo" in normalized:
        normalized = "schema_sft_grpo"
    elif "schema_sft_merged" in normalized:
        normalized = "schema_sft_merged"

    if family.startswith("Original") or family.startswith("Amendment B answer-confidence cold"):
        normalized = normalized.replace("_seed", "")

    return normalized


def _confidence_metrics(data: dict[str, Any], metrics: dict[str, Any]) -> tuple[Any, Any, Any]:
    confidence = data.get("stated_confidence") or data.get("response_confidence") or {}
    if not isinstance(confidence, dict):
        confidence = {}
    mean_confidence = (
        confidence.get("mean_stated_confidence")
        or confidence.get("mean_response_confidence")
        or metrics.get("mean_stated_confidence")
        or metrics.get("mean_response_confidence")
    )
    return (
        mean_confidence,
        confidence.get("coverage_pct"),
        confidence.get("brier_vs_response_appropriateness"),
    )


def _balanced_behavior_score(metrics: dict[str, Any]) -> float:
    return mean(
        [
            float(metrics["truthful_pct"]),
            float(metrics["refusal_recall_pct"]),
            100.0 - float(metrics["over_refusal_pct"]),
            float(metrics["correct_on_known_pct"]),
        ]
    )


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, path in _selected_metric_paths():
        data = json.loads(path.read_text(encoding="utf-8"))
        metrics = data.get("metrics", {})
        if metrics.get("n") != 3369:
            continue

        counts = data.get("counts", {})
        arm = data.get("arm") or path.parent.name.split("__")[0]
        mean_confidence, confidence_coverage, brier_response = _confidence_metrics(data, metrics)
        result_dir = path.parents[1].name

        rows.append(
            {
                "family": family,
                "run_dir": result_dir,
                "arm": arm,
                "normalized_arm": _normalized_arm(family, arm),
                "seed": _infer_seed(arm, result_dir),
                "n": metrics.get("n", ""),
                "truthful_pct": metrics.get("truthful_pct", ""),
                "refusal_recall_pct": metrics.get("refusal_recall_pct", ""),
                "answer_on_unknown_pct": metrics.get("answer_on_unknown_pct", ""),
                "over_refusal_pct": metrics.get("over_refusal_pct", ""),
                "correct_on_known_pct": metrics.get("correct_on_known_pct", ""),
                "refusal_rate_pct": metrics.get("refusal_rate_pct", ""),
                "balanced_behavior_score": _balanced_behavior_score(metrics),
                "mean_confidence": mean_confidence or "",
                "confidence_coverage_pct": confidence_coverage or "",
                "brier_vs_response_appropriateness": brier_response or "",
                "refuse_on_unknown": counts.get("refuse_on_unknown", ""),
                "refuse_on_known": counts.get("refuse_on_known", ""),
                "answered_known": counts.get("answered_known", ""),
                "correct_known": counts.get("correct_known", ""),
                "answered_unknown": counts.get("answered_unknown", ""),
                "source_metrics": path.relative_to(ROOT.parents[2]).as_posix(),
            }
        )

    return sorted(rows, key=lambda row: (row["family"], row["normalized_arm"], row["seed"], row["arm"]))


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _group_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["family"], row["normalized_arm"])].append(row)

    metric_fields = [
        "truthful_pct",
        "refusal_recall_pct",
        "answer_on_unknown_pct",
        "over_refusal_pct",
        "correct_on_known_pct",
        "refusal_rate_pct",
        "balanced_behavior_score",
        "mean_confidence",
        "confidence_coverage_pct",
        "brier_vs_response_appropriateness",
    ]

    out: list[dict[str, Any]] = []
    for (family, arm), group in sorted(grouped.items()):
        record: dict[str, Any] = {"family": family, "normalized_arm": arm, "n_runs": len(group)}
        for field in metric_fields:
            values = [float(row[field]) for row in group if row[field] not in ("", None)]
            record[f"mean_{field}"] = mean(values) if values else ""
        record["source_metrics"] = ";".join(row["source_metrics"] for row in group)
        out.append(record)

    return out


def main() -> None:
    rows = build_rows()
    _write_csv(PER_RUN_OUT, rows, list(rows[0].keys()))

    grouped_rows = _group_rows(rows)
    _write_csv(GROUPED_OUT, grouped_rows, list(grouped_rows[0].keys()))

    print(f"Wrote {PER_RUN_OUT}")
    print(f"Wrote {GROUPED_OUT}")


if __name__ == "__main__":
    main()
