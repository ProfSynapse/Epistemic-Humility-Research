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


def test_contrastive_sft_rows_include_high_idk_and_low_hallucination():
    rows = [
        {
            "prompt": [{"role": "user", "content": "Unknown?"}],
            "chosen": [{"role": "assistant", "content": "I don't know the answer."}],
            "rejected": [{"role": "assistant", "content": "A made-up answer."}],
        },
        {
            "prompt": [{"role": "user", "content": "Known?"}],
            "chosen": [{"role": "assistant", "content": "Correct answer."}],
            "rejected": [{"role": "assistant", "content": "I am not sure what the answer is."}],
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

    out = builder.build_contrastive_sft_rows(rows, probe_records=probes)

    unknown_idk = _payload(out[0]["messages"][-1]["content"])
    unknown_hallucination = _payload(out[1]["messages"][-1]["content"])
    known_answer = _payload(out[2]["messages"][-1]["content"])
    known_over_refusal = _payload(out[3]["messages"][-1]["content"])
    assert unknown_idk["answer"] == "I don't know the answer."
    assert 0.7 <= unknown_idk["response_confidence"] <= 0.9
    assert unknown_hallucination["answer"] == "A made-up answer."
    assert 0.1 <= unknown_hallucination["response_confidence"] <= 0.35
    assert known_answer["answer"] == "Correct answer."
    assert 0.7 <= known_answer["response_confidence"] <= 0.9
    assert known_over_refusal["answer"] == "I am not sure what the answer is."
    assert 0.1 <= known_over_refusal["response_confidence"] <= 0.35
    assert out[0]["response_confidence_role"] == "appropriate"
    assert out[1]["response_confidence_role"] == "inappropriate"


def test_contrastive_sft_emits_loss_mask_text_on_inappropriate_rows_only():
    rows = [
        {
            "prompt": [{"role": "user", "content": "Unknown?"}],
            "chosen": [{"role": "assistant", "content": "I don't know the answer."}],
            "rejected": [{"role": "assistant", "content": "A made-up answer."}],
        }
    ]
    probes = [
        {
            "probe_pool_row_key": "unknown-key",
            "label": "unknown",
            "p_correct": 0.0,
            "n_samples": 32,
            "sampled_correct": [False] * 32,
        }
    ]

    out = builder.build_contrastive_sft_rows(rows, probe_records=probes)
    appropriate, inappropriate = out[0], out[1]

    # appropriate rows are fully supervised -> no mask directive
    assert appropriate["response_confidence_role"] == "appropriate"
    assert "loss_mask_text" not in appropriate

    # inappropriate rows carry the exact rendered answer value to mask
    assert inappropriate["response_confidence_role"] == "inappropriate"
    assert inappropriate["loss_mask_text"] == ["A made-up answer."]
    # and the span occurs verbatim inside the rendered assistant JSON
    rendered = inappropriate["messages"][-1]["content"]
    assert inappropriate["loss_mask_text"][0] in rendered
    # the masked span does NOT include the response_confidence key
    assert "response_confidence" not in inappropriate["loss_mask_text"][0]


def test_contrastive_sft_spreads_repeated_targets_without_row_dropping():
    rows = []
    probes = []
    for idx in range(50):
        rows.append(
            {
                "prompt": [{"role": "user", "content": f"Unknown {idx}?"}],
                "chosen": [{"role": "assistant", "content": "I don't know the answer."}],
                "rejected": [{"role": "assistant", "content": f"Wrong answer {idx}."}],
            }
        )
        probes.append(
            {
                "probe_pool_row_key": f"unknown-{idx}",
                "label": "unknown",
                "p_correct": 0.0,
                "n_samples": 32,
                "sampled_correct": [False] * 32,
            }
        )

    out = builder.build_contrastive_sft_rows(rows, probe_records=probes)

    values = [
        _payload(row["messages"][-1]["content"])["response_confidence"]
        for row in out
    ]
    assert len(out) == 100
    assert len(set(values)) > 80
    assert all(0.1 <= value <= 0.9 for value in values)


def test_clean_sft_rows_include_only_appropriate_completions_with_spread_targets():
    rows = [
        {
            "conversations": [
                {"role": "system", "content": "old"},
                {"role": "user", "content": "Unknown?"},
                {"role": "assistant", "content": "I don't know the answer."},
            ]
        },
        {
            "conversations": [
                {"role": "system", "content": "old"},
                {"role": "user", "content": "Known?"},
                {"role": "assistant", "content": "Correct answer."},
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

    out = builder.build_clean_sft_rows(rows, probe_records=probes)

    assert len(out) == 2
    unknown = _payload(out[0]["messages"][-1]["content"])
    known = _payload(out[1]["messages"][-1]["content"])
    assert unknown["answer"] == "I don't know the answer."
    assert known["answer"] == "Correct answer."
    assert 0.7 <= unknown["response_confidence"] <= 0.9
    assert 0.7 <= known["response_confidence"] <= 0.9
    assert out[0]["response_confidence_role"] == "appropriate"
    assert out[1]["response_confidence_role"] == "appropriate"
    assert out[0]["source_label"] == "unknown"
    assert out[1]["source_label"] == "known"


def test_clean_sft_rows_do_not_double_rows_or_supervise_rejections():
    rows = []
    probes = []
    for idx in range(50):
        rows.append(
            {
                "conversations": [
                    {"role": "user", "content": f"Q{idx}?"},
                    {"role": "assistant", "content": "I don't know the answer."},
                ]
            }
        )
        probes.append(
            {
                "probe_pool_row_key": f"unknown-{idx}",
                "label": "unknown",
                "p_correct": 0.0,
                "n_samples": 32,
                "sampled_correct": [False] * 32,
            }
        )

    out = builder.build_clean_sft_rows(rows, probe_records=probes)

    values = [
        _payload(row["messages"][-1]["content"])["response_confidence"]
        for row in out
    ]
    assert len(out) == 50
    assert len(set(values)) > 40
    assert all(0.7 <= value <= 0.9 for value in values)


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
    clean_sft = builder.build_clean_ambiguous_sft_rows(rows)
    contrastive_sft = builder.build_contrastive_ambiguous_sft_rows(rows)
    dpo = builder.build_ambiguous_dpo_rows(rows)
    kto = builder.build_ambiguous_kto_rows(rows)

    assert _payload(sft[0]["messages"][-1]["content"]) == {
        "answer": "Paris",
        "response_confidence": 0.5,
    }
    clean_payload = _payload(clean_sft[0]["messages"][-1]["content"])
    assert clean_payload["answer"] == "Paris"
    assert 0.35 <= clean_payload["response_confidence"] <= 0.6
    assert clean_sft[0]["response_confidence_role"] == "ambiguous_answer"
    contrastive_payload = _payload(contrastive_sft[0]["messages"][-1]["content"])
    assert contrastive_payload["answer"] == "Paris"
    assert 0.35 <= contrastive_payload["response_confidence"] <= 0.6
    assert contrastive_sft[0]["response_confidence_role"] == "ambiguous_answer"
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
