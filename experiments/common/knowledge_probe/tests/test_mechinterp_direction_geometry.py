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

import direction_geometry as geometry  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_direction(
    root: Path,
    *,
    direction_id: str,
    vector: list[float],
    layer: int,
    role: str = "delta",
    feature: int | None = None,
) -> dict:
    vector_path = root / f"{direction_id}.safetensors"
    safetensors_numpy.save_file(
        {geometry_row_tensor_key(): np.asarray(vector, dtype=np.float32)},
        str(vector_path),
    )
    row = {
        "direction_id": direction_id,
        "role": role,
        "layer": layer,
        "hidden_dim": len(vector),
        "status": "ok",
        "tensor_key": geometry_row_tensor_key(),
        "vector_file": str(vector_path),
        "method": "fixture",
        "contrast": "unknown_minus_known",
    }
    if feature is not None:
        row["feature"] = feature
        row["candidate_label"] = "feature_fixture"
        row["feature_skew_label"] = "unknown"
    return row


def geometry_row_tensor_key() -> str:
    return "direction"


def _write_manifest(path: Path, rows: list[dict]) -> None:
    path.write_text(
        json.dumps({"analysis_type": "fixture", "directions": rows}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_run_config_writes_pairwise_and_nearest_neighbors(tmp_path):
    root = tmp_path / "vectors"
    root.mkdir()
    rows = [
        _write_direction(root, direction_id="a", vector=[1.0, 0.0], layer=3),
        _write_direction(root, direction_id="b", vector=[0.0, 1.0], layer=3, feature=7),
        _write_direction(root, direction_id="c", vector=[1.0, 1.0], layer=4, feature=8),
    ]
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, rows)
    config = tmp_path / "geometry.yaml"
    out = tmp_path / "out"
    _write_yaml(
        config,
        {
            "direction_sets": [
                {
                    "label": "broad_l3",
                    "manifest": str(manifest),
                    "filters": {"layers": [3], "roles": ["delta"]},
                },
                {
                    "label": "feature_selected",
                    "manifest": str(manifest),
                    "include_direction_ids": ["c"],
                },
            ],
            "nearest_neighbors_per_direction": 2,
            "output": {"root": str(out)},
        },
    )

    result = geometry.run_config(config)

    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    pairwise = (out / "pairwise_cosine.csv").read_text(encoding="utf-8")
    nearest = (out / "nearest_neighbors.csv").read_text(encoding="utf-8")
    inventory = (out / "direction_inventory.csv").read_text(encoding="utf-8")

    assert result["ok"] is True
    assert result["notice"] == geometry.NOTICE
    assert summary["direction_count"] == 3
    assert summary["pair_count"] == 3
    assert "0.707106" in pairwise
    assert "feature_selected" in nearest
    assert "broad_l3" in inventory


def test_run_config_rejects_empty_selection(tmp_path):
    root = tmp_path / "vectors"
    root.mkdir()
    manifest = tmp_path / "manifest.json"
    _write_manifest(
        manifest,
        [_write_direction(root, direction_id="a", vector=[1.0, 0.0], layer=3)],
    )
    config = tmp_path / "geometry.yaml"
    _write_yaml(
        config,
        {
            "direction_sets": [
                {
                    "label": "missing",
                    "manifest": str(manifest),
                    "include_direction_ids": ["not-present"],
                }
            ],
            "output": {"root": str(tmp_path / "out")},
        },
    )

    with pytest.raises(geometry.DirectionGeometryError, match="selected no non-zero vectors"):
        geometry.run_config(config)
