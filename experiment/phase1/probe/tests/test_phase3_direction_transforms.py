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

import phase3_direction_transforms as transforms  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_source_direction(
    root: Path,
    *,
    direction_id: str,
    vector: list[float],
    layer: int = 7,
    role: str = "delta",
) -> dict:
    vector_path = root / f"{direction_id}.safetensors"
    safetensors_numpy.save_file(
        {transforms.TENSOR_KEY: np.asarray(vector, dtype=np.float32)},
        str(vector_path),
    )
    return {
        "direction_id": direction_id,
        "status": "ok",
        "role": role,
        "layer": layer,
        "hidden_dim": len(vector),
        "norm": float(np.linalg.norm(np.asarray(vector, dtype=np.float32))),
        "vector_sha256": "unused",
        "tensor_key": transforms.TENSOR_KEY,
        "vector_file": str(vector_path),
        "method": "known_unknown_diff",
        "contrast": "unknown_minus_known",
        "positive_label": "unknown",
        "negative_label": "known",
    }


def _fixture_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(
        json.dumps({"analysis_type": "unit", "directions": rows}, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def test_run_config_exports_unit_rescaled_direction(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    row = _write_source_direction(source_root, direction_id="a", vector=[3.0, 4.0])
    source_manifest = _fixture_manifest(tmp_path, [row])
    output_root = tmp_path / "out"
    config_path = tmp_path / "transforms.yaml"
    _write_yaml(
        config_path,
        {
            "source_manifest": str(source_manifest),
            "transforms": [
                {
                    "label": "a_norm2",
                    "source_direction_id": "a",
                    "method": "unit_rescale_to_norm",
                    "target_norm": 2.0,
                    "metadata": {"arm": "fixture"},
                }
            ],
            "output": {"root": str(output_root)},
        },
    )

    result = transforms.run_config(config_path)

    manifest = json.loads((output_root / "direction_transforms.manifest.json").read_text(encoding="utf-8"))
    record = manifest["directions"][0]
    tensor = safetensors_numpy.load_file(str(Path(record["vector_file"])))[transforms.TENSOR_KEY]

    assert result["ok"] is True
    assert result["notice"] == transforms.NOTICE
    assert record["source_direction_id"] == "a"
    assert record["transform_method"] == "unit_rescale_to_norm"
    assert record["arm"] == "fixture"
    assert float(np.linalg.norm(tensor)) == pytest.approx(2.0)


def test_run_config_rejects_missing_source_direction(tmp_path):
    source_root = tmp_path / "source"
    source_root.mkdir()
    source_manifest = _fixture_manifest(
        tmp_path,
        [_write_source_direction(source_root, direction_id="a", vector=[1.0, 0.0])],
    )
    config_path = tmp_path / "transforms.yaml"
    _write_yaml(
        config_path,
        {
            "source_manifest": str(source_manifest),
            "transforms": [{"label": "missing", "source_direction_id": "b"}],
            "output": {"root": str(tmp_path / "out")},
        },
    )

    with pytest.raises(transforms.DirectionTransformError, match="not found"):
        transforms.run_config(config_path)
