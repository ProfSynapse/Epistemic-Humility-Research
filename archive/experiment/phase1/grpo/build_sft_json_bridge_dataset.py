#!/usr/bin/env python3
"""Build a small SFT bridge dataset for GRPO's answer/confidence JSON contract.

The bridge keeps the existing GRPO prompt contract and adds an assistant target:

  {"answer": "<gold or abstention>", "confidence": <0..1>}

Confidence is response confidence: high when the answer or abstention is the
appropriate response.

This is an Amendment B format bridge, not a replacement for the locked Phase 1
SFT/DPO/KTO datasets.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _target_for_row(row: dict[str, Any]) -> dict[str, Any]:
    label = str(row.get("label", "")).strip().lower()
    if label == "known":
        answer = str(row.get("gold_answer") or "").strip()
        if not answer:
            aliases = row.get("aliases") or []
            answer = str(aliases[0]) if aliases else ""
        if not answer:
            raise ValueError(f"known row lacks gold answer/aliases: {row.get('id')}")
        return {"answer": answer, "confidence": 1.0}
    if label == "unknown":
        return {"answer": "I don't know the answer", "confidence": 1.0}
    raise ValueError(f"unsupported row label {label!r} for row {row.get('id')}")


def build_bridge_rows(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    selected = rows[:limit] if limit else rows
    bridge_rows: list[dict[str, Any]] = []
    for row in selected:
        prompt = row.get("prompt")
        if not isinstance(prompt, list) or not prompt:
            raise ValueError(f"row lacks chat prompt: {row.get('id')}")
        target = _target_for_row(row)
        bridge_rows.append(
            {
                "messages": [
                    *prompt,
                    {
                        "role": "assistant",
                        "content": json.dumps(target, ensure_ascii=False, separators=(",", ": ")),
                    },
                ],
                "id": row.get("id"),
                "question_id": row.get("question_id"),
                "label": row.get("label"),
                "bridge_target": "answer_confidence_json",
            }
        )
    return bridge_rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl",
        help="Input GRPO train JSONL.",
    )
    parser.add_argument(
        "--output",
        default="scratch/grpo_bootstrap/qwen3-4b-instruct/sft_json_bridge_train.jsonl",
        help="Output SFT bridge JSONL.",
    )
    parser.add_argument("--limit", type=int, help="Optional first-N row limit for a smoke bridge.")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    bridge_rows = build_bridge_rows(_read_jsonl(input_path), limit=args.limit)
    _write_jsonl(output_path, bridge_rows)
    known = sum(1 for row in bridge_rows if row.get("label") == "known")
    unknown = sum(1 for row in bridge_rows if row.get("label") == "unknown")
    print(
        json.dumps(
            {
                "input": str(input_path),
                "output": str(output_path),
                "rows": len(bridge_rows),
                "known": known,
                "unknown": unknown,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
