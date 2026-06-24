from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

safetensors_numpy = pytest.importorskip("safetensors.numpy")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_sae_feature_composites as composites  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_source_direction(
    root: Path,
    *,
    direction_id: str,
    vector: list[float],
    feature: int,
    layer: int = 7,
    role: str = "delta",
) -> dict:
    vector_path = root / f"{direction_id}.safetensors"
    safetensors_numpy.save_file(
        {composites.TENSOR_KEY: np.asarray(vector, dtype=np.float32)},
        str(vector_path),
    )
    return {
        "direction_id": direction_id,
        "candidate_label": "fixture",
        "feature": feature,
        "status": "ok",
        "role": role,
        "layer": layer,
        "hidden_dim": len(vector),
        "norm": float(np.linalg.norm(np.asarray(vector, dtype=np.float32))),
        "vector_sha256": "unused",
        "tensor_key": composites.TENSOR_KEY,
        "vector_file": str(vector_path),
        "feature_skew_label": "unknown",
    }


def _fixture_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(
        json.dumps({"analysis_type": "unit", "directions": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def _fixture_config(tmp_path: Path, source_manifest: Path, output_root: Path, composite: dict) -> Path:
    config_path = tmp_path / "composites.yaml"
    _write_yaml(
        config_path,
        {
            "source_manifest": str(source_manifest),
            "composites": [composite],
            "output": {"root": str(output_root)},
        },
    )
    return config_path


def test_run_config_exports_unit_mean_rescaled_composite(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    rows = [
        _write_source_direction(source_root, direction_id="a", vector=[3.0, 0.0], feature=1),
        _write_source_direction(source_root, direction_id="b", vector=[0.0, 4.0], feature=2),
    ]
    source_manifest = _fixture_manifest(tmp_path, rows)
    output_root = tmp_path / "out"
    config_path = _fixture_config(
        tmp_path,
        source_manifest,
        output_root,
        {
            "label": "unknown_pair",
            "source_direction_ids": ["a", "b"],
            "weights": [1.0, 1.0],
            "combine": "unit_weighted_mean",
            "rescale": "mean_source_norm",
            "feature_skew_label": "unknown",
            "contrast": "unknown_minus_known",
        },
    )

    result = composites.run_config(config_path)

    manifest = json.loads(
        (output_root / "sae_feature_composite_directions.manifest.json").read_text(encoding="utf-8")
    )
    record = manifest["directions"][0]
    tensor = safetensors_numpy.load_file(str(Path(record["vector_file"])))["direction"]

    assert result["ok"] is True
    assert result["notice"] == composites.NOTICE
    assert manifest["direction_count"] == 1
    assert record["source_features"] == [1, 2]
    assert record["combine"] == "unit_weighted_mean"
    assert record["rescale"] == "mean_source_norm"
    assert record["contrast"] == "unknown_minus_known"
    assert float(np.linalg.norm(tensor)) == pytest.approx(3.5)


def test_run_config_rejects_mixed_layers(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    rows = [
        _write_source_direction(source_root, direction_id="a", vector=[1.0, 0.0], feature=1, layer=7),
        _write_source_direction(source_root, direction_id="b", vector=[0.0, 1.0], feature=2, layer=8),
    ]
    source_manifest = _fixture_manifest(tmp_path, rows)
    config_path = _fixture_config(
        tmp_path,
        source_manifest,
        tmp_path / "out",
        {"label": "bad", "source_direction_ids": ["a", "b"]},
    )

    with pytest.raises(composites.SaeFeatureCompositeError, match="share one layer"):
        composites.run_config(config_path)
