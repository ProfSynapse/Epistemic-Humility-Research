from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import sae_behavior_feature_analysis as behavior_analysis  # noqa: E402


def _row(
    row_key: str,
    *,
    label: str,
    refused: bool,
    correct: bool,
    confidence: float,
    wrong_hint_match: bool = False,
) -> dict:
    return {
        "row_key": row_key,
        "label": label,
        "question": f"Question {row_key}",
        "strata": [],
        "source_arms": {
            "fixture_arm": {
                "answer_text": "I don't know" if refused else "Answer",
                "refused": refused,
                "correct": correct,
                "truthful": correct,
                "stated_confidence": confidence,
                "wrong_hint_match": wrong_hint_match,
            }
        },
    }


def test_row_matches_filter_uses_target_arm_behavior():
    row = _row("u1", label="unknown", refused=True, correct=False, confidence=0.0)

    assert behavior_analysis.row_matches_filter(
        row,
        "fixture_arm",
        {"label": "unknown", "refused": True, "confidence_max": 0.25},
    )
    assert not behavior_analysis.row_matches_filter(row, "fixture_arm", {"label": "known"})
    assert not behavior_analysis.row_matches_filter(row, "fixture_arm", {"refused": False})
    assert not behavior_analysis.row_matches_filter(row, "fixture_arm", {"confidence_min": 0.75})


def test_row_matches_filter_supports_wrong_hint_match():
    row = _row(
        "known_wrong_hint",
        label="known",
        refused=False,
        correct=False,
        confidence=0.95,
        wrong_hint_match=True,
    )

    assert behavior_analysis.row_matches_filter(row, "fixture_arm", {"wrong_hint_match": True})
    assert not behavior_analysis.row_matches_filter(row, "fixture_arm", {"wrong_hint_match": False})


def test_rank_features_for_behavior_contrast_orders_by_effect_size():
    rows = [
        _row("u_refused_1", label="unknown", refused=True, correct=False, confidence=0.0),
        _row("u_refused_2", label="unknown", refused=True, correct=False, confidence=0.1),
        _row("u_answered_1", label="unknown", refused=False, correct=False, confidence=0.9),
        _row("u_answered_2", label="unknown", refused=False, correct=False, confidence=1.0),
    ]
    codes = np.asarray(
        [
            [5.0, 1.0],
            [4.0, 1.0],
            [0.0, 3.0],
            [0.0, 3.0],
        ],
        dtype=np.float32,
    )
    contrast = {
        "name": "unknown_refused_vs_unknown_answered",
        "positive": {"label": "unknown", "refused": True},
        "negative": {"label": "unknown", "refused": False},
        "min_rows_per_group": 2,
    }

    ranked, summary, positive_mask, negative_mask = behavior_analysis.rank_features_for_contrast(
        codes,
        rows,
        arm="fixture_arm",
        contrast=contrast,
    )

    assert summary["skipped"] is False
    assert summary["positive_count"] == 2
    assert summary["negative_count"] == 2
    assert positive_mask.tolist() == [True, True, False, False]
    assert negative_mask.tolist() == [False, False, True, True]
    assert ranked[0]["feature"] == 0
    assert ranked[0]["mean_diff_positive_minus_negative"] > 0.0


def test_rank_features_skips_insufficient_groups():
    rows = [
        _row("u_refused_1", label="unknown", refused=True, correct=False, confidence=0.0),
        _row("u_answered_1", label="unknown", refused=False, correct=False, confidence=1.0),
    ]
    codes = np.zeros((2, 2), dtype=np.float32)
    contrast = {
        "name": "needs_more_rows",
        "positive": {"label": "unknown", "refused": True},
        "negative": {"label": "unknown", "refused": False},
        "min_rows_per_group": 2,
    }

    ranked, summary, _positive_mask, _negative_mask = behavior_analysis.rank_features_for_contrast(
        codes,
        rows,
        arm="fixture_arm",
        contrast=contrast,
    )

    assert ranked == []
    assert summary["skipped"] is True
    assert summary["reason"] == "insufficient_rows"


def test_row_arm_fails_closed_on_missing_arm():
    row = _row("u1", label="unknown", refused=True, correct=False, confidence=0.0)

    with pytest.raises(behavior_analysis.SaeBehaviorFeatureAnalysisError, match="missing source arm"):
        behavior_analysis.row_arm(row, "missing")
