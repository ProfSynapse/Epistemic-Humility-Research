#!/usr/bin/env python3
"""Tests for the prospective GRPO epistemic-humility reward."""

from pathlib import Path
import sys
import json

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import humility_reward as hr  # noqa: E402


def test_parse_completion_splits_final_confidence():
    parsed = hr.parse_completion(json.dumps({"answer": "Paris.", "confidence": 0.73}))
    assert parsed.answer_text == "Paris."
    assert parsed.stated_confidence == 0.73


def test_parse_completion_accepts_ten_point_scale():
    parsed = hr.parse_completion(json.dumps({"answer": "Paris.", "confidence": 7}))
    assert parsed.stated_confidence == 0.7


def test_confidence_line_is_not_parsed_as_structured_confidence():
    parsed = hr.parse_completion("Paris.\nConfidence: 0.73")
    assert parsed.answer_text == "Paris.\nConfidence: 0.73"
    assert parsed.stated_confidence is None


def test_known_correct_high_confidence_beats_over_refusal_and_wrong():
    correct = hr.score_completion(
        json.dumps({"answer": "Paris.", "confidence": 0.95}),
        label="known",
        aliases=["paris"],
    )
    refused = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "confidence": 0.05}),
        label="known",
        aliases=["paris"],
    )
    wrong = hr.score_completion(
        json.dumps({"answer": "London.", "confidence": 0.95}),
        label="known",
        aliases=["paris"],
    )
    assert correct > refused
    assert correct > wrong
    assert refused > wrong


def test_unknown_abstention_beats_low_confidence_guess():
    abstain = hr.score_completion(
        json.dumps({"answer": "I don't know the answer.", "confidence": 0.05}),
        label="unknown",
        aliases=[],
    )
    guess = hr.score_completion(
        json.dumps({"answer": "The answer is Paris.", "confidence": 0.05}),
        label="unknown",
        aliases=[],
    )
    assert abstain > guess


def test_confident_wrong_is_worse_than_low_confidence_wrong():
    low = hr.score_completion(
        json.dumps({"answer": "London.", "confidence": 0.05}),
        label="known",
        aliases=["paris"],
    )
    high = hr.score_completion(
        json.dumps({"answer": "London.", "confidence": 0.95}),
        label="known",
        aliases=["paris"],
    )
    assert high < low


def test_generic_hedging_penalized_on_known_correct_answer():
    clean = hr.score_completion(
        json.dumps({"answer": "Paris.", "confidence": 0.95}),
        label="known",
        aliases=["paris"],
    )
    hedged = hr.score_completion(
        json.dumps({"answer": "I think the answer is Paris.", "confidence": 0.95}),
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
