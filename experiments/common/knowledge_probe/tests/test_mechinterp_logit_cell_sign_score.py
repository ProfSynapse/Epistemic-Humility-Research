from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest
import yaml

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import logit_cell_sign_score as score  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_run_config_scores_declared_cell_goals(tmp_path):
    summary = tmp_path / "cell_logit_summary.csv"
    summary.write_text(
        "\n".join(
            [
                "run_label,candidate_label,grid_coefficient,control,behavior_cell,target_group,row_count,probability_sum_delta_mean",
                "run,cand,50,activation_addition,known_refused,refusal_openers,2,-0.2",
                "run,cand,50,activation_addition,unknown_answered_wrong,refusal_openers,2,0.1",
                "run,cand,50,activation_addition,known_correct_answered,refusal_openers,2,0.05",
                "run,cand,50,activation_addition,unknown_refused,refusal_openers,2,-0.03",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    output = tmp_path / "out"
    _write_yaml(
        config,
        {
            "input_summaries": [{"label": "fixture", "path": str(summary)}],
            "score": {
                "cell_goals": [
                    {"behavior_cell": "known_refused", "mode": "decrease"},
                    {"behavior_cell": "unknown_answered_wrong", "mode": "increase"},
                    {"behavior_cell": "known_correct_answered", "mode": "preserve_nonpositive"},
                    {"behavior_cell": "unknown_refused", "mode": "preserve_nonnegative"},
                ]
            },
            "output": {"root": str(output)},
        },
    )

    result = score.run_config(config)

    rows = _read_csv(output / "cell_sign_scores.csv")
    assert result["ok"] is True
    assert result["scored_row_count"] == 1
    assert float(rows[0]["sign_score"]) == pytest.approx(0.22)
    assert rows[0]["all_goals_passed"] == "False"
    assert rows[0]["passed_goal_count"] == "2"
    assert rows[0]["known_refused_passed"] == "True"
    assert rows[0]["unknown_answered_wrong_passed"] == "True"
    assert rows[0]["known_correct_answered_passed"] == "False"
    assert rows[0]["unknown_refused_passed"] == "False"


def test_run_config_fails_on_bad_goal_mode(tmp_path):
    summary = tmp_path / "cell_logit_summary.csv"
    summary.write_text(
        "run_label,candidate_label,grid_coefficient,control,behavior_cell,target_group,probability_sum_delta_mean\n",
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    _write_yaml(
        config,
        {
            "input_summaries": [{"label": "fixture", "path": str(summary)}],
            "score": {"cell_goals": [{"behavior_cell": "known_refused", "mode": "up"}]},
            "output": {"root": str(tmp_path / "out")},
        },
    )

    with pytest.raises(score.LogitCellSignScoreError, match="mode must be one of"):
        score.run_config(config)
