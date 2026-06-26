from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_selfaware_behavior_manifest as builder  # noqa: E402


def _row(index: int, label: str, refused: bool, correct: bool, answer: str = "answer") -> dict:
    return {
        "aliases": ["alias"] if label == "known" else [],
        "answer_text": answer,
        "config_sha": "abc123",
        "correct": correct,
        "enable_thinking": False,
        "eval_set": "selfaware",
        "generated_answer": json.dumps({"answer": answer, "response_confidence": 0.7}),
        "generation_attempts": 1,
        "id": f"selfaware-{index + 1}",
        "label": label,
        "method": "test_arm",
        "model": "test-model",
        "question": f"Question {index}?",
        "refused": refused,
        "row_index": index,
        "source": "selfaware",
        "stated_confidence": 0.7,
        "stated_confidence_retry_count": 0,
        "stated_confidence_retry_exhausted": False,
        "truthful": correct or (label == "unknown" and refused),
    }


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_builds_balanced_selfaware_behavior_manifest(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "PROBE_DIR", tmp_path)
    monkeypatch.setattr(builder, "REPO_ROOT", tmp_path)
    scored = tmp_path / "scored_rows.jsonl"
    _write_jsonl(
        scored,
        [
            _row(0, "unknown", False, False, "wrong"),
            _row(1, "unknown", False, False, "wrong two"),
            _row(2, "unknown", True, False, "I don't know"),
            _row(3, "known", False, True, "known"),
        ],
    )
    config = {
        "purpose": "test manifest",
        "behavior_arm": "clean_sft_grpo_v2",
        "inputs": {"scored_rows": str(scored)},
        "sampling": {"seed": 123},
        "quotas": {
            "unknown_answered_wrong": 2,
            "unknown_refused": 1,
            "known_correct_answered": 1,
        },
        "output": {
            "manifest": "out/manifest.json",
            "row_keys_file": "out/row_keys.txt",
            "selected_scored_rows": "out/rows.jsonl",
            "summary": "out/summary.json",
        },
    }

    selected, manifest = builder.select_rows(config)
    builder.write_outputs(config, selected, manifest)

    assert manifest["schema_version"] == "phase3-selfaware-frozen-row-manifest/v1"
    assert manifest["row_count"] == 4
    assert manifest["selected_behavior_cell_counts"] == {
        "known_correct_answered": 1,
        "unknown_answered_wrong": 2,
        "unknown_refused": 1,
    }
    first = manifest["rows"][0]
    assert first["row_key"] == "selfaware::selfaware::000000::selfaware-1"
    assert first["source_arms"]["clean_sft_grpo_v2"]["behavior_cell"] == "unknown_answered_wrong"
    assert (tmp_path / "out" / "row_keys.txt").read_text(encoding="utf-8").splitlines() == [
        "selfaware::selfaware::000000::selfaware-1",
        "selfaware::selfaware::000001::selfaware-2",
        "selfaware::selfaware::000002::selfaware-3",
        "selfaware::selfaware::000003::selfaware-4",
    ]


def test_raises_when_quota_cannot_be_met(tmp_path, monkeypatch):
    monkeypatch.setattr(builder, "PROBE_DIR", tmp_path)
    monkeypatch.setattr(builder, "REPO_ROOT", tmp_path)
    scored = tmp_path / "scored_rows.jsonl"
    _write_jsonl(scored, [_row(0, "unknown", False, False)])
    config = {
        "behavior_arm": "clean_sft_grpo_v2",
        "inputs": {"scored_rows": str(scored)},
        "quotas": {"unknown_answered_wrong": 2},
        "output": {
            "manifest": "out/manifest.json",
            "row_keys_file": "out/row_keys.txt",
            "selected_scored_rows": "out/rows.jsonl",
            "summary": "out/summary.json",
        },
    }

    with pytest.raises(builder.SelfAwareBehaviorManifestError, match="quota"):
        builder.select_rows(config)
