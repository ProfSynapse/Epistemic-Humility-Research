"""Explore unknown-question semantic category behavior by training regimen.

This joins validated semantic labels for unknown questions back to row-level
behavior outputs. It is exploratory only: category labels are analysis aids, not
gold labels, and small cells should be read as directional.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable


ROOT = Path(__file__).resolve().parents[5]
DEFAULT_LABELS_PATH = (
    ROOT
    / "experiment"
    / "phase1"
    / "eval"
    / "analysis"
    / "unknown_question_labels"
    / "llm_labeled_unknown_answered_questions_v3.csv"
)
DEFAULT_ROW_DIR = ROOT / "experiment" / "phase1" / "eval" / "analysis" / "row_pattern_outputs"
DEFAULT_OUTPUT_DIR = ROOT / "experiment" / "phase1" / "eval" / "analysis" / "unknown_question_labels"

ARM_ORDER = ("sft_merged", "sft_dpo", "sft_kto")
CATEGORY_AXES = ("primary_domain", "epistemic_type")
DELTA_PAIRS = (
    ("sft_dpo", "sft_merged", "dpo_minus_sft"),
    ("sft_kto", "sft_merged", "kto_minus_sft"),
    ("sft_dpo", "sft_kto", "dpo_minus_kto"),
)
MIN_TOP_EFFECT_N = 5


def normalize_question(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def question_hash(question: str) -> str:
    return hashlib.sha256(normalize_question(question).encode("utf-8")).hexdigest()[:16]


def question_key(analysis_family: str, question: str) -> str:
    return f"{analysis_family}:{question_hash(question)}"


def truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def parse_float(value: str | None) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def is_answered(row: dict[str, str]) -> bool:
    state = row.get("behavior_state", "")
    if state:
        return state == "unknown_answered_hallucination_exposure"
    return not truthy(row.get("refused"))


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n <= 0:
        return (math.nan, math.nan)
    p_hat = successes / n
    z2 = z * z
    denom = 1 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denom
    margin = z * math.sqrt((p_hat * (1 - p_hat) + z2 / (4 * n)) / n) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def rate_diff_ci(success_a: int, n_a: int, success_b: int, n_b: int, z: float = 1.96) -> tuple[float, float]:
    if n_a <= 0 or n_b <= 0:
        return (math.nan, math.nan)
    p_a = success_a / n_a
    p_b = success_b / n_b
    se = math.sqrt((p_a * (1 - p_a) / n_a) + (p_b * (1 - p_b) / n_b))
    diff = p_a - p_b
    return (max(-1.0, diff - z * se), min(1.0, diff + z * se))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: Iterable[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_labels(path: Path) -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    for row in read_csv(path):
        key = row.get("question_key") or f"{row.get('analysis_family_coverage', '')}:{row.get('question_hash', '')}"
        if not key or key == ":":
            key = question_key(row.get("analysis_family_coverage", ""), row.get("question", ""))
        labels[key] = row
    return labels


def load_row_masters(row_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for filename in ("row_master_amendment_a.csv", "row_master_amendment_b.csv"):
        path = row_dir / filename
        for row in read_csv(path):
            if row.get("include_status") == "include" and row.get("label") == "unknown":
                rows.append(row)
    return rows


def join_rows_to_labels(
    rows: list[dict[str, str]], labels_by_key: dict[str, dict[str, str]]
) -> tuple[list[dict[str, str]], dict[str, int]]:
    joined: list[dict[str, str]] = []
    total_unknown = 0
    labeled_unknown = 0
    missing_keys: set[str] = set()
    matched_keys: set[str] = set()

    for row in rows:
        total_unknown += 1
        key = question_key(row.get("analysis_family", ""), row.get("question", ""))
        label = labels_by_key.get(key)
        if not label:
            missing_keys.add(key)
            continue
        matched_keys.add(key)
        labeled_unknown += 1
        enriched = dict(row)
        enriched["category_question_key"] = key
        for field in ("primary_domain", "secondary_domain", "epistemic_type", "answer_form", "label_confidence"):
            enriched[field] = label.get(field, "")
        joined.append(enriched)

    return joined, {
        "source_unknown_rows": total_unknown,
        "joined_unknown_rows": labeled_unknown,
        "missing_unknown_rows": total_unknown - labeled_unknown,
        "label_questions": len(labels_by_key),
        "matched_label_questions": len(matched_keys),
        "unmatched_label_questions": len(set(labels_by_key) - matched_keys),
        "missing_question_keys": len(missing_keys),
    }


def aggregate_by_arm(joined_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    buckets: dict[tuple[str, str, str, str], dict[str, object]] = {}
    for row in joined_rows:
        for axis in CATEGORY_AXES:
            category_value = row.get(axis) or "missing"
            key = (row.get("analysis_family", ""), axis, category_value, row.get("arm_role", ""))
            bucket = buckets.setdefault(
                key,
                {
                    "analysis_family": key[0],
                    "category_axis": key[1],
                    "category_value": key[2],
                    "arm_role": key[3],
                    "n": 0,
                    "answered_count": 0,
                    "refused_count": 0,
                    "confidence_values": [],
                },
            )
            bucket["n"] = int(bucket["n"]) + 1
            answered = is_answered(row)
            bucket["answered_count"] = int(bucket["answered_count"]) + int(answered)
            bucket["refused_count"] = int(bucket["refused_count"]) + int(truthy(row.get("refused")))
            confidence = parse_float(row.get("stated_confidence"))
            if confidence is not None:
                bucket["confidence_values"].append(confidence)

    output: list[dict[str, object]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        n = int(bucket["n"])
        answered = int(bucket["answered_count"])
        refused = int(bucket["refused_count"])
        low, high = wilson_interval(answered, n)
        confidence_values = bucket.pop("confidence_values")
        output.append(
            {
                **bucket,
                "answer_rate": f"{answered / n:.6f}" if n else "",
                "answer_rate_ci_low": f"{low:.6f}" if n else "",
                "answer_rate_ci_high": f"{high:.6f}" if n else "",
                "refusal_rate": f"{refused / n:.6f}" if n else "",
                "mean_stated_confidence": f"{mean(confidence_values):.6f}" if confidence_values else "",
                "confidence_n": len(confidence_values),
            }
        )
    return output


def aggregate_deltas(by_arm_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    index = {
        (str(row["analysis_family"]), str(row["category_axis"]), str(row["category_value"]), str(row["arm_role"])): row
        for row in by_arm_rows
    }
    groups = sorted({(family, axis, value) for family, axis, value, _arm in index})
    output: list[dict[str, object]] = []
    for family, axis, value in groups:
        for arm_a, arm_b, comparison in DELTA_PAIRS:
            row_a = index.get((family, axis, value, arm_a))
            row_b = index.get((family, axis, value, arm_b))
            if not row_a or not row_b:
                continue
            n_a = int(row_a["n"])
            n_b = int(row_b["n"])
            answered_a = int(row_a["answered_count"])
            answered_b = int(row_b["answered_count"])
            rate_a = answered_a / n_a if n_a else math.nan
            rate_b = answered_b / n_b if n_b else math.nan
            diff = rate_a - rate_b
            low, high = rate_diff_ci(answered_a, n_a, answered_b, n_b)
            output.append(
                {
                    "analysis_family": family,
                    "category_axis": axis,
                    "category_value": value,
                    "comparison": comparison,
                    "from_arm": arm_b,
                    "to_arm": arm_a,
                    "from_n": n_b,
                    "to_n": n_a,
                    "from_answer_rate": f"{rate_b:.6f}",
                    "to_answer_rate": f"{rate_a:.6f}",
                    "answer_rate_delta": f"{diff:.6f}",
                    "answer_rate_delta_ci_low": f"{low:.6f}" if not math.isnan(low) else "",
                    "answer_rate_delta_ci_high": f"{high:.6f}" if not math.isnan(high) else "",
                    "min_cell_n": min(n_a, n_b),
                    "absolute_delta": f"{abs(diff):.6f}",
                }
            )
    return output


def top_effects(delta_rows: list[dict[str, object]], limit: int = 40) -> list[dict[str, object]]:
    eligible = [row for row in delta_rows if int(row["min_cell_n"]) >= MIN_TOP_EFFECT_N]
    eligible.sort(key=lambda row: (float(row["absolute_delta"]), int(row["min_cell_n"])), reverse=True)
    return eligible[:limit]


def confidence_by_category(joined_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    buckets: dict[tuple[str, str, str, str], list[float]] = defaultdict(list)
    for row in joined_rows:
        if row.get("analysis_family") != "amendment_b":
            continue
        confidence = parse_float(row.get("stated_confidence"))
        if confidence is None:
            continue
        for axis in CATEGORY_AXES:
            buckets[(row["analysis_family"], axis, row.get(axis) or "missing", row.get("arm_role", ""))].append(confidence)

    output: list[dict[str, object]] = []
    for key in sorted(buckets):
        values = buckets[key]
        output.append(
            {
                "analysis_family": key[0],
                "category_axis": key[1],
                "category_value": key[2],
                "arm_role": key[3],
                "confidence_n": len(values),
                "mean_stated_confidence": f"{mean(values):.6f}",
                "min_stated_confidence": f"{min(values):.6f}",
                "max_stated_confidence": f"{max(values):.6f}",
            }
        )
    return output


def write_report(
    path: Path,
    labels_path: Path,
    coverage: dict[str, int],
    by_arm_rows: list[dict[str, object]],
    top_rows: list[dict[str, object]],
) -> None:
    lines = [
        "# Category x Regimen Exploratory Analysis",
        "",
        "Exploratory join of semantic unknown-question labels to row-level behavior outputs.",
        "",
        "## Inputs",
        "",
        f"- Semantic labels: `{labels_path.name}`",
        "- Row masters: `row_master_amendment_a.csv`, `row_master_amendment_b.csv`",
        "- Category axes: `primary_domain`, `epistemic_type`",
        "- Regimen arms: `sft_merged`, `sft_dpo`, `sft_kto`",
        "",
        "## Join Coverage",
        "",
    ]
    for key, value in coverage.items():
        lines.append(f"- {key}: {value}")

    lines.extend(
        [
            "",
            "## Top Exploratory Answer-Rate Effects",
            "",
            "Ranked by absolute answer-rate delta with `min_cell_n >= 5`.",
            "",
            "| family | axis | category | comparison | from_rate | to_rate | delta | min_n |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in top_rows[:20]:
        lines.append(
            "| {analysis_family} | {category_axis} | {category_value} | {comparison} | "
            "{from_answer_rate} | {to_answer_rate} | {answer_rate_delta} | {min_cell_n} |".format(**row)
        )

    if not top_rows:
        lines.append("| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |")

    lines.extend(
        [
            "",
            "## Top Effects By Amendment",
            "",
            "| family | axis | category | comparison | from_rate | to_rate | delta | min_n |",
            "|---|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    by_family: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in top_rows:
        by_family[str(row["analysis_family"])].append(row)
    for family in sorted(by_family):
        for row in by_family[family][:5]:
            lines.append(
                "| {analysis_family} | {category_axis} | {category_value} | {comparison} | "
                "{from_answer_rate} | {to_answer_rate} | {answer_rate_delta} | {min_cell_n} |".format(**row)
            )

    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- This is exploratory/vibes analysis, not a confirmatory statistical test.",
            "- Semantic labels are broad analysis labels; they are not gold labels.",
            "- The label artifact covers unknown questions that were answered by at least one arm, so always-unanswered unknown questions are outside the joined category analysis unless separately labeled.",
            "- Small category cells can create large deltas; use `min_cell_n` and confidence intervals before interpreting a cluster.",
            "- `answer_form` is intentionally excluded from the main analysis because it is less reliable than `primary_domain` and `epistemic_type`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_labels_path(labels_path: Path) -> Path:
    if labels_path.exists():
        return labels_path
    raise FileNotFoundError(f"semantic label file not found: {labels_path}")


def run(labels_path: Path = DEFAULT_LABELS_PATH, row_dir: Path = DEFAULT_ROW_DIR, output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, int]:
    resolved_labels_path = resolve_labels_path(labels_path)
    labels = load_labels(resolved_labels_path)
    source_rows = load_row_masters(row_dir)
    joined_rows, coverage = join_rows_to_labels(source_rows, labels)

    by_arm_rows = aggregate_by_arm(joined_rows)
    delta_rows = aggregate_deltas(by_arm_rows)
    top_rows = top_effects(delta_rows)
    confidence_rows = confidence_by_category(joined_rows)

    write_csv(
        output_dir / "category_regimen_behavior_by_arm.csv",
        by_arm_rows,
        [
            "analysis_family",
            "category_axis",
            "category_value",
            "arm_role",
            "n",
            "answered_count",
            "refused_count",
            "answer_rate",
            "answer_rate_ci_low",
            "answer_rate_ci_high",
            "refusal_rate",
            "mean_stated_confidence",
            "confidence_n",
        ],
    )
    write_csv(
        output_dir / "category_regimen_deltas.csv",
        delta_rows,
        [
            "analysis_family",
            "category_axis",
            "category_value",
            "comparison",
            "from_arm",
            "to_arm",
            "from_n",
            "to_n",
            "from_answer_rate",
            "to_answer_rate",
            "answer_rate_delta",
            "answer_rate_delta_ci_low",
            "answer_rate_delta_ci_high",
            "min_cell_n",
            "absolute_delta",
        ],
    )
    write_csv(
        output_dir / "category_regimen_top_effects.csv",
        top_rows,
        [
            "analysis_family",
            "category_axis",
            "category_value",
            "comparison",
            "from_arm",
            "to_arm",
            "from_n",
            "to_n",
            "from_answer_rate",
            "to_answer_rate",
            "answer_rate_delta",
            "answer_rate_delta_ci_low",
            "answer_rate_delta_ci_high",
            "min_cell_n",
            "absolute_delta",
        ],
    )
    write_csv(
        output_dir / "category_regimen_confidence_by_category_b.csv",
        confidence_rows,
        [
            "analysis_family",
            "category_axis",
            "category_value",
            "arm_role",
            "confidence_n",
            "mean_stated_confidence",
            "min_stated_confidence",
            "max_stated_confidence",
        ],
    )
    write_report(output_dir / "category_regimen_report.md", resolved_labels_path, coverage, by_arm_rows, top_rows)
    return coverage


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS_PATH)
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    coverage = run(args.labels, args.row_dir, args.output_dir)
    for key, value in coverage.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()
