#!/usr/bin/env python3
"""Tests for GRPO smoke subset construction."""

import json
from pathlib import Path
import sys

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import make_smoke_subset as subset  # noqa: E402


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_build_subset_can_include_ambiguous_label(tmp_path):
    input_path = tmp_path / "train.jsonl"
    output_path = tmp_path / "smoke.jsonl"
    rows = [
        {"id": "known-1", "label": "known"},
        {"id": "unknown-1", "label": "unknown"},
        {"id": "ambiguous-1", "label": "ambiguous"},
        {"id": "known-2", "label": "known"},
        {"id": "unknown-2", "label": "unknown"},
        {"id": "ambiguous-2", "label": "ambiguous"},
    ]
    input_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    counts = subset.build_subset(
        input_path,
        output_path,
        per_label=2,
        labels=["known", "unknown", "ambiguous"],
    )

    assert counts == {"known": 2, "unknown": 2, "ambiguous": 2, "total": 6}
    assert [row["label"] for row in _read_jsonl(output_path)] == [
        "known",
        "unknown",
        "ambiguous",
        "known",
        "unknown",
        "ambiguous",
    ]
