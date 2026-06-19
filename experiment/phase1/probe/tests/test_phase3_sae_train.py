from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

pytest.importorskip("torch")
safetensors_numpy = pytest.importorskip("safetensors.numpy")
safetensors_torch = pytest.importorskip("safetensors.torch")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_sae_smoke as smoke  # noqa: E402
import phase3_sae_train as train  # noqa: E402
from test_phase3_sae_smoke import _write_extraction  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _config(config_path: Path, extraction_dir: Path, output_root: Path, **training_overrides: object) -> Path:
    payload = {
        "spec": {
            "name": "unit",
            "analysis_type": train.ANALYSIS_TYPE,
            "notice": train.NOTICE,
        },
        "training": {
            "seed": 20260619,
            "max_rows_per_label": 4,
            "dictionary_size": 3,
            "epochs": 3,
            "batch_size": 4,
            "learning_rate": 0.01,
            "l1_coefficient": 0.001,
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
        "output": {"root": str(output_root)},
    }
    payload["training"].update(training_overrides)
    _write_yaml(config_path, payload)
    return config_path


def test_run_config_trains_sae_pilot_and_writes_claim_safe_outputs(tmp_path):
    extraction_dir = tmp_path / "extract"
    output_root = tmp_path / "sae_runs" / "unit"
    _write_extraction(extraction_dir, row_count_per_label=5, layer_count=3, hidden_dim=6)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, output_root)

    summary = train.run_config(config_path)

    candidate_root = output_root / "fixture_delta_l1"
    manifest = json.loads((candidate_root / "run_manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((candidate_root / "metrics.json").read_text(encoding="utf-8"))
    history = json.loads((candidate_root / "training_history.json").read_text(encoding="utf-8"))
    weights = safetensors_torch.load_file(str(candidate_root / "sae_weights.safetensors"))

    assert summary["ok"] is True
    assert manifest["notice"] == train.NOTICE
    assert manifest["analysis_type"] == train.ANALYSIS_TYPE
    assert manifest["training"]["trained_sae"] is True
    assert manifest["training"]["causal_evidence"] is False
    assert manifest["selection"]["row_count"] == 8
    assert manifest["selection"]["label_counts"] == {"known": 4, "unknown": 4}
    assert metrics["notice"] == train.NOTICE
    assert metrics["dictionary_size"] == 3
    assert metrics["hidden_dim"] == 6
    assert metrics["validation"]["mse"] >= 0.0
    assert len(history["history"]) >= 2
    assert weights["encoder.weight"].shape == (3, 6)
    assert weights["decoder.weight"].shape == (6, 3)
    assert weights["normalization.mean"].shape == (6,)


def test_run_config_rejects_cuda_when_unavailable(tmp_path):
    if train.torch.cuda.is_available():
        pytest.skip("cuda is available in this environment")
    extraction_dir = tmp_path / "extract"
    _write_extraction(extraction_dir, row_count_per_label=5, layer_count=3, hidden_dim=6)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, tmp_path / "out", device="cuda")

    with pytest.raises(train.SaeTrainError, match="requested cuda"):
        train.run_config(config_path)


def test_run_config_reuses_smoke_fail_closed_output_root_guard(tmp_path):
    extraction_dir = tmp_path / "extract"
    _write_extraction(extraction_dir, row_count_per_label=5, layer_count=3, hidden_dim=6)
    config_path = _config(tmp_path / "config.yaml", extraction_dir, extraction_dir / "sae_runs")

    with pytest.raises(smoke.SaeSmokeError, match="output root must not be inside extraction dir"):
        train.run_config(config_path)
