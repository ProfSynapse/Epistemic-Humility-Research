from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_gold_behavior_panel as panel  # noqa: E402


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_gold_behavior_panel_materializes_cells_and_key_files(tmp_path):
    source_rows = tmp_path / "source_rows.jsonl"
    scored_rows = tmp_path / "scored_rows.jsonl"
    _write_jsonl(
        source_rows,
        [
            {"probe_pool_row_key": "k1", "label": "known", "question": "Known refused?"},
            {"probe_pool_row_key": "k2", "label": "known", "question": "Known correct?"},
            {"probe_pool_row_key": "u1", "label": "unknown", "question": "Unknown refused?"},
            {"probe_pool_row_key": "u2", "label": "unknown", "question": "Unknown wrong?"},
        ],
    )
    _write_jsonl(
        scored_rows,
        [
            {
                "probe_pool_row_key": "k1",
                "label": "known",
                "control": "no_vector_baseline",
                "arm_id": "baseline",
                "candidate_label": "fixture",
                "generated_answer": "I don't know",
                "refused": True,
                "correct": False,
                "truthful": False,
                "aliases": ["alpha"],
                "answer_value": "Alpha",
            },
            {
                "probe_pool_row_key": "k2",
                "label": "known",
                "control": "no_vector_baseline",
                "arm_id": "baseline",
                "candidate_label": "fixture",
                "generated_answer": "Beta",
                "refused": False,
                "correct": True,
                "truthful": True,
                "aliases": ["beta"],
                "answer_value": "Beta",
            },
            {
                "probe_pool_row_key": "u1",
                "label": "unknown",
                "control": "no_vector_baseline",
                "arm_id": "baseline",
                "candidate_label": "fixture",
                "generated_answer": "I am not sure.",
                "refused": True,
                "correct": False,
                "truthful": True,
            },
            {
                "probe_pool_row_key": "u2",
                "label": "unknown",
                "control": "no_vector_baseline",
                "arm_id": "baseline",
                "candidate_label": "fixture",
                "generated_answer": "Gamma",
                "refused": False,
                "correct": False,
                "truthful": False,
            },
        ],
    )
    config_path = tmp_path / "panel.yaml"
    output_root = tmp_path / "panel"
    config_path.write_text(
        yaml.safe_dump(
            {
                "source_rows": str(source_rows),
                "scored_rows": str(scored_rows),
                "behavior_arm": "fixture_baseline",
                "arm_id": "baseline",
                "output": {"root": str(output_root)},
                "balanced_panel": {
                    "name": "four_cell",
                    "cells": [
                        "known_refused",
                        "known_correct_answered",
                        "unknown_refused",
                        "unknown_answered_wrong",
                    ],
                    "rows_per_cell": 1,
                },
            }
        ),
        encoding="utf-8",
    )

    summary = panel.materialize_panel(config_path)

    assert summary["ok"] is True
    assert summary["behavior_cell_counts"] == {
        "known_correct_answered": 1,
        "known_refused": 1,
        "unknown_answered_wrong": 1,
        "unknown_refused": 1,
    }
    materialized = [
        json.loads(line)
        for line in (output_root / "rows.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert materialized[0]["source_arms"]["fixture_baseline"]["behavior_cell"] == "known_refused"
    assert materialized[1]["aliases"] == ["beta"]
    assert (output_root / "row_keys" / "known_refused_row_keys.txt").read_text(encoding="utf-8") == "k1\n"
    assert (
        output_root / "row_keys" / "four_cell_row_keys.txt"
    ).read_text(encoding="utf-8").splitlines() == ["k1", "k2", "u1", "u2"]
