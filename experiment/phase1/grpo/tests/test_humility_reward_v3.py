#!/usr/bin/env python3
"""Tests for the GRPO epistemic-humility reward v3 (proper-scoring confidence)."""

import json
import sys
from pathlib import Path

GRPO_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRPO_DIR))

import pytest  # noqa: E402

import humility_reward_v3 as hr  # noqa: E402


def _payload(answer: str, confidence: float) -> str:
    return json.dumps({"answer": answer, "response_confidence": confidence})


REFUSAL = "I don't know the answer"


# --- proper score shape ----------------------------------------------------

def test_proper_score_peaks_at_target():
    w = 1.2
    at = hr._proper_score(0.4, 0.4, w)
    near = hr._proper_score(0.5, 0.4, w)
    far = hr._proper_score(0.9, 0.4, w)
    assert at == pytest.approx(w)
    assert at > near > far


def test_score_is_maximized_at_target_confidence():
    grid = [i / 20 for i in range(1, 20)]
    target = 0.35
    best = max(grid, key=lambda c: hr.score_completion(
        _payload("Paris", c), label="known", aliases=["Paris"], p_target=target))
    assert abs(best - target) <= 0.05


# --- THE FIX: calibrated per-prompt confidence beats a collapsed constant ---

def test_calibrated_beats_flat_on_easy_prompt():
    # easy prompt: group all-correct -> target 1.0; stating 0.95 should beat 0.82
    cal = hr.score_completion(_payload("Paris", 0.95), label="known", aliases=["Paris"], p_target=1.0)
    flat = hr.score_completion(_payload("Paris", 0.82), label="known", aliases=["Paris"], p_target=1.0)
    assert cal > flat


def test_calibrated_beats_flat_on_hard_prompt():
    # hard prompt: group mostly wrong -> target ~0.33; stating 0.33 should beat 0.82
    cal = hr.score_completion(_payload("Paris", 0.33), label="known", aliases=["Paris"], p_target=0.33)
    flat = hr.score_completion(_payload("Paris", 0.82), label="known", aliases=["Paris"], p_target=0.33)
    assert cal > flat


# --- behavior still dominates ----------------------------------------------

def test_behavior_ordering_preserved_regardless_of_confidence():
    kc = hr.score_completion(_payload("Paris", 0.8), label="known", aliases=["Paris"])
    ua = hr.score_completion(_payload(REFUSAL, 0.8), label="unknown")
    kw = hr.score_completion(_payload("London", 0.5), label="known", aliases=["Paris"])
    kor = hr.score_completion(_payload(REFUSAL, 0.5), label="known", aliases=["Paris"])
    assert kc > ua > kw > kor


def test_known_over_refusal_stays_bad_even_with_humble_confidence():
    # low confidence cannot rescue an over-refusal
    kor = hr.score_completion(_payload(REFUSAL, 0.15), label="known", aliases=["Paris"])
    assert kor < 0.0


# --- outcome-mode appropriateness target -----------------------------------

def test_outcome_mode_rewards_high_confidence_on_correct():
    hi = hr.score_completion(_payload("Paris", 0.9), label="known", aliases=["Paris"])
    lo = hr.score_completion(_payload("Paris", 0.4), label="known", aliases=["Paris"])
    assert hi > lo  # appropriate -> target 1.0


def test_outcome_mode_rewards_low_confidence_on_unknown_guess():
    # answering an unknown is inappropriate (target 0.0) -> low confidence scores better
    hi = hr.score_completion(_payload("Atlantis", 0.9), label="unknown")
    lo = hr.score_completion(_payload("Atlantis", 0.1), label="unknown")
    assert lo > hi


# --- target resolution modes -----------------------------------------------

def _texts():
    return [_payload("Paris", 0.9), _payload("Paris", 0.9), _payload("London", 0.9)]


def test_group_target_is_prompt_appropriateness_rate():
    cfg = hr.RewardConfigV3(target_mode="group")
    targets = hr._resolve_targets(
        completions_text=_texts(), labels=["known"] * 3, aliases=[["Paris"]] * 3,
        prompts=["q", "q", "q"], group_ids=None, internal=None, config=cfg)
    assert targets == pytest.approx([2 / 3, 2 / 3, 2 / 3])


def test_outcome_mode_targets_are_none():
    cfg = hr.RewardConfigV3(target_mode="outcome")
    targets = hr._resolve_targets(
        completions_text=_texts(), labels=["known"] * 3, aliases=[["Paris"]] * 3,
        prompts=None, group_ids=None, internal=None, config=cfg)
    assert targets == [None, None, None]


def test_internal_mode_uses_passed_column():
    cfg = hr.RewardConfigV3(target_mode="internal")
    targets = hr._resolve_targets(
        completions_text=_texts()[:2], labels=["known"] * 2, aliases=[["Paris"]] * 2,
        prompts=None, group_ids=None, internal=[0.3, 0.7], config=cfg)
    assert targets == pytest.approx([0.3, 0.7])


def test_internal_mode_requires_column():
    cfg = hr.RewardConfigV3(target_mode="internal")
    with pytest.raises(ValueError):
        hr._resolve_targets(
            completions_text=_texts()[:1], labels=["known"], aliases=[["Paris"]],
            prompts=None, group_ids=None, internal=None, config=cfg)


def test_blend_mixes_group_and_internal():
    cfg = hr.RewardConfigV3(target_mode="blend", internal_blend=0.5)
    targets = hr._resolve_targets(
        completions_text=_texts(), labels=["known"] * 3, aliases=[["Paris"]] * 3,
        prompts=["q", "q", "q"], group_ids=None, internal=[0.0, 0.0, 0.0], config=cfg)
    # group=2/3, internal=0 -> blend 1/3
    assert targets == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_unknown_target_mode_raises():
    cfg = hr.RewardConfigV3(target_mode="nope")
    with pytest.raises(ValueError):
        hr._resolve_targets(
            completions_text=_texts()[:1], labels=["known"], aliases=[["Paris"]],
            prompts=None, group_ids=None, internal=None, config=cfg)


# --- penalties -------------------------------------------------------------

def test_endpoint_confidence_is_penalized():
    mid = hr.score_completion(_payload("Paris", 0.9), label="known", aliases=["Paris"])
    one = hr.score_completion(_payload("Paris", 1.0), label="known", aliases=["Paris"])
    zero = hr.score_completion(_payload("Paris", 0.0), label="known", aliases=["Paris"])
    assert mid > one
    assert mid > zero


def test_invalid_json_is_penalized():
    valid = hr.score_completion(_payload("Paris", 0.8), label="known", aliases=["Paris"])
    invalid = hr.score_completion("Paris (no json)", label="known", aliases=["Paris"])
    assert valid > invalid


# --- TRL entry -------------------------------------------------------------

def test_trl_reward_returns_one_score_per_completion():
    reward_fn = hr.make_reward(hr.RewardConfigV3(target_mode="group"))
    completions = _texts()
    rewards = reward_fn(completions, prompts=["q", "q", "q"],
                        label="known", aliases=["Paris"])
    assert len(rewards) == 3
    # two correct + one wrong, all stating 0.9 against a 2/3 target
    assert rewards[0] == pytest.approx(rewards[1])
    assert rewards[0] > rewards[2]  # correct behavior beats wrong


def test_trl_reward_default_closure_callable():
    rewards = hr.epistemic_humility_reward(
        [_payload("Paris", 0.8)], prompts=["q"], label="known", aliases=["Paris"])
    assert len(rewards) == 1
