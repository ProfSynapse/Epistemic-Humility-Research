#!/usr/bin/env python3
"""Tests for schema-aware response-confidence dataset projections."""

from pathlib import Path
import json
import sys

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import build_schema_response_confidence_datasets as builder  # noqa: E402


def _payload(content: str) -> dict:
    return json.loads(content)


def test_build_sft_rows_wraps_assistant_with_response_confidence():
    rows = [
        {
            "conversations": [
                {"role": "system", "content": "old"},
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "A."},
            ]
        }
    ]

    out = builder.build_sft_rows(rows)

    assert "response_confidence" in out[0]["messages"][0]["content"]
    assistant = _payload(out[0]["messages"][-1]["content"])
    assert assistant == {"answer": "A.", "response_confidence": 0.8}


def test_build_sft_rows_uses_probe_scaled_response_confidence():
    rows = [
        {
            "conversations": [
                {"role": "system", "content": "old"},
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "I don't know the answer."},
            ]
        },
        {
            "conversations": [
                {"role": "system", "content": "old"},
                {"role": "user", "content": "Known?"},
                {"role": "assistant", "content": "A."},
            ]
        },
    ]
    probes = [
        {
            "probe_pool_row_key": "unknown-key",
            "label": "unknown",
            "p_correct": 0.0,
            "n_samples": 32,
            "sampled_correct": [False] * 32,
        },
        {
            "probe_pool_row_key": "known-key",
            "label": "known",
            "p_correct": 1.0,
            "n_samples": 32,
            "sampled_correct": [True] * 32,
        },
    ]

    out = builder.build_sft_rows(rows, probe_records=probes)

    assert _payload(out[0]["messages"][-1]["content"]) == {
        "answer": "I don't know the answer.",
        "response_confidence": 0.8765,
    }
    assert out[0]["probe_pool_row_key"] == "unknown-key"
    assert out[0]["source_label"] == "unknown"
    assert _payload(out[1]["messages"][-1]["content"]) == {
        "answer": "A.",
        "response_confidence": 0.8765,
    }
    assert out[1]["probe_pool_row_key"] == "known-key"
    assert out[1]["source_label"] == "known"


def test_build_dpo_rows_wraps_chosen_and_rejected_bands():
    rows = [
        {
            "prompt": [{"role": "user", "content": "Q?"}],
            "chosen": [{"role": "assistant", "content": "Good."}],
            "rejected": [{"role": "assistant", "content": "Bad."}],
        }
    ]

    out = builder.build_dpo_rows(rows)

    chosen = _payload(out[0]["chosen"][0]["content"])
    rejected = _payload(out[0]["rejected"][0]["content"])
    assert chosen == {"answer": "Good.", "response_confidence": 0.8}
    assert rejected == {"answer": "Bad.", "response_confidence": 0.2}


def test_build_kto_rows_uses_label_for_confidence_band():
    rows = [
        {
            "conversations": [
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "Good."},
            ],
            "label": True,
        },
        {
            "conversations": [
                {"role": "user", "content": "Q?"},
                {"role": "assistant", "content": "Bad."},
            ],
            "label": False,
        },
    ]

    out = builder.build_kto_rows(rows)

    assert _payload(out[0]["conversations"][-1]["content"])["response_confidence"] == 0.8
    assert _payload(out[1]["conversations"][-1]["content"])["response_confidence"] == 0.2


def test_ambiguous_middle_rows_use_p_correct_band():
    rows = [
        {
            "question": "Who?",
            "answer_value": "Paris",
            "p_correct": 0.5,
            "n_samples": 32,
            "sampled_answers": ["Paris"] * 16 + ["London"] * 16,
            "sampled_correct": [True] * 16 + [False] * 16,
        }
    ]

    sft = builder.build_ambiguous_sft_rows(rows)
    dpo = builder.build_ambiguous_dpo_rows(rows)
    kto = builder.build_ambiguous_kto_rows(rows)

    assert _payload(sft[0]["messages"][-1]["content"]) == {
        "answer": "Paris",
        "response_confidence": 0.5,
    }
    assert _payload(dpo[0]["chosen"][0]["content"])["response_confidence"] == 0.5
    assert _payload(dpo[0]["rejected"][0]["content"])["response_confidence"] == 0.5
    assert _payload(kto[0]["conversations"][-1]["content"])["response_confidence"] == 0.5
    assert kto[0]["label"] is True
    assert kto[1]["label"] is False


def test_normal_and_ambiguous_rows_have_stable_columns():
    normal_sft = [
        {
            "conversations": [
                {"role": "user", "content": "Known?"},
                {"role": "assistant", "content": "Known answer."},
            ]
        }
    ]
    normal_dpo = [
        {
            "prompt": [{"role": "user", "content": "Known?"}],
            "chosen": [{"role": "assistant", "content": "Known answer."}],
            "rejected": [{"role": "assistant", "content": "I don't know."}],
        }
    ]
    normal_kto = [
        {
            "conversations": [
                {"role": "user", "content": "Known?"},
                {"role": "assistant", "content": "Known answer."},
            ],
            "label": True,
        }
    ]
    ambiguous = [
        {
            "question": "Ambiguous?",
            "answer_value": "Maybe",
            "p_correct": 0.5,
            "sampled_answers": ["Wrong"],
            "sampled_correct": [False],
        }
    ]

    sft_rows = builder.build_sft_rows(normal_sft) + builder.build_ambiguous_sft_rows(ambiguous)
    dpo_rows = builder.build_dpo_rows(normal_dpo) + builder.build_ambiguous_dpo_rows(ambiguous)
    kto_rows = builder.build_kto_rows(normal_kto) + builder.build_ambiguous_kto_rows(ambiguous)

    for rows in (sft_rows, dpo_rows, kto_rows):
        expected_keys = set(rows[0])
        assert expected_keys
        assert all(set(row) == expected_keys for row in rows)

    assert sft_rows[0]["source_label"] == ""
    assert sft_rows[0]["p_correct"] == -1.0
    assert dpo_rows[0]["source_label"] == ""
    assert dpo_rows[0]["p_correct"] == -1.0
    assert kto_rows[0]["source_label"] == ""
    assert kto_rows[0]["p_correct"] == -1.0
