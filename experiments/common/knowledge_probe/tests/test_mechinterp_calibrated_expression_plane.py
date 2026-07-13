from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

safetensors_numpy = pytest.importorskip("safetensors.numpy")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import calibrated_expression_plane as plane  # noqa: E402


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _row(row_key: str, *, label: str, refused: bool, correct: bool, confidence: float) -> dict:
    return {
        "row_key": row_key,
        "label": label,
        "source_arms": {
            "fixture_arm": {
                "refused": refused,
                "correct": correct,
                "truthful": correct,
                "stated_confidence": confidence,
            }
        },
    }


def _write_extraction(tmp_path: Path) -> Path:
    extraction = tmp_path / "extraction"
    extraction.mkdir()
    (extraction / "manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "verified": True,
                "persistence_format": "safetensors",
                "tensor_shapes": {"h_lora": [2, 2]},
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _row("unknown::wrong", label="unknown", refused=False, correct=False, confidence=0.8),
        _row("unknown::refused", label="unknown", refused=True, correct=False, confidence=0.1),
        _row("known::correct", label="known", refused=False, correct=True, confidence=0.9),
    ]
    with (extraction / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    tensors = {
        "unknown__wrong": {"L0": [0.0, 0.0], "L1": [2.0, 1.0]},
        "unknown__refused": {"L0": [0.0, 0.0], "L1": [-1.0, 3.0]},
        "known__correct": {"L0": [0.0, 0.0], "L1": [4.0, -2.0]},
    }
    for safe_key, payload in tensors.items():
        safetensors_numpy.save_file(
            {key: np.asarray(value, dtype=np.float32) for key, value in payload.items()},
            str(extraction / f"{safe_key}__h_lora.safetensors"),
        )
    return extraction


def _write_direction(
    root: Path,
    *,
    direction_id: str,
    vector: list[float],
    layer: int = 1,
    role: str = "h_lora",
) -> dict:
    path = root / f"{direction_id}.safetensors"
    safetensors_numpy.save_file({"direction": np.asarray(vector, dtype=np.float32)}, str(path))
    return {
        "direction_id": direction_id,
        "role": role,
        "layer": layer,
        "hidden_dim": len(vector),
        "tensor_key": "direction",
        "vector_file": str(path),
        "method": "fixture",
    }


def _write_direction_manifest(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "directions.manifest.json"
    path.write_text(json.dumps({"analysis_type": "fixture", "directions": rows}, indent=2) + "\n", encoding="utf-8")
    return path


def _base_config(extraction: Path, direction_manifest: Path, output_root: Path) -> dict:
    return {
        "extraction": {
            "label": "fixture",
            "extraction_dir": str(extraction),
            "extraction_manifest": str(extraction / "manifest.json"),
            "role": "h_lora",
            "behavior_arm": "fixture_arm",
        },
        "direction_manifest": str(direction_manifest),
        "planes": [
            {
                "layer": 1,
                "x_direction_id": "x_axis",
                "y_direction_id": "y_axis",
            }
        ],
        "behavior_cells": {
            "fallback_cell": "other",
            "cells": [
                {
                    "label": "unknown_answered_wrong",
                    "filter": {"label": "unknown", "refused": False, "correct": False},
                },
                {
                    "label": "unknown_refused",
                    "filter": {"label": "unknown", "refused": True},
                },
                {
                    "label": "known_correct_answered",
                    "filter": {"label": "known", "refused": False, "correct": True},
                },
            ],
        },
        "output": {"root": str(output_root)},
    }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_run_config_writes_plane_rows_summary_and_json(tmp_path):
    extraction = _write_extraction(tmp_path)
    vector_root = tmp_path / "vectors"
    vector_root.mkdir()
    direction_manifest = _write_direction_manifest(
        tmp_path,
        [
            _write_direction(vector_root, direction_id="x_axis", vector=[2.0, 0.0]),
            _write_direction(vector_root, direction_id="y_axis", vector=[0.0, 5.0]),
        ],
    )
    config = tmp_path / "plane.yaml"
    output_root = tmp_path / "out"
    _write_yaml(config, _base_config(extraction, direction_manifest, output_root))

    result = plane.run_config(config)

    plane_rows = _read_csv(output_root / "plane_rows.csv")
    summary_rows = _read_csv(output_root / "plane_summary.csv")
    summary = json.loads((output_root / "summary.json").read_text(encoding="utf-8"))

    assert result["ok"] is True
    assert result["notice"] == plane.NOTICE
    assert len(plane_rows) == 3
    assert len(summary_rows) == 3
    assert summary["analysis_type"] == plane.ANALYSIS_TYPE
    assert summary["projection_row_count"] == 3
    assert summary["counts_by_layer"] == {"1": 3}
    assert summary["counts_by_behavior_cell"] == {
        "known_correct_answered": 1,
        "unknown_answered_wrong": 1,
        "unknown_refused": 1,
    }
    by_cell = {row["behavior_cell"]: row for row in plane_rows}
    assert float(by_cell["unknown_answered_wrong"]["x_projection"]) == pytest.approx(2.0)
    assert float(by_cell["unknown_answered_wrong"]["y_projection"]) == pytest.approx(1.0)
    assert float(by_cell["unknown_refused"]["x_projection"]) == pytest.approx(-1.0)
    assert float(by_cell["unknown_refused"]["y_projection"]) == pytest.approx(3.0)
    assert float(by_cell["known_correct_answered"]["x_projection"]) == pytest.approx(4.0)
    assert float(by_cell["known_correct_answered"]["y_projection"]) == pytest.approx(-2.0)
    assert summary["outputs"]["plane_rows"].endswith("plane_rows.csv")
    assert "unknown_answered_wrong" in (output_root / "plane_summary.csv").read_text(encoding="utf-8")


def test_run_config_fails_on_axis_hidden_dim_mismatch(tmp_path):
    extraction = _write_extraction(tmp_path)
    vector_root = tmp_path / "vectors"
    vector_root.mkdir()
    direction_manifest = _write_direction_manifest(
        tmp_path,
        [
            _write_direction(vector_root, direction_id="x_axis", vector=[1.0, 0.0, 0.0]),
            _write_direction(vector_root, direction_id="y_axis", vector=[0.0, 1.0]),
        ],
    )
    config = tmp_path / "plane.yaml"
    _write_yaml(config, _base_config(extraction, direction_manifest, tmp_path / "out"))

    with pytest.raises(plane.CalibratedExpressionPlaneError, match="hidden dim mismatch"):
        plane.run_config(config)
