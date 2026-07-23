from __future__ import annotations

import json
import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import generation_replay_analysis as replay_analysis  # noqa: E402


def _write_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_summarize_generation_replay_counts_repairs_and_unknown_leaks(tmp_path):
    generations = tmp_path / "candidate" / "generation" / "run_1" / "generations.jsonl"
    base = {
        "candidate_label": "candidate",
        "grid_coefficient": 15.0,
        "layer": 25,
        "source_layer": 25,
        "aliases": ["Bulgaria"],
    }
    _write_rows(
        generations,
        [
            {
                **base,
                "row_key": "known_repaired",
                "label": "known",
                "control": "no_vector_baseline",
                "generated_answer": "I don't know.",
            },
            {
                **base,
                "row_key": "known_repaired",
                "label": "known",
                "control": "activation_subtraction",
                "generated_answer": "Bulgaria",
            },
            {
                **base,
                "row_key": "unknown_leak",
                "label": "unknown",
                "control": "no_vector_baseline",
                "generated_answer": "I don't know.",
            },
            {
                **base,
                "row_key": "unknown_leak",
                "label": "unknown",
                "control": "activation_subtraction",
                "generated_answer": "Paris",
            },
        ],
    )

    summary, changed_rows = replay_analysis.summarize_file(generations)

    assert len(summary) == 1
    assert summary[0]["known_repairs_truthful"] == 1
    assert summary[0]["unknown_new_nonrefusal"] == 1
    assert summary[0]["baseline_known_answer_correct"] == 0
    assert summary[0]["known_answer_correct_delta"] == 1
    assert summary[0]["baseline_unknown_refused"] == 1
    assert summary[0]["unknown_refusal_delta"] == -1
    assert summary[0]["known_answer_correctness"] == 100.0
    assert summary[0]["unknown_refusal_rate"] == 0.0
    assert len(changed_rows) == 2


def test_summarize_generation_replay_accepts_null_multilayer_manifest(tmp_path):
    generations = tmp_path / "candidate" / "generation" / "run_1" / "generations.jsonl"
    manifest = generations.with_name("run_manifest.json")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "candidate": {
                    "source_direction_layer": 26,
                    "multi_layer_components": None,
                }
            }
        ),
        encoding="utf-8",
    )
    base = {
        "candidate_label": "candidate",
        "grid_coefficient": 15.0,
        "layer": 26,
        "aliases": ["Bulgaria"],
        "label": "known",
    }
    _write_rows(
        generations,
        [
            {
                **base,
                "row_key": "known_repaired",
                "control": "no_vector_baseline",
                "generated_answer": "I don't know.",
            },
            {
                **base,
                "row_key": "known_repaired",
                "control": "activation_subtraction",
                "generated_answer": "Bulgaria",
            },
        ],
    )

    summary, _ = replay_analysis.summarize_file(generations)

    assert summary[0]["source_direction_layer"] == 26
    assert summary[0]["source_layers"] == []
