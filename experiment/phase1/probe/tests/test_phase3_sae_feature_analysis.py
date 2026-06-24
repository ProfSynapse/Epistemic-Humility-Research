from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("torch")
pytest.importorskip("safetensors.numpy")
pytest.importorskip("safetensors.torch")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_sae_feature_analysis as feature_analysis  # noqa: E402
import phase3_sae_train as train  # noqa: E402
from test_phase3_sae_smoke import _write_extraction  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _train_topk_run(tmp_path: Path) -> Path:
    extraction_dir = tmp_path / "extract"
    train_root = tmp_path / "sae_runs" / "unit_topk"
    _write_extraction(extraction_dir, row_count_per_label=5, layer_count=3, hidden_dim=6)
    train_config = {
        "spec": {
            "name": "unit",
            "analysis_type": train.ANALYSIS_TYPE,
            "notice": train.NOTICE,
        },
        "training": {
            "seed": 20260619,
            "max_rows_per_label": 4,
            "dictionary_size": 4,
            "activation": "topk_relu",
            "top_k": 2,
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 0.01,
            "l1_coefficient": 0.0,
            "validation_fraction": 0.25,
            "device": "cpu",
        },
        "candidate_extractions": [
            {
                "label": "fixture_delta_l1",
                "arm": "fixture",
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
                "role": "delta",
                "layer": 1,
                "required_status": "ok",
            }
        ],
        "output": {"root": str(train_root)},
    }
    train_config_path = tmp_path / "train.yaml"
    _write_yaml(train_config_path, train_config)
    train.run_config(train_config_path)
    return train_root / "fixture_delta_l1"


def _analysis_config(config_path: Path, run_dir: Path, output_root: Path) -> Path:
    payload = {
        "spec": {
            "name": "unit",
            "analysis_type": feature_analysis.ANALYSIS_TYPE,
            "notice": feature_analysis.NOTICE,
        },
        "analysis": {
            "top_features": 3,
            "top_rows_per_feature": 2,
        },
        "candidate_runs": [
            {
                "label": "fixture_topk_features",
                "run_dir": str(run_dir),
            }
        ],
        "output": {"root": str(output_root)},
    }
    _write_yaml(config_path, payload)
    return config_path


def test_run_config_ranks_trained_sae_features(tmp_path):
    run_dir = _train_topk_run(tmp_path)
    output_root = tmp_path / "sae_feature_analysis" / "unit"
    config_path = _analysis_config(tmp_path / "analysis.yaml", run_dir, output_root)

    summary = feature_analysis.run_config(config_path)

    candidate_root = output_root / "fixture_topk_features"
    candidate_summary = json.loads((candidate_root / "summary.json").read_text(encoding="utf-8"))
    examples = json.loads((candidate_root / "top_feature_examples.json").read_text(encoding="utf-8"))
    with (candidate_root / "feature_rankings.csv").open(encoding="utf-8", newline="") as fh:
        ranking_rows = list(csv.DictReader(fh))

    assert summary["ok"] is True
    assert candidate_summary["notice"] == feature_analysis.NOTICE
    assert candidate_summary["activation"] == "topk_relu"
    assert candidate_summary["top_k"] == 2
    assert candidate_summary["row_count"] == 8
    assert candidate_summary["dictionary_size"] == 4
    assert 0.0 <= candidate_summary["mean_active_features"] <= 2.0
    assert len(candidate_summary["top_features"]) == 3
    assert len(ranking_rows) == 4
    assert examples["notice"] == feature_analysis.NOTICE
    assert set(examples["top_feature_examples"]) == {
        str(item["feature"]) for item in candidate_summary["top_features"]
    }


def test_run_config_fails_closed_on_unknown_selected_row(tmp_path):
    run_dir = _train_topk_run(tmp_path)
    selected_rows = run_dir / "selected_rows.jsonl"
    selected_rows.write_text(
        json.dumps({"row_key": "missing-row-key", "label": "known"}) + "\n",
        encoding="utf-8",
    )
    config_path = _analysis_config(tmp_path / "analysis.yaml", run_dir, tmp_path / "out")

    with pytest.raises(feature_analysis.SaeFeatureAnalysisError, match="unknown row_key"):
        feature_analysis.run_config(config_path)
