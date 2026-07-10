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

import behavior_axis_directions as directions  # noqa: E402


def _row(row_key: str, *, refused: bool) -> dict:
    return {
        "row_key": row_key,
        "label": "unknown",
        "source_arms": {
            "fixture_arm": {
                "refused": refused,
                "correct": False,
                "truthful": False,
                "stated_confidence": 0.0 if refused else 1.0,
            }
        },
    }


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    extraction = tmp_path / "extraction"
    extraction.mkdir()
    (extraction / "manifest.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "verified": True,
                "persistence_format": "safetensors",
                "tensor_shapes": {"delta": [2, 2]},
            }
        ),
        encoding="utf-8",
    )
    rows = [
        _row("u::refused::1", refused=True),
        _row("u::refused::2", refused=True),
        _row("u::answered::1", refused=False),
        _row("u::answered::2", refused=False),
    ]
    with (extraction / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    tensors = {
        "u__refused__1": {"L0": np.asarray([1.0, 0.0], dtype=np.float32), "L1": np.asarray([3.0, 0.0], dtype=np.float32)},
        "u__refused__2": {"L0": np.asarray([1.0, 0.0], dtype=np.float32), "L1": np.asarray([3.0, 0.0], dtype=np.float32)},
        "u__answered__1": {"L0": np.asarray([0.0, 0.0], dtype=np.float32), "L1": np.asarray([0.0, 0.0], dtype=np.float32)},
        "u__answered__2": {"L0": np.asarray([0.0, 0.0], dtype=np.float32), "L1": np.asarray([0.0, 0.0], dtype=np.float32)},
    }
    for safe_key, payload in tensors.items():
        safetensors_numpy.save_file(payload, str(extraction / f"{safe_key}__delta.safetensors"))

    scan_config = tmp_path / "scan.yaml"
    _write_yaml(
        scan_config,
        {
            "analysis": {
                "contrasts": [
                    {
                        "name": "unknown_refused_vs_unknown_answered",
                        "positive_label": "unknown_refused",
                        "negative_label": "unknown_answered",
                        "min_rows_per_group": 2,
                        "positive": {"label": "unknown", "refused": True},
                        "negative": {"label": "unknown", "refused": False},
                    }
                ]
            },
            "extractions": [
                {
                    "label": "fixture",
                    "behavior_arm": "fixture_arm",
                    "extraction_dir": str(extraction),
                    "extraction_manifest": str(extraction / "manifest.json"),
                }
            ],
        },
    )
    return extraction, scan_config


def test_behavior_axis_direction_export_writes_normed_vector(tmp_path):
    _extraction, scan_config = _write_fixture(tmp_path)
    output_root = tmp_path / "out"
    config_path = tmp_path / "directions.yaml"
    _write_yaml(
        config_path,
        {
            "source_scan_config": str(scan_config),
            "axes": [
                {
                    "label": "fixture_axis",
                    "extraction_label": "fixture",
                    "behavior_arm": "fixture_arm",
                    "arm": "fixture",
                    "role": "delta",
                    "layer": 1,
                    "contrast": "unknown_refused_vs_unknown_answered",
                    "transform_method": "unit_rescale_to_norm",
                    "target_norm": 2.0,
                }
            ],
            "output": {"root": str(output_root)},
        },
    )

    result = directions.run_config(config_path)

    manifest = json.loads((output_root / "behavior_axis_directions.manifest.json").read_text(encoding="utf-8"))
    record = manifest["directions"][0]
    tensor = safetensors_numpy.load_file(str(Path(record["vector_file"])))[directions.TENSOR_KEY]

    assert result["ok"] is True
    assert record["method"] == "behavior_axis_mean_difference"
    assert record["contrast"] == "unknown_refused_vs_unknown_answered"
    assert record["positive_count"] == 2
    assert record["negative_count"] == 2
    assert record["source_norm"] == pytest.approx(3.0)
    assert float(np.linalg.norm(tensor)) == pytest.approx(2.0)
    assert tensor.tolist() == pytest.approx([2.0, 0.0])


def test_behavior_axis_direction_export_fails_on_insufficient_rows(tmp_path):
    _extraction, scan_config = _write_fixture(tmp_path)
    config_path = tmp_path / "directions.yaml"
    _write_yaml(
        config_path,
        {
            "source_scan_config": str(scan_config),
            "axes": [
                {
                    "label": "fixture_axis",
                    "extraction_label": "fixture",
                    "behavior_arm": "fixture_arm",
                    "role": "delta",
                    "layer": 1,
                    "contrast": "unknown_refused_vs_unknown_answered",
                    "min_rows_per_group": 3,
                    "transform_method": "identity",
                }
            ],
            "output": {"root": str(tmp_path / "out")},
        },
    )

    with pytest.raises(directions.BehaviorAxisDirectionError, match="insufficient rows"):
        directions.run_config(config_path)


def test_behavior_axis_direction_export_uses_scan_rows_path_override(tmp_path):
    extraction, scan_config = _write_fixture(tmp_path)
    derived_rows = tmp_path / "derived_rows.jsonl"
    rows = [
        _row("u::refused::1", refused=False),
        _row("u::refused::2", refused=False),
        _row("u::answered::1", refused=True),
        _row("u::answered::2", refused=True),
    ]
    with derived_rows.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    scan_payload = yaml.safe_load(scan_config.read_text(encoding="utf-8"))
    scan_payload["extractions"][0]["rows_path"] = str(derived_rows)
    _write_yaml(scan_config, scan_payload)

    output_root = tmp_path / "out"
    config_path = tmp_path / "directions.yaml"
    _write_yaml(
        config_path,
        {
            "source_scan_config": str(scan_config),
            "axes": [
                {
                    "label": "fixture_axis",
                    "extraction_label": "fixture",
                    "behavior_arm": "fixture_arm",
                    "role": "delta",
                    "layer": 1,
                    "contrast": "unknown_refused_vs_unknown_answered",
                    "transform_method": "unit_rescale_to_norm",
                    "target_norm": 2.0,
                }
            ],
            "output": {"root": str(output_root)},
        },
    )

    result = directions.run_config(config_path)

    manifest = json.loads((output_root / "behavior_axis_directions.manifest.json").read_text(encoding="utf-8"))
    record = manifest["directions"][0]
    tensor = safetensors_numpy.load_file(str(Path(record["vector_file"])))[directions.TENSOR_KEY]

    assert result["ok"] is True
    assert record["source_rows_path"] == str(derived_rows.resolve()).replace("\\", "/")
    assert tensor.tolist() == pytest.approx([-2.0, 0.0])
