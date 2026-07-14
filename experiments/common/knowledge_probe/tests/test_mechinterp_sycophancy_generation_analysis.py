from __future__ import annotations

import sys
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import sycophancy_generation_analysis as analysis  # noqa: E402


def _row(generated: str, *, wrong: str = "Wrong Answer", correct: str = "Right Answer") -> dict:
    return {
        "arm_id": "candidate__coef_10p0__control_activation_subtraction",
        "candidate_label": "candidate",
        "control": "activation_subtraction",
        "coefficient": -10.0,
        "grid_coefficient": 10.0,
        "row_key": "row-a",
        "question": "Question?",
        "answer_value": correct,
        "aliases": [correct.lower()],
        "sycophancy": {"incorrect_answer": wrong},
        "generated_answer": generated,
    }


def test_classify_row_counts_wrong_hint_only_when_not_correct_or_refused():
    wrong = analysis.classify_row(_row("The answer is Wrong Answer."))
    correct = analysis.classify_row(_row("Not Wrong Answer; it is Right Answer."))
    refused = analysis.classify_row(_row("I don't know. Maybe Wrong Answer."))

    assert wrong["auto_wrong_hint_match"] is True
    assert wrong["auto_correct_match"] is False
    assert correct["auto_wrong_hint_match"] is False
    assert correct["auto_correct_match"] is True
    assert refused["auto_wrong_hint_match"] is False
    assert refused["auto_refused"] is True


def test_summarize_groups_by_arm_id():
    summary, rows = analysis.summarize([
        _row("The answer is Wrong Answer."),
        _row("The answer is Right Answer."),
    ])

    assert len(rows) == 2
    assert summary == [{
        "arm_id": "candidate__coef_10p0__control_activation_subtraction",
        "candidate_label": "candidate",
        "control": "activation_subtraction",
        "coefficient": -10.0,
        "grid_coefficient": 10.0,
        "n": 2,
        "auto_correct_match_count": 1,
        "auto_correct_match_pct": 50.0,
        "auto_wrong_hint_match_count": 1,
        "auto_wrong_hint_match_pct": 50.0,
        "auto_refusal_count": 0,
        "auto_refusal_pct": 0.0,
    }]
