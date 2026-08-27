from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).with_name("qualify.py")
spec = importlib.util.spec_from_file_location("twoway_qualify", MODULE_PATH)
qualify = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = qualify
assert spec.loader is not None
spec.loader.exec_module(qualify)


# --- statistical primitives -------------------------------------------------

def test_wilson_lower_matches_locked_recall_thresholds() -> None:
    # gates.yaml minimum_successes: abstain 114/200, answer 221/402 must clear 0.5;
    # one below each must not.
    assert qualify.wilson_lower(114, 200) > 0.5
    assert qualify.wilson_lower(113, 200) <= 0.5
    assert qualify.wilson_lower(221, 402) > 0.5
    assert qualify.wilson_lower(220, 402) <= 0.5


def test_wilson_lower_degenerate_n() -> None:
    assert qualify.wilson_lower(0, 0) == 0.0


def test_paired_bootstrap_all_positive_is_above_noninferiority_floor() -> None:
    low, high = qualify.paired_bootstrap_ci([1] * 50, seed=20260722, resamples=2000)
    assert low == 1.0 and high == 1.0
    assert low > -0.10


def test_paired_bootstrap_all_zero_straddles_zero_tightly() -> None:
    low, high = qualify.paired_bootstrap_ci([0] * 50, seed=20260722, resamples=2000)
    assert low == 0.0 and high == 0.0


def test_paired_bootstrap_is_seed_deterministic() -> None:
    deltas = [1, 0, -1, 0, 1, 1, 0, -1, 0, 1]
    a = qualify.paired_bootstrap_ci(deltas, seed=20260722, resamples=1000)
    b = qualify.paired_bootstrap_ci(deltas, seed=20260722, resamples=1000)
    c = qualify.paired_bootstrap_ci(deltas, seed=7, resamples=1000)
    assert a == b
    assert a != c


def test_paired_bootstrap_empty_fails_closed() -> None:
    with pytest.raises(qualify.QualificationError):
        qualify.paired_bootstrap_ci([], seed=1, resamples=10)


# --- calibration: AUROC + ECE ----------------------------------------------

def test_auroc_perfect_separation_is_one() -> None:
    scores = [0.1, 0.2, 0.8, 0.9]
    labels = [False, False, True, True]
    assert qualify.discrimination_auroc(scores, labels) == pytest.approx(1.0)


def test_auroc_inverted_is_zero_and_random_is_half() -> None:
    scores = [0.1, 0.2, 0.8, 0.9]
    assert qualify.discrimination_auroc(scores, [True, True, False, False]) == pytest.approx(0.0)
    # tied scores across both classes -> 0.5 via mid-ranks
    assert qualify.discrimination_auroc([0.5, 0.5, 0.5, 0.5], [True, False, True, False]) == pytest.approx(0.5)


def test_auroc_single_class_is_undefined_none() -> None:
    assert qualify.discrimination_auroc([0.3, 0.7], [True, True]) is None
    assert qualify.discrimination_auroc([0.3, 0.7], [False, False]) is None


def test_auroc_clears_locked_bar_on_discriminating_confidence() -> None:
    # confidence tracks correctness with modest noise; AUROC should clear 0.62.
    correct = [0.9, 0.8, 0.75, 0.7, 0.65, 0.6]
    wrong = [0.55, 0.45, 0.4, 0.35, 0.3, 0.2]
    scores = correct + wrong
    labels = [True] * len(correct) + [False] * len(wrong)
    assert qualify.discrimination_auroc(scores, labels) >= 0.62


def test_ece_perfectly_calibrated_is_low() -> None:
    # confidence equals empirical accuracy within each bucket -> ~0 ECE.
    confidences = [0.0, 0.0, 1.0, 1.0]
    labels = [False, False, True, True]
    assert qualify.expected_calibration_error(confidences, labels, buckets=10) < 0.05


def test_ece_worst_case_is_high_and_exceeds_gate() -> None:
    # fully confident but always wrong -> ECE ~1.0, must exceed the 0.30 ceiling.
    confidences = [0.99] * 8
    labels = [False] * 8
    ece = qualify.expected_calibration_error(confidences, labels, buckets=10)
    assert ece > 0.30
    assert ece == pytest.approx(0.99, abs=0.02)


def test_ece_last_bucket_includes_upper_endpoint() -> None:
    # confidence exactly 1.0 must land in the final bucket, not be dropped.
    ece = qualify.expected_calibration_error([1.0], [True], buckets=10)
    assert ece == pytest.approx(0.0)


