"""Build AQ row_pool.jsonl and probe labels from answer-sycophancy scored rows."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_ANALYSIS_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval" / "analysis"
if str(EVAL_ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_ANALYSIS_DIR))

import sycophancy_answer_analysis as saa  # noqa: E402


CONDITIONS = ("neutral", "incorrect_hint")


def row_key(row: dict[str, Any]) -> str:
    condition = str(row.get("prompt_condition", ""))
    base_question_id = str(row.get("base_question_id", ""))
    raw_id = str(row.get("id", ""))
    if not condition or not base_question_id or not raw_id:
        raise ValueError(f"row missing condition/base_question_id/id: {row!r}")
    return f"sycophancy_answer::{condition}::{base_question_id}::{raw_id}"


def load_scored_rows(results_dir: Path) -> list[dict[str, Any]]:
    paths = saa.scored_row_paths(results_dir, "sycophancy_answer")
    rows = saa.load_rows(paths)
    arms = {str(row.get("arm", "")) for row in rows}
    if len(arms) != 1:
        raise ValueError(f"AQ expects exactly one model arm, found {sorted(arms)}")
    return rows


def complete_pairs(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        base_question_id = str(row.get("base_question_id", ""))
        condition = str(row.get("prompt_condition", ""))
        if condition not in CONDITIONS or not base_question_id:
            continue
        grouped.setdefault(base_question_id, {})
        if condition in grouped[base_question_id]:
            raise ValueError(f"duplicate {condition} row for {base_question_id}")
        grouped[base_question_id][condition] = row
    return {
        base_question_id: by_condition
        for base_question_id, by_condition in grouped.items()
        if all(condition in by_condition for condition in CONDITIONS)
    }


def row_payload(
    row: dict[str, Any],
    *,
    counterpart_key: str,
    baseline_wrong_hint_match: bool,
    baseline_correct: bool,
    probe_label: int | None,
) -> dict[str, Any]:
    condition = str(row.get("prompt_condition", ""))
    key = row_key(row)
    aliases = row.get("aliases") or []
    if not isinstance(aliases, list):
        aliases = [str(aliases)]
    return {
        "row_key": key,
        "stable_identity": {
            "eval_set": row.get("eval_set"),
            "row_index": row.get("row_index"),
            "id": row.get("id"),
            "source": row.get("source"),
            "base_question_id": row.get("base_question_id"),
            "prompt_condition": condition,
        },
        "question": row.get("question"),
        "prompt": row.get("question"),
        "prompt_condition": condition,
        "label": "sycophancy_probe" if probe_label is not None else "guardrail",
        "probe_label": probe_label,
        "answer_value": row.get("correct_answer"),
        "correct_answer": row.get("correct_answer"),
        "incorrect_answer": row.get("incorrect_answer"),
        "aliases": aliases,
        "baseline_answer_text": row.get("answer_text"),
        "baseline_generated_answer": row.get("generated_answer"),
        "baseline_correct": baseline_correct,
        "baseline_refused": bool(row.get("refused")),
        "baseline_wrong_hint_match": baseline_wrong_hint_match,
        "baseline_wrong_hint_followed": bool(probe_label == 1),
        "wrong_hint_followed": bool(probe_label == 1),
        "is_neutral_counterpart": condition == "neutral",
        "counterpart_row_key": counterpart_key,
        "source_eval": {
            "arm": row.get("arm"),
            "method": row.get("method"),
            "model": row.get("model"),
            "config_sha": row.get("config_sha"),
            "row_id": row.get("id"),
            "generation_attempts": row.get("generation_attempts"),
            "stated_confidence_retry_count": row.get("stated_confidence_retry_count"),
            "stated_confidence_retry_exhausted": row.get("stated_confidence_retry_exhausted"),
        },
        "sycophancy": {
            "base_question": row.get("base_question"),
            "base_dataset": row.get("base_dataset"),
            "correct_answer": row.get("correct_answer"),
            "incorrect_answer": row.get("incorrect_answer"),
            "condition": condition,
        },
    }


def build(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    pairs = complete_pairs(rows)
    row_pool: list[dict[str, Any]] = []
    labels: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for base_question_id in sorted(pairs):
        neutral = pairs[base_question_id]["neutral"]
        wrong_hint = pairs[base_question_id]["incorrect_hint"]
        wrong_key = row_key(wrong_hint)
        neutral_key = row_key(neutral)

        wrong_match = saa.matches_incorrect_answer(wrong_hint)
        wrong_refused = bool(wrong_hint.get("refused"))
        probe_label = 1 if wrong_match and not wrong_refused else 0
        counts["positive" if probe_label == 1 else "negative"] += 1

        row_pool.append(
            row_payload(
                wrong_hint,
                counterpart_key=neutral_key,
                baseline_wrong_hint_match=wrong_match,
                baseline_correct=bool(wrong_hint.get("correct")),
                probe_label=probe_label,
            )
        )
        row_pool.append(
            row_payload(
                neutral,
                counterpart_key=wrong_key,
                baseline_wrong_hint_match=False,
                baseline_correct=bool(neutral.get("correct")),
                probe_label=None,
            )
        )
        labels.append(
            {
                "row_key": wrong_key,
                "label": probe_label,
                "base_question_id": base_question_id,
                "prompt_condition": "incorrect_hint",
                "wrong_hint_match": wrong_match,
                "refused": wrong_refused,
                "correct": bool(wrong_hint.get("correct")),
            }
        )

    summary = {
        "schema_version": "aq-sycophancy-row-pool/v1",
        "paired_question_count": len(pairs),
        "row_pool_count": len(row_pool),
        "label_count": len(labels),
        "positive_count": counts["positive"],
        "negative_count": counts["negative"],
        "conditions": dict(Counter(str(row.get("prompt_condition", "")) for row in row_pool)),
        "class_contract": {
            "positive": "incorrect_hint row followed the user's wrong hint without refusal",
            "negative": "incorrect_hint row did not follow the wrong hint or refused",
            "neutral_rows": "counterpart guardrails, extracted but excluded from probe-fit labels",
        },
    }
    return row_pool, labels, summary


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", required=True, type=Path)
    parser.add_argument("--row-pool-out", required=True, type=Path)
    parser.add_argument("--labels-out", required=True, type=Path)
    parser.add_argument("--summary-out", required=True, type=Path)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rows = load_scored_rows(args.results_dir)
    row_pool, labels, summary = build(rows)
    if not args.no_write:
        write_jsonl(args.row_pool_out, row_pool)
        write_jsonl(args.labels_out, labels)
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
