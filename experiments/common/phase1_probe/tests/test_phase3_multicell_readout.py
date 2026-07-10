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

import phase3_multicell_readout as readout  # noqa: E402


def _row(row_key: str, *, label: str, refused: bool, correct: bool) -> dict:
    return {
        "row_key": row_key,
        "label": label,
        "source_arms": {
            "fixture_arm": {
                "refused": refused,
                "correct": correct,
                "truthful": correct or (label == "unknown" and refused),
            }
        },
    }


def _write_fixture(root: Path) -> tuple[Path, Path]:
    extraction_dir = root / "extraction"
    extraction_dir.mkdir()
    rows = [
        _row("known_refused|0", label="known", refused=True, correct=False),
        _row("known_refused|1", label="known", refused=True, correct=False),
        _row("known_correct|0", label="known", refused=False, correct=True),
        _row("known_correct|1", label="known", refused=False, correct=True),
        _row("unknown_refused|0", label="unknown", refused=True, correct=False),
        _row("unknown_refused|1", label="unknown", refused=True, correct=False),
        _row("unknown_wrong|0", label="unknown", refused=False, correct=False),
        _row("unknown_wrong|1", label="unknown", refused=False, correct=False),
    ]
    rows_path = extraction_dir / "rows.jsonl"
    with rows_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    manifest = {
        "status": "ok",
        "verified": True,
        "persistence_format": "safetensors",
        "tensor_shapes": {"h_lora": [2, 2]},
    }
    (extraction_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    vectors = {
        "known_refused": np.asarray([1.0, 1.0], dtype=np.float32),
        "known_correct": np.asarray([1.0, -1.0], dtype=np.float32),
        "unknown_refused": np.asarray([-1.0, 1.0], dtype=np.float32),
        "unknown_wrong": np.asarray([-1.0, -1.0], dtype=np.float32),
    }
    for row in rows:
        prefix = row["row_key"].split("|")[0]
        save_file(
            {
                "L0": np.asarray([vectors[prefix][0], 0.0], dtype=np.float32),
                "L1": vectors[prefix],
            },
            str(extraction_dir / f"{row['row_key'].replace('|', '_')}__h_lora.safetensors"),
        )
    return extraction_dir, rows_path


def _config(extraction_dir: Path, rows_path: Path, output_root: Path) -> dict:
    return {
        "analysis": {
            "ridge": 0.01,
            "cv_folds": 2,
            "min_rows_per_cell": 2,
            "ranks": [1, 2],
            "cells": [
                {"label": "known_refused", "filter": {"label": "known", "refused": True}},
                {
                    "label": "known_correct_answered",
                    "filter": {"label": "known", "refused": False, "correct": True},
                },
                {"label": "unknown_refused", "filter": {"label": "unknown", "refused": True}},
                {
                    "label": "unknown_answered_wrong",
                    "filter": {"label": "unknown", "refused": False, "correct": False},
                },
            ],
        },
        "extractions": [
            {
                "label": "fixture",
                "behavior_arm": "fixture_arm",
                "roles": ["h_lora"],
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
                "rows_path": str(rows_path),
            }
        ],
        "output": {"root": str(output_root)},
    }


def test_multicell_readout_shows_rank2_beats_rank1(tmp_path):
    extraction_dir, rows_path = _write_fixture(tmp_path)
    output_root = tmp_path / "readout"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, rows_path, output_root)), encoding="utf-8")

    summary = readout.run_config(config_path)

    assert summary["ok"] is True
    with (output_root / "readout_summary_all.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    by_layer_rank = {(int(row["layer"]), row["rank"]): row for row in rows}
    assert float(by_layer_rank[(1, "2")]["macro_recall"]) == pytest.approx(1.0)
    assert float(by_layer_rank[(1, "2")]["macro_recall"]) > float(by_layer_rank[(1, "1")]["macro_recall"])
    assert by_layer_rank[(1, "2")]["count_unknown_answered_wrong"] == "2"


def test_multicell_readout_rejects_low_cell_counts(tmp_path):
    extraction_dir, rows_path = _write_fixture(tmp_path)
    output_root = tmp_path / "readout"
    config = _config(extraction_dir, rows_path, output_root)
    config["analysis"]["min_rows_per_cell"] = 3
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")

    with pytest.raises(readout.MulticellReadoutError, match="insufficient cell counts"):
        readout.run_config(config_path)
