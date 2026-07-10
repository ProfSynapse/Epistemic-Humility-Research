#!/usr/bin/env python3
"""Compare thinking-enabled TriviaQA probe rows against the locked probe."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


EXP_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXP_DIR.parents[1]
PROBE_DIR = REPO_ROOT / "experiment/phase1/probe"
DEFAULT_BASE = PROBE_DIR / "qwen3-4b-instruct" / "probe_results.jsonl"
DEFAULT_THINKING = (
    PROBE_DIR / "qwen3-4b-instruct-thinking-audit-128-1024" / "probe_results.jsonl"
)
DEFAULT_OUT = (
    EXP_DIR
    / "artifacts"
    / "thinking_audit_128_1024"
)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def index_by_row_key(rows: list[dict]) -> dict[str, dict]:
    return {row["probe_pool_row_key"]: row for row in rows}


def status_counts(row: dict) -> Counter:
    return Counter(row.get("sampled_thinking_extract_statuses", []))


def compare_rows(base_rows: list[dict], thinking_rows: list[dict]) -> list[dict]:
    base_by_key = index_by_row_key(base_rows)
    compared: list[dict] = []
    for thinking in thinking_rows:
        row_key = thinking["probe_pool_row_key"]
        base = base_by_key.get(row_key)
        if base is None:
            continue
        statuses = status_counts(thinking)
        compared.append({
            "probe_pool_row_key": row_key,
            "question_id": thinking["question_id"],
            "question": thinking["question"],
            "base_label": base["label"],
            "thinking_label": thinking["label"],
            "label_transition": f"{base['label']}->{thinking['label']}",
            "base_p_correct": base["p_correct"],
            "thinking_p_correct": thinking["p_correct"],
            "delta_p_correct": round(
                float(thinking["p_correct"]) - float(base["p_correct"]), 6
            ),
            "base_greedy_correct": base["greedy_correct"],
            "thinking_greedy_correct": thinking["greedy_correct"],
            "base_greedy_answer": base["greedy_answer"],
            "thinking_greedy_answer": thinking["greedy_answer"],
            "thinking_greedy_extract_status": thinking.get(
                "greedy_thinking_extract_status", ""
            ),
            "sampled_post_think": statuses.get("post_think", 0),
            "sampled_no_thinking_tags": statuses.get("no_thinking_tags", 0),
            "sampled_unterminated_thinking": statuses.get(
                "unterminated_thinking", 0
            ),
            "answer_value": thinking.get("answer_value"),
        })
    return compared


def summarize(rows: list[dict], *, base_count: int, thinking_count: int) -> dict:
    transitions = Counter(row["label_transition"] for row in rows)
    base_labels = Counter(row["base_label"] for row in rows)
    thinking_labels = Counter(row["thinking_label"] for row in rows)
    greedy_transitions = Counter(
        (row["base_greedy_correct"], row["thinking_greedy_correct"])
        for row in rows
    )
    extract_statuses = Counter()
    for row in rows:
        extract_statuses["post_think"] += row["sampled_post_think"]
        extract_statuses["no_thinking_tags"] += row["sampled_no_thinking_tags"]
        extract_statuses["unterminated_thinking"] += row[
            "sampled_unterminated_thinking"
        ]
    unknown_rows = [row for row in rows if row["base_label"] == "unknown"]
    unknown_became_nonunknown = [
        row for row in unknown_rows if row["thinking_label"] != "unknown"
    ]
    unknown_became_known = [
        row for row in unknown_rows if row["thinking_label"] == "known"
    ]
    return {
        "base_rows": base_count,
        "thinking_rows": thinking_count,
        "joined_rows": len(rows),
        "base_label_counts_joined": dict(base_labels),
        "thinking_label_counts_joined": dict(thinking_labels),
        "label_transitions": dict(transitions),
        "greedy_correct_transitions": {
            f"{before}->{after}": count
            for (before, after), count in greedy_transitions.items()
        },
        "sampled_thinking_extract_status_counts": dict(extract_statuses),
        "base_unknown_rows_joined": len(unknown_rows),
        "base_unknown_became_nonunknown": len(unknown_became_nonunknown),
        "base_unknown_became_known": len(unknown_became_known),
        "base_unknown_became_known_frac": (
            len(unknown_became_known) / len(unknown_rows) if unknown_rows else 0.0
        ),
    }


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0]) if rows else [
        "probe_pool_row_key",
        "question_id",
        "base_label",
        "thinking_label",
        "label_transition",
    ]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--thinking", type=Path, default=DEFAULT_THINKING)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    base_rows = read_jsonl(args.base)
    thinking_rows = read_jsonl(args.thinking)
    rows = compare_rows(base_rows, thinking_rows)
    summary = summarize(
        rows, base_count=len(base_rows), thinking_count=len(thinking_rows)
    )

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_csv(rows, args.out_dir / "row_comparison.csv")
    (args.out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
