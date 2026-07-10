from __future__ import annotations

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

import phase3_head_steering_directions as steering  # noqa: E402

# 2 heads x head_dim 3 = width 6. Head 1 (cols 3:6) carries the refused/answered
# separation along its first slot; head 0 is constant noise. So head 1's theta
# must be ~[1,0,0] and its sigma > 0; head 0's mass-mean direction is zero.
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


def _vec(head1_l1: float) -> dict:
    return {
        "L0": np.asarray([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32),
        "L1": np.asarray([0.0, 0.0, 0.0, head1_l1, 0.0, 0.0], dtype=np.float32),
    }


def _write_fixture(root: Path, *, manifest_overrides: dict | None = None) -> Path:
    extraction_dir = root / "extraction"
    extraction_dir.mkdir()
    manifest = {
        "status": "ok",
        "verified": True,
        "persistence_format": "safetensors",
        "granularity": "attention_head",
        "num_attention_heads": NUM_HEADS,
        "head_dim": HEAD_DIM,
        "tensor_shapes": {"h_lora": [2, WIDTH]},
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
    tensors = {
        "u|refused|1": _vec(6.0),
        "u|refused|2": _vec(5.5),
        "u|answered|1": _vec(0.2),
        "u|answered|2": _vec(0.0),
    }
    for row_key, t in tensors.items():
        save_file(t, str(extraction_dir / f"{row_key.replace('|', '_')}__h_lora.safetensors"))
    return extraction_dir


def _config(extraction_dir: Path, output_root: Path, *, targets=None) -> dict:
    if targets is None:
        targets = [{"layer": 1, "head": 1}, {"layer": 1, "head": 0}]
    return {
        "output": {"root": str(output_root)},
        "steering_specs": [
            {
                "label": "fixture",
                "behavior_arm": "fixture_arm",
                "arm_role": "h_lora",
                "extraction_dir": str(extraction_dir),
                "extraction_manifest": str(extraction_dir / "manifest.json"),
                "contrast": {
                    "name": "answered_vs_refused",
                    "positive_label": "answered",
                    "negative_label": "refused",
                    "min_rows_per_group": 2,
                    "positive": {"label": "unknown", "refused": False},
                    "negative": {"label": "unknown", "refused": True},
                },
                "targets": targets,
            }
        ],
    }


def test_steering_directions_recover_planted_head_axis(tmp_path):
    extraction_dir = _write_fixture(tmp_path)
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, output_root)), encoding="utf-8")

    summary = steering.run_config(config_path)
    assert summary["ok"] is True

    artifact = json.loads((output_root / "fixture" / "steering_directions.json").read_text(encoding="utf-8"))
    by_head = {(d["layer"], d["head"]): d for d in artifact["directions"]}

    # Head 1 carries the signal along its first slot: theta ~= [-1, 0, 0]
    # (positive=answered has LOWER values than negative=refused, so
    # mean(answered) - mean(refused) is negative on slot 0), sigma > 0.
    h1 = by_head[(1, 1)]
    assert h1["theta"][0] == pytest.approx(-1.0, abs=1e-5)
    assert abs(h1["theta"][1]) < 1e-6 and abs(h1["theta"][2]) < 1e-6
    assert h1["sigma"] > 1.0

    # Head 0 is constant noise: zero mass-mean direction, zero sigma.
    h0 = by_head[(1, 0)]
    assert h0["mean_diff_norm"] == pytest.approx(0.0)
    assert h0["sigma"] == pytest.approx(0.0)

    assert artifact["contrast"]["positive_label"] == "answered"
    assert artifact["arm_role"] == "h_lora"


def test_steering_rejects_out_of_range_target(tmp_path):
    extraction_dir = _write_fixture(tmp_path)
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(_config(extraction_dir, output_root, targets=[{"layer": 1, "head": 9}])),
        encoding="utf-8",
    )
    with pytest.raises(steering.HeadSteeringError, match="head 9 out of range"):
        steering.run_config(config_path)


def test_steering_rejects_non_head_extraction(tmp_path):
    extraction_dir = _write_fixture(tmp_path, manifest_overrides={"granularity": "residual_stream"})
    output_root = tmp_path / "outputs"
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(_config(extraction_dir, output_root)), encoding="utf-8")
    with pytest.raises(steering.HeadLocalizationScanError, match="granularity"):
        steering.run_config(config_path)