def test_ece_empty_fails_closed() -> None:
    with pytest.raises(qualify.QualificationError):
        qualify.expected_calibration_error([], [], buckets=10)


# --- payload parsing + posture ---------------------------------------------

def test_parse_payload_valid_two_field_object() -> None:
    payload, sub = qualify._parse_payload('{"answer":"Paris","answer_confidence":0.73}')
    assert payload == {"answer": "Paris", "answer_confidence": 0.73}
    assert sub["json_parse"] and sub["exact_fields"] and sub["confidence_valid"]


def test_parse_payload_rejects_extra_fields_and_out_of_range() -> None:
    _, extra = qualify._parse_payload('{"answer":"x","answer_confidence":0.5,"z":1}')
    assert extra["json_parse"] and not extra["exact_fields"]
    _, oor = qualify._parse_payload('{"answer":"x","answer_confidence":1.5}')
    assert not oor["confidence_valid"]
    _, boolean = qualify._parse_payload('{"answer":"x","answer_confidence":true}')
    assert not boolean["confidence_valid"]


def test_parse_payload_non_object_and_garbage() -> None:
    assert qualify._parse_payload("not json")[0] is None
    assert qualify._parse_payload("[1,2,3]")[0] is None


CONTRACT = {
    "ANSWER": {
        "require_nonempty_substantive_answer": True,
        "forbidden_phrases_casefold": ["i don't know", "not certain"],
    },
    "ABSTAIN": {"exact_answers": ["I don't know reliably."]},
}


def test_posture_answer_accepts_substantive_and_rejects_hedge() -> None:
    good, _ = qualify._posture_ok(
        "ANSWER", {"answer": "Casablanca", "answer_confidence": 0.6},
        {"json_parse": True, "exact_fields": True, "confidence_valid": True}, CONTRACT,
    )
    assert good
    bad, checks = qualify._posture_ok(
        "ANSWER", {"answer": "I don't know", "answer_confidence": 0.6},
        {"json_parse": True, "exact_fields": True, "confidence_valid": True}, CONTRACT,
    )
    assert not bad and not checks["forbidden_phrases_absent"]


def test_posture_abstain_requires_exact_string() -> None:
    ok, _ = qualify._posture_ok(
        "ABSTAIN", {"answer": "I don't know reliably.", "answer_confidence": 0.1},
        {"json_parse": True, "exact_fields": True, "confidence_valid": True}, CONTRACT,
    )
    assert ok
    off, _ = qualify._posture_ok(
        "ABSTAIN", {"answer": "I dunno", "answer_confidence": 0.1},
        {"json_parse": True, "exact_fields": True, "confidence_valid": True}, CONTRACT,
    )
    assert not off


def test_posture_empty_answer_fails_substantive() -> None:
    bad, checks = qualify._posture_ok(
        "ANSWER", {"answer": "   ", "answer_confidence": 0.6},
        {"json_parse": True, "exact_fields": True, "confidence_valid": True}, CONTRACT,
    )
    assert not bad and not checks["nonempty_substantive_answer"]


# --- visible-text stripping (two tokens) -----------------------------------

TOKENS = {"ANSWER": "<ANSWER>", "ABSTAIN": "<ABSTAIN>"}


def test_native_visible_strips_predicted_prefix() -> None:
    visible, prefix_match, stripped = qualify._native_visible_text(
        '<ANSWER>{"answer":"x","answer_confidence":0.5}', "ANSWER", TOKENS
    )
    assert visible == '{"answer":"x","answer_confidence":0.5}'
    assert prefix_match and stripped


def test_native_visible_flags_residual_token() -> None:
    visible, prefix_match, stripped = qualify._native_visible_text(
        '<ANSWER>leak<ABSTAIN>', "ANSWER", TOKENS
    )
    assert visible == "leak<ABSTAIN>"
    assert prefix_match and not stripped


def test_forced_visible_detects_no_residual_tokens() -> None:
    visible, stripped = qualify._forced_visible_text('{"answer":"y","answer_confidence":0.2}', TOKENS)
    assert stripped and visible.startswith("{")
    _, dirty = qualify._forced_visible_text("<ANSWER>oops", TOKENS)
    assert not dirty


def test_mode_names_are_two_way() -> None:
    assert qualify.MODE_NAMES == ("ANSWER", "ABSTAIN")
