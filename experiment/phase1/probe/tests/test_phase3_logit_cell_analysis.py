from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_logit_cell_analysis as analysis  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_run_config_aggregates_by_behavior_cell(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    rows = [
        {
            "probe_pool_row_key": "k-ref",
            "label": "known",
            "source_arms": {"arm": {"refused": True, "correct": False}},
        },
        {
            "probe_pool_row_key": "u-wrong",
            "label": "unknown",
            "source_arms": {"arm": {"refused": False, "correct": False}},
        },
    ]
    rows_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    diagnostics = tmp_path / "diag.jsonl"
    diag_rows = [
        {
            "probe_pool_row_key": "k-ref",
            "candidate_label": "cand",
            "grid_coefficient": 1.0,
            "control": "activation_addition",
            "top1_changed": True,
            "intervention_applied_count": 1,
            "logit_target_metrics": {
                "refusal_openers": {
                    "probability_sum_delta": 0.2,
                    "logit_sum_delta": 1.5,
                }
            },
        },
        {
            "probe_pool_row_key": "u-wrong",
            "candidate_label": "cand",
            "grid_coefficient": 1.0,
            "control": "activation_addition",
            "top1_changed": False,
            "intervention_applied_count": 1,
            "logit_target_metrics": {
                "refusal_openers": {
                    "probability_sum_delta": -0.1,
                    "logit_sum_delta": -0.5,
                }
            },
        },
    ]
    diagnostics.write_text("\n".join(json.dumps(row) for row in diag_rows) + "\n", encoding="utf-8")
    config = tmp_path / "config.yaml"
    out = tmp_path / "out"
    _write_yaml(
        config,
        {
            "source_rows": str(rows_path),
            "behavior_arm": "arm",
            "target_group": "refusal_openers",
            "runs": [{"label": "run", "diagnostics": str(diagnostics)}],
            "behavior_cells": {
                "fallback_cell": "other",
                "cells": [
                    {"label": "known_refused", "filter": {"label": "known", "refused": True}},
                    {
                        "label": "unknown_answered_wrong",
                        "filter": {"label": "unknown", "refused": False, "correct": False},
                    },
                ],
            },
            "output": {"root": str(out)},
        },
    )

    result = analysis.run_config(config)

    summary_rows = _read_csv(out / "cell_logit_summary.csv")
    by_cell = {row["behavior_cell"]: row for row in summary_rows}
    assert result["ok"] is True
    assert result["summary_row_count"] == 2
    assert float(by_cell["known_refused"]["probability_sum_delta_mean"]) == pytest.approx(0.2)
    assert float(by_cell["known_refused"]["top1_changed_rate"]) == pytest.approx(100.0)
    assert float(by_cell["unknown_answered_wrong"]["probability_sum_delta_mean"]) == pytest.approx(-0.1)


def test_run_config_fails_on_unknown_row_key(tmp_path):
    rows_path = tmp_path / "rows.jsonl"
    rows_path.write_text(
        json.dumps({"probe_pool_row_key": "known", "label": "known", "source_arms": {"arm": {}}}) + "\n",
        encoding="utf-8",
    )
    diagnostics = tmp_path / "diag.jsonl"
    diagnostics.write_text(
        json.dumps(
            {
                "probe_pool_row_key": "missing",
                "candidate_label": "cand",
                "grid_coefficient": 1.0,
                "control": "activation_addition",
                "logit_target_metrics": {
                    "refusal_openers": {"probability_sum_delta": 0.0, "logit_sum_delta": 0.0}
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    config = tmp_path / "config.yaml"
    _write_yaml(
        config,
        {
            "source_rows": str(rows_path),
            "behavior_arm": "arm",
            "runs": [{"label": "run", "diagnostics": str(diagnostics)}],
            "behavior_cells": {
                "cells": [{"label": "known", "filter": {"label": "known"}}],
            },
            "output": {"root": str(tmp_path / "out")},
        },
    )

    with pytest.raises(analysis.LogitCellAnalysisError, match="unknown row key"):
        analysis.run_config(config)
