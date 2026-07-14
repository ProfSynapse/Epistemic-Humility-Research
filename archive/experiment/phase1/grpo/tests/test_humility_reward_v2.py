#!/usr/bin/env python3
"""Tests for the GRPO epistemic-humility reward v2."""

from pathlib import Path
import sys
import json

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import humility_reward_v2 as hr  # noqa: E402


def _payload(answer: str, confidence: float) -> str:
    return json.dumps({"answer": answer, "response_confidence": confidence})


def test_v2_known_correct_dominates_unknown_abstention_and_errors():
    known_correct = hr.score_completion(
        _payload("Paris.", 0.82),
        label="known",
        aliases=["paris"],
    )
    unknown_abstain = hr.score_completion(
        _payload("I don't know the answer.", 0.82),
        label="unknown",
        aliases=[],
    )
    known_wrong_low = hr.score_completion(
        _payload("London.", 0.22),
        label="known",
        aliases=["paris"],
    )
    known_overrefusal_low = hr.score_completion(
        _payload("I don't know the answer.", 0.18),
        label="known",
        aliases=["paris"],
    )

    assert known_correct > unknown_abstain > known_wrong_low > known_overrefusal_low


def test_v2_known_over_refusal_is_bad_even_with_low_confidence():
    overrefusal_low = hr.score_completion(
        _payload("I don't know the answer.", 0.18),
        label="known",
        aliases=["paris"],
    )
    wrong_low = hr.score_completion(
        _payload("London.", 0.22),
        label="known",
        aliases=["paris"],
    )
    unknown_guess_low = hr.score_completion(
        _payload("Paris.", 0.18),
        label="unknown",
        aliases=[],
    )

    assert overrefusal_low < wrong_low
    assert overrefusal_low < unknown_guess_low
    assert overrefusal_low < 0.0


def test_v2_confident_known_over_refusal_is_worse_than_low_confidence_over_refusal():
    low = hr.score_completion(
        _payload("I don't know the answer.", 0.18),
        label="known",
        aliases=["paris"],
    )
    high = hr.score_completion(
        _payload("I don't know the answer.", 0.82),
        label="known",
        aliases=["paris"],
    )
    assert high < low


def test_v2_unknown_abstention_prefers_high_response_confidence():
    high = hr.score_completion(
        _payload("I don't know the answer.", 0.82),
        label="unknown",
        aliases=[],
    )
    low = hr.score_completion(
        _payload("I don't know the answer.", 0.2),
        label="unknown",
        aliases=[],
    )
    assert high > low > 0.0


def test_v2_confident_unknown_guess_is_worse_than_low_confidence_guess():
    low = hr.score_completion(
        _payload("Paris.", 0.18),
        label="unknown",
        aliases=[],
    )
    high = hr.score_completion(
        _payload("Paris.", 0.82),
        label="unknown",
        aliases=[],
    )
    assert high < low < 0.0


def test_v2_confidence_target_distance_shapes_correct_known_answers():
    target = hr.score_completion(
        _payload("Paris.", 0.82),
        label="known",
        aliases=["paris"],
    )
    too_low = hr.score_completion(
        _payload("Paris.", 0.22),
        label="known",
        aliases=["paris"],
    )
    endpoint = hr.score_completion(
        _payload("Paris.", 1.0),
        label="known",
        aliases=["paris"],
    )
    assert target > too_low > endpoint


def test_v2_ambiguous_correct_prefers_middle_confidence():
    middle = hr.score_completion(
        _payload("Paris.", 0.5),
        label="ambiguous",
        aliases=["paris"],
    )
    high = hr.score_completion(
        _payload("Paris.", 0.82),
        label="ambiguous",
        aliases=["paris"],
    )
    low = hr.score_completion(
        _payload("Paris.", 0.18),
        label="ambiguous",
        aliases=["paris"],
    )
    assert middle > high
    assert middle > low


def test_v2_malformed_known_correct_is_not_rewarded_like_valid_json():
    valid = hr.score_completion(
        _payload("Paris.", 0.82),
        label="known",
        aliases=["paris"],
    )
    malformed = hr.score_completion("Paris.", label="known", aliases=["paris"])
    known_wrong_low = hr.score_completion(
        _payload("London.", 0.22),
        label="known",
        aliases=["paris"],
    )

    assert valid > malformed
    assert malformed <= known_wrong_low


def test_v2_trl_reward_expands_metadata_for_multiple_generations():
    rewards = hr.epistemic_humility_reward(
        [
            _payload("Paris.", 0.82),
            _payload("I don't know the answer.", 0.18),
            _payload("London.", 0.22),
        ],
        label=["known"],
        aliases=[["paris"]],
    )
    assert len(rewards) == 3
    assert rewards[0] > rewards[2] > rewards[1]
