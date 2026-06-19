from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("torch")
safetensors_numpy = pytest.importorskip("safetensors.numpy")
pytest.importorskip("safetensors.torch")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_sae_feature_analysis as feature_analysis  # noqa: E402
import phase3_sae_feature_directions as feature_directions  # noqa: E402
from test_phase3_sae_feature_analysis import _analysis_config, _train_topk_run  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _feature_analysis_summary(tmp_path: Path) -> Path:
    run_dir = _train_topk_run(tmp_path)
    output_root = tmp_path / "sae_feature_analysis" / "unit"
    config_path = _analysis_config(tmp_path / "analysis.yaml", run_dir, output_root)
    feature_analysis.run_config(config_path)
    return output_root / "fixture_topk_features" / "summary.json"


def _direction_config(config_path: Path, summary_path: Path, output_root: Path, **selection: object) -> Path:
    payload = {
        "spec": {
            "name": "unit",
            "analysis_type": feature_directions.ANALYSIS_TYPE,
            "notice": feature_directions.NOTICE,
        },
        "selection": selection or {"top_per_sign": 1},
        "candidate_analyses": [
            {
                "label": "fixture_topk_features",
                "summary": str(summary_path),
            }
        ],
        "output": {"root": str(output_root)},
    }
    _write_yaml(config_path, payload)
    return config_path


def test_run_config_exports_sae_feature_directions(tmp_path):
    summary_path = _feature_analysis_summary(tmp_path)
    output_root = tmp_path / "sae_feature_directions" / "unit"
    config_path = _direction_config(tmp_path / "directions.yaml", summary_path, output_root)

    summary = feature_directions.run_config(config_path)

    manifest = json.loads((output_root / "sae_feature_directions.manifest.json").read_text(encoding="utf-8"))
    with (output_root / "sae_feature_directions.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    vector_path = Path(rows[0]["vector_file"])
    tensors = safetensors_numpy.load_file(str(PROBE_DIR.parents[2] / vector_path))

    assert summary["ok"] is True
    assert summary["notice"] == feature_directions.NOTICE
    assert manifest["direction_count"] == 2
    assert len(rows) == 2
    assert {row["feature_skew_label"] for row in rows} == {"known", "unknown"}
    assert rows[0]["tensor_key"] == "direction"
    assert tensors["direction"].shape == (6,)
    assert float(rows[0]["norm"]) > 0.0


def test_run_config_rejects_missing_explicit_feature(tmp_path):
    summary_path = _feature_analysis_summary(tmp_path)
    config_path = _direction_config(
        tmp_path / "directions.yaml",
        summary_path,
        tmp_path / "out",
        features=[999],
    )

    with pytest.raises(feature_directions.SaeFeatureDirectionError, match="missing requested features"):
        feature_directions.run_config(config_path)
