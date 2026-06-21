#!/usr/bin/env python3
"""Print a deterministic sanity table for the Amendment B GRPO reward."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import humility_reward as hr


CASES = [
    {
        "case": "known_correct_high_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "Paris.", "confidence": 0.95},
    },
    {
        "case": "known_correct_low_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "Paris.", "confidence": 0.25},
    },
    {
        "case": "known_over_refusal_high_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "I don't know enough to answer.", "confidence": 0.95},
    },
    {
        "case": "known_over_refusal_low_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "I don't know enough to answer.", "confidence": 0.05},
    },
    {
        "case": "known_wrong_low_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "London.", "confidence": 0.05},
    },
    {
        "case": "known_wrong_high_conf",
        "label": "known",
        "aliases": ["paris"],
        "completion": {"answer": "London.", "confidence": 0.95},
    },
    {
        "case": "unknown_abstain_high_conf",
        "label": "unknown",
        "aliases": [],
        "completion": {"answer": "I don't know enough to answer.", "confidence": 0.95},
    },
    {
        "case": "unknown_abstain_low_conf",
        "label": "unknown",
        "aliases": [],
        "completion": {"answer": "I don't know enough to answer.", "confidence": 0.05},
    },
    {
        "case": "unknown_guess_low_conf",
        "label": "unknown",
        "aliases": [],
        "completion": {"answer": "Paris.", "confidence": 0.05},
    },
    {
        "case": "unknown_guess_high_conf",
        "label": "unknown",
        "aliases": [],
        "completion": {"answer": "Paris.", "confidence": 0.95},
    },
    {
        "case": "malformed_known_correct",
        "label": "known",
        "aliases": ["paris"],
        "completion": "Paris.",
    },
]


def _completion_text(value: object) -> str:
    if isinstance(value, dict):
        return json.dumps(value)
    return str(value)


def build_rows() -> list[dict[str, str]]:
    rows = []
    for case in CASES:
        completion = _completion_text(case["completion"])
        score = hr.score_completion(
            completion,
            label=str(case["label"]),
            aliases=list(case["aliases"]),
        )
        parsed = hr.parse_completion(completion)
        rows.append(
            {
                "case": str(case["case"]),
                "label": str(case["label"]),
                "valid_json": str(parsed.valid_json).lower(),
                "refused": str(hr.is_refusal(parsed.answer_text)).lower(),
                "confidence": "" if parsed.stated_confidence is None else f"{parsed.stated_confidence:.3f}",
                "reward": f"{score:.6f}",
                "answer_text": parsed.answer_text,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional CSV output path.")
    args = parser.parse_args(argv)

    rows = build_rows()
    fieldnames = ["case", "label", "valid_json", "refused", "confidence", "reward", "answer_text"]

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    writer = csv.DictWriter(__import__("sys").stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
