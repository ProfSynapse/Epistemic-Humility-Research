#!/usr/bin/env python3
"""Tests for prospective GRPO dataset projection."""

import json
from pathlib import Path
import sys

import yaml

GRPO_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = GRPO_DIR.parents[0] / "data"
sys.path.insert(0, str(GRPO_DIR))
sys.path.insert(0, str(DATA_DIR))

import build_datasets as bd  # noqa: E402
import build_grpo_dataset as bgd  # noqa: E402

FIXTURES = DATA_DIR / "tests" / "fixtures"
PROBE = FIXTURES / "probe_results.jsonl"
CHENG_CLEAN = FIXTURES / "cheng_test_gold_clean.jsonl"
BANK = DATA_DIR / "abstention_bank.json"
CONFIG = DATA_DIR / "config" / "build.yaml"


def _load_config():
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def test_build_grpo_projection_uses_existing_frozen_split(tmp_path):
    paths = {
        "probe_results": PROBE,
        "cheng_test_gold": CHENG_CLEAN,
        "abstention_bank": BANK,
        "output_dir": tmp_path,
        "config": CONFIG,
    }
    bd.build_all(_load_config(), "test-model", paths)

    manifest = bgd.build_grpo_projection(
        probe_results=PROBE,
        frozen_questions=tmp_path / "questions_frozen.json",
        output_dir=tmp_path,
    )

    frozen = json.loads((tmp_path / "questions_frozen.json").read_text(encoding="utf-8"))
    train_rows = _read_jsonl(tmp_path / "grpo_train.jsonl")
    dev_rows = _read_jsonl(tmp_path / "grpo_dev.jsonl")

    assert manifest["train_rows"] == len(frozen["train_question_keys"])
    assert manifest["dev_rows"] == len(frozen["dev_question_keys"])
    assert len(train_rows) == manifest["train_rows"]
    assert len(dev_rows) == manifest["dev_rows"]
    assert train_rows[0]["prompt"][0]["role"] == "system"
    assert "JSON object" in train_rows[0]["prompt"][0]["content"]
    assert train_rows[0]["label"] in {"known", "unknown"}
    assert isinstance(train_rows[0]["aliases"], list)


def test_build_grpo_projection_can_reconstruct_from_triviaqa_source(tmp_path):
    frozen = {
        "known_question_keys": ["000000000001|known_q"],
        "unknown_question_keys": ["000000000002|unknown_q"],
        "train_question_keys": ["000000000001|known_q"],
        "dev_question_keys": ["000000000002|unknown_q"],
    }
    frozen_path = tmp_path / "questions_frozen.json"
    frozen_path.write_text(json.dumps(frozen), encoding="utf-8")

    source_path = tmp_path / "train.jsonl"
    rows = [
        {"question_id": "skip", "question": "skip", "answer": {"normalized_aliases": []}},
        {
            "question_id": "known_q",
            "question": "What is the capital of France?",
            "answer": {"value": "Paris", "normalized_aliases": ["paris"]},
        },
        {
            "question_id": "unknown_q",
            "question": "What is an unrecorded fact?",
            "answer": {"value": "Unknown", "normalized_aliases": ["unknown"]},
        },
    ]
    source_path.write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    missing_probe = tmp_path / "missing_probe_results.jsonl"
    manifest = bgd.build_grpo_projection(
        probe_results=missing_probe,
        frozen_questions=frozen_path,
        triviaqa_train=source_path,
        output_dir=tmp_path,
    )

    train_rows = _read_jsonl(tmp_path / "grpo_train.jsonl")
    dev_rows = _read_jsonl(tmp_path / "grpo_dev.jsonl")
    assert manifest["metadata_source"] == str(source_path)
    assert train_rows[0]["id"] == "000000000001|known_q"
    assert train_rows[0]["aliases"] == ["paris"]
    assert train_rows[0]["answerable"] is True
    assert dev_rows[0]["label"] == "unknown"


def test_build_grpo_projection_can_include_middle_discard_rows(tmp_path):
    frozen = {
        "known_question_keys": ["000000000001|known_q"],
        "unknown_question_keys": ["000000000002|unknown_q"],
        "train_question_keys": ["000000000001|known_q"],
        "dev_question_keys": ["000000000002|unknown_q"],
    }
    frozen_path = tmp_path / "questions_frozen.json"
    frozen_path.write_text(json.dumps(frozen), encoding="utf-8")
    probe_path = tmp_path / "probe_results.jsonl"
    rows = [
        {
            "probe_pool_row_key": "000000000001|known_q",
            "question_id": "known_q",
            "question": "Known?",
            "label": "known",
            "greedy_answer": "Known",
            "p_correct": 1.0,
            "sampled_answers": ["Known"],
            "sampled_correct": [True],
            "normalized_aliases": ["known"],
            "answer_value": "Known",
        },
        {
            "probe_pool_row_key": "000000000002|unknown_q",
            "question_id": "unknown_q",
            "question": "Unknown?",
            "label": "unknown",
            "greedy_answer": "Wrong",
            "p_correct": 0.0,
            "sampled_answers": ["Wrong"],
            "sampled_correct": [False],
            "normalized_aliases": ["unknown"],
            "answer_value": "Unknown",
        },
        {
            "probe_pool_row_key": "000000000003|discard_q",
            "question_id": "discard_q",
            "question": "Ambiguous?",
            "label": "discard",
            "greedy_answer": "Middle",
            "p_correct": 0.5,
            "sampled_answers": ["Middle", "Wrong"],
            "sampled_correct": [True, False],
            "normalized_aliases": ["middle"],
            "answer_value": "Middle",
        },
    ]
    probe_path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")

    manifest = bgd.build_grpo_projection(
        probe_results=probe_path,
        frozen_questions=frozen_path,
        output_dir=tmp_path,
        include_ambiguous_middle=True,
        dev_fraction=0.5,
    )

    all_rows = _read_jsonl(tmp_path / "grpo_train.jsonl") + _read_jsonl(tmp_path / "grpo_dev.jsonl")
    ambiguous = [row for row in all_rows if row["label"] == "ambiguous"]
    assert manifest["ambiguous_middle"]["rows"] == 1
    assert ambiguous[0]["p_correct"] == 0.5
    assert ambiguous[0]["gold_answer"] == "Middle"
