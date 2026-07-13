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

import head_localization_scan as head_scan  # noqa: E402


# Fixture layout: 2 heads x head_dim 3 = width 6 per block, 2 blocks (L0, L1).
# Head 0 (cols 0:3) is constant noise; head 1 (cols 3:6) carries the
# refused-vs-answered separation, and L1 separates more strongly than L0. So the
# top-ranked (layer, head) MUST be (L1, H1) — the scan has to slice the right
# columns to find it.
NUM_HEADS = 2
HEAD_DIM = 3
WIDTH = NUM_HEADS * HEAD_DIM


def _row(row_key: str, *, refused: bool) -> dict:
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
                "stated_confidence": 0.0 if refused else 1.0,
            }
        },
    }


def _vec(head1_l0: float, head1_l1: float) -> dict:
    # head 0 slots (0:3) constant zero; head 1 slots (3:6) carry the signal.
    return {
        "L0": np.asarray([0.0, 0.0, 0.0, head1_l0, 0.0, 0.0], dtype=np.float32),
        "L1": np.asarray([0.0, 0.0, 0.0, head1_l1, 0.0, 0.0], dtype=np.float32),
    }


def _write_fixture_extraction(root: Path, *, manifest_overrides: dict | None = None) -> Path:
    extraction_dir = root / "extraction"
    extraction_dir.mkdir()
    manifest = {
        "status": "ok",
        "verified": True,
        "persistence_format": "safetensors",
        "granularity": "attention_head",
        "num_attention_heads": NUM_HEADS,
        "head_dim": HEAD_DIM,
        "tensor_shapes": {"h_base": [2, WIDTH]},
    }
    if manifest_overrides:
        manifest.update(manifest_overrides)
    (extraction_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    rows = [
        _row("u|refused|1", refused=True),
        _row("u|refused|2", refused=True),
        _row("u|answered|1", refused=False),
        _row("u|answered|2", refused=False),
    ]
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")

    tensors_by_row = {
        "u|refused|1": _vec(1.0, 6.0),
        "u|refused|2": _vec(0.9, 5.5),
        "u|answered|1": _vec(0.3, 0.2),
        "u|answered|2": _vec(0.2, 0.0),
    }
    for row_key, tensors in tensors_by_row.items():
        safe_key = row_key.replace("|", "_")
        save_file(tensors, str(extraction_dir / f"{safe_key}__h_base.safetensors"))
    return extraction_dir


def _config(extraction_dir: Path, output_root: Path) -> dict:
    return {
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


def test_head_scan_ranks_the_separating_head(tmp_path):
    extraction_dir = _write_fixture_extraction(tmp_path)
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, output_root)), encoding="utf-8")

    summary = head_scan.run_config(config_path)

    assert summary["ok"] is True
    # 1 role x 2 layers x 2 heads x 1 contrast = 4 axes.
    assert summary["row_count"] == 4
    with (output_root / "top_heads_all.csv").open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    # The strongest axis must be the head that carries the signal: L1 H1.
    assert rows[0]["layer"] == "1"
    assert rows[0]["head"] == "1"
    # Head 0 (constant noise) must separate strictly less than head 1.
    head0_d = max(
        abs(float(r["projection_cohen_d"])) for r in rows if r["head"] == "0"
    )
    assert abs(float(rows[0]["projection_cohen_d"])) > head0_d


def test_head_scan_rejects_non_head_granularity(tmp_path):
    extraction_dir = _write_fixture_extraction(
        tmp_path, manifest_overrides={"granularity": "residual_stream"}
    )
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, output_root)), encoding="utf-8")

    with pytest.raises(head_scan.HeadLocalizationScanError, match="granularity"):
        head_scan.run_config(config_path)


def test_head_scan_rejects_width_not_heads_times_head_dim(tmp_path):
    # tensor_shapes width 5 != num_attention_heads(2) * head_dim(3) = 6.
    extraction_dir = _write_fixture_extraction(
        tmp_path, manifest_overrides={"tensor_shapes": {"h_base": [2, 5]}}
    )
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, output_root)), encoding="utf-8")

    with pytest.raises(head_scan.HeadLocalizationScanError, match="not per-head"):
        head_scan.run_config(config_path)
