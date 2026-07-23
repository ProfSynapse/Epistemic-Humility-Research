#!/usr/bin/env python3
"""Tests for the prospective GRPO epistemic-humility reward."""

from pathlib import Path
import sys
import json

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import humility_reward as hr  # noqa: E402


def test_parse_completion_splits_final_confidence():
    parsed = hr.parse_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.73})
    )
    assert parsed.answer_text == "Paris."
    assert parsed.stated_confidence == 0.73
    assert parsed.valid_json is True


def test_parse_completion_accepts_legacy_confidence_key():
    parsed = hr.parse_completion(json.dumps({"answer": "Paris.", "confidence": 0.73}))
    assert parsed.answer_text == "Paris."
    assert parsed.stated_confidence == 0.73
    assert parsed.valid_json is True


def test_parse_completion_rejects_non_amendment_b_json():
    raw = json.dumps({"answer": "Paris.", "response_confidence": 7})
    parsed = hr.parse_completion(raw)
    assert parsed.answer_text == raw
    assert parsed.stated_confidence is None
    assert parsed.valid_json is False


def test_confidence_line_is_not_parsed_as_structured_confidence():
    parsed = hr.parse_completion("Paris.\nConfidence: 0.73")
    assert parsed.answer_text == "Paris.\nConfidence: 0.73"
    assert parsed.stated_confidence is None
    assert parsed.valid_json is False


def test_parse_completion_accepts_json_after_thinking_block():
    parsed = hr.parse_completion(
        '<think>scratchpad</think>\n{"answer": "Paris.", "response_confidence": 0.73}'
    )
    assert parsed.answer_text == "Paris."
    assert parsed.stated_confidence == 0.73
    assert parsed.valid_json is True


def test_known_correct_high_confidence_beats_over_refusal_and_wrong():
    correct = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    refused = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    wrong = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    assert correct > refused
    assert correct > wrong
    assert refused > wrong


def test_unknown_abstention_beats_low_confidence_guess():
    abstain = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.8}),
        label="unknown",
        aliases=[],
    )
    guess = hr.score_completion(
        json.dumps({"answer": "The answer is Paris.", "response_confidence": 0.2}),
        label="unknown",
        aliases=[],
    )
    assert abstain > guess


def test_unknown_abstention_prefers_high_response_confidence():
    high = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.8}),
        label="unknown",
        aliases=[],
    )
    low = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.2}),
        label="unknown",
        aliases=[],
    )
    assert high > low


def test_natural_stated_confidence_abstention_counts_as_refusal():
    assert hr.is_refusal("I don't know enough to answer.") is True
    assert hr.is_refusal("I do not know the exact number.") is True
    assert hr.is_refusal("I'm really not sure what the answer is, so I'd rather not guess.") is True
    assert hr.is_refusal("I'm not confident here.") is True
    assert hr.is_refusal("I do not want to guess.") is True
    assert hr.is_refusal("NONE OF US KNOW THE ANSWER TO THAT ONE.") is True
    assert hr.is_refusal("How can I know the answer to this question?") is True
    assert hr.is_refusal("I can't answer reliably.") is True
    assert hr.is_refusal("Abstain: insufficient information.") is True


def test_semantic_unknown_abstentions_beat_hallucination():
    hallucination = hr.score_completion(
        json.dumps({"answer": "Elinor Muskie.", "response_confidence": 0.8}),
        label="unknown",
        aliases=[],
    )
    for answer in [
        "I'm really not sure what the answer is, so I'd rather not guess.",
        "NONE OF US KNOW THE ANSWER TO THAT ONE.",
        "How can I know the answer to this question?",
        "I can't answer reliably.",
    ]:
        abstain = hr.score_completion(
            json.dumps({"answer": answer, "response_confidence": 0.8}),
            label="unknown",
            aliases=[],
        )
        assert abstain > hallucination


def test_semantic_known_over_refusal_still_penalized():
    correct = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    for answer in [
        "I'm really not sure what the answer is, so I'd rather not guess.",
        "NONE OF US KNOW THE ANSWER TO THAT ONE.",
        "How can I know the answer to this question?",
        "I can't answer reliably.",
    ]:
        over_refusal = hr.score_completion(
            json.dumps({"answer": answer, "response_confidence": 0.8}),
            label="known",
            aliases=["paris"],
        )
        assert correct > over_refusal


def test_confident_wrong_is_worse_than_low_confidence_wrong():
    low = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.2}),
        label="known",
        aliases=["paris"],
    )
    high = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    assert high < low


def test_known_over_refusal_is_less_bad_when_low_confidence():
    low = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.2}),
        label="known",
        aliases=["paris"],
    )
    high = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    assert high < low


def test_reward_keeps_intermediate_low_confidence_errors():
    correct_high = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    over_refusal_low = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "response_confidence": 0.2}),
        label="known",
        aliases=["paris"],
    )
    wrong_low = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.2}),
        label="known",
        aliases=["paris"],
    )
    wrong_high = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )

    assert correct_high > over_refusal_low > wrong_low > wrong_high


def test_malformed_correct_answer_is_not_rewarded_like_valid_json():
    valid = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    malformed = hr.score_completion("Paris.", label="known", aliases=["paris"])
    unknown_abstain = hr.score_completion(
        json.dumps({"answer": "I don't know enough to answer.", "response_confidence": 0.8}),
        label="unknown",
        aliases=[],
    )
    assert malformed < valid
    assert malformed < unknown_abstain


def test_generic_hedging_penalized_on_known_correct_answer():
    clean = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    hedged = hr.score_completion(
        json.dumps({"answer": "I think the answer is Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    assert hedged < clean


def test_trl_reward_expands_metadata_for_multiple_generations():
    rewards = hr.epistemic_humility_reward(
        [
            json.dumps({"answer": "Paris.", "confidence": 0.9}),
            json.dumps({"answer": "London.", "confidence": 0.9}),
        ],
        label=["known"],
        aliases=[["paris"]],
    )
    assert len(rewards) == 2
    assert rewards[0] > rewards[1]


def test_exact_confidence_endpoints_are_not_optimal():
    endpoint = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 1.0}),
        label="known",
        aliases=["paris"],
    )
    banded = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="known",
        aliases=["paris"],
    )
    assert banded > endpoint


def test_ambiguous_correct_prefers_middle_confidence_band():
    middle = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.5}),
        label="ambiguous",
        aliases=["paris"],
    )
    high = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.8}),
        label="ambiguous",
        aliases=["paris"],
    )
    low = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.2}),
        label="ambiguous",
        aliases=["paris"],
    )
    assert middle > high
    assert middle > low


def test_ambiguous_high_confidence_wrong_is_penalized():
    correct_middle = hr.score_completion(
        json.dumps({"answer": "Paris.", "response_confidence": 0.5}),
        label="discard",
        aliases=["paris"],
    )
    wrong_high = hr.score_completion(
        json.dumps({"answer": "London.", "response_confidence": 0.8}),
        label="discard",
        aliases=["paris"],
    )
    assert correct_middle > wrong_high
