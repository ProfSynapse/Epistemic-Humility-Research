from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

pytest.importorskip("safetensors.numpy")
from safetensors.numpy import save_file  # noqa: E402

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import behavior_axis_scan as axis_scan  # noqa: E402


def _row(row_key: str, *, refused: bool, confidence: float) -> dict:
    return {
        "row_key": row_key,
        "label": "unknown",
        "question": f"Question {row_key}",
        "strata": [],
        "source_arms": {
            "fixture_arm": {
                "answer_text": "I don't know" if refused else "Answer",
                "refused": refused,
                "correct": False,
                "truthful": False,
                "stated_confidence": confidence,
            }
        },
    }


def _write_fixture_extraction(root: Path) -> Path:
    extraction_dir = root / "extraction"
    extraction_dir.mkdir()
    manifest = {
        "status": "ok",
        "verified": True,
        "persistence_format": "safetensors",
        "tensor_shapes": {"h_base": [2, 3]},
    }
    (extraction_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    rows = [
        _row("u|refused|1", refused=True, confidence=0.0),
        _row("u|refused|2", refused=True, confidence=0.1),
        _row("u|answered|1", refused=False, confidence=0.9),
        _row("u|answered|2", refused=False, confidence=1.0),
    ]
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    tensors_by_row = {
        "u|refused|1": {"L0": np.asarray([1.0, 0.0, 0.0], dtype=np.float32), "L1": np.asarray([6.0, 0.0, 0.0], dtype=np.float32)},
        "u|refused|2": {"L0": np.asarray([0.9, 0.0, 0.0], dtype=np.float32), "L1": np.asarray([5.5, 0.0, 0.0], dtype=np.float32)},
        "u|answered|1": {"L0": np.asarray([0.3, 0.0, 0.0], dtype=np.float32), "L1": np.asarray([0.2, 0.0, 0.0], dtype=np.float32)},
        "u|answered|2": {"L0": np.asarray([0.2, 0.0, 0.0], dtype=np.float32), "L1": np.asarray([0.0, 0.0, 0.0], dtype=np.float32)},
    }
    for row_key, tensors in tensors_by_row.items():
        safe_key = row_key.replace("|", "_")
        save_file(tensors, str(extraction_dir / f"{safe_key}__h_base.safetensors"))
    return extraction_dir


def test_rank_auc_handles_ties():
    scores = np.asarray([1.0, 1.0, 2.0, 3.0], dtype=np.float64)
    labels = np.asarray([False, True, True, False])

    assert axis_scan.rank_auc(scores, labels) == pytest.approx(0.375)


def test_behavior_axis_scan_ranks_expected_layer(tmp_path, monkeypatch):
    extraction_dir = _write_fixture_extraction(tmp_path)
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config = {
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
            ],
        },
        "extractions": [
            {
                "label": "fixture",
                "behavior_arm": "fixture_arm",
                "roles": ["h_base"],
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
            }
        ],
        "output": {"root": str(output_root)},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    summary = axis_scan.run_config(config_path)

    assert summary["ok"] is True
    with (output_root / "top_layers_all.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert rows[0]["layer"] == "1"
    assert float(rows[0]["projection_cohen_d"]) > float(rows[1]["projection_cohen_d"])
    assert rows[0]["contrast"] == "unknown_refused_vs_unknown_answered"


def test_behavior_axis_scan_can_use_rows_path_override(tmp_path):
    extraction_dir = _write_fixture_extraction(tmp_path)
    derived_rows = tmp_path / "derived_rows.jsonl"
    rows = [
        _row("u|refused|1", refused=False, confidence=0.0),
        _row("u|refused|2", refused=False, confidence=0.1),
        _row("u|answered|1", refused=True, confidence=0.9),
        _row("u|answered|2", refused=True, confidence=1.0),
    ]
    with derived_rows.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config = {
        "analysis": {
            "contrasts": [
                {
                    "name": "derived_refused_vs_derived_answered",
                    "positive_label": "derived_refused",
                    "negative_label": "derived_answered",
                    "min_rows_per_group": 2,
                    "positive": {"label": "unknown", "refused": True},
                    "negative": {"label": "unknown", "refused": False},
                }
            ],
        },
        "extractions": [
            {
                "label": "fixture",
                "behavior_arm": "fixture_arm",
                "roles": ["h_base"],
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
                "rows_path": str(derived_rows),
            }
        ],
        "output": {"root": str(output_root)},
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    summary = axis_scan.run_config(config_path)

    assert summary["ok"] is True
    extraction_summary = json.loads((output_root / "fixture" / "summary.json").read_text(encoding="utf-8"))
    assert extraction_summary["rows_path"] == str(derived_rows.resolve()).replace("\\", "/")
    with (output_root / "top_layers_all.csv").open(newline="", encoding="utf-8") as fh:
        top_rows = list(csv.DictReader(fh))
    assert top_rows[0]["positive_count"] == "2"
    assert top_rows[0]["negative_count"] == "2"
