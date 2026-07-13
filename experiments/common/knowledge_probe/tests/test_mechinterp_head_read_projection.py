from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("safetensors.numpy")
from safetensors.numpy import save_file  # noqa: E402

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import head_read_projection as readproj  # noqa: E402
import head_steering_directions as steering  # noqa: E402

# Signal head (head 1, head_dim 3): slot0 carries a "wrongness read" that, on a
# fixture WITH within-label correctness variance, lets the prompt-token
# projection separate wrong from correct answered items. Head 0 is noise.
NUM_HEADS = 2
HEAD_DIM = 3
WIDTH = NUM_HEADS * HEAD_DIM


def _row(key: str, *, label: str, refused: bool, correct: bool, confidence: float) -> dict:
    return {
        "row_key": key,
        "label": label,
        "question": f"Q {key}",
        "strata": [],
        "source_arms": {
            "arm": {
                "refused": refused,
                "correct": correct,
                "truthful": correct and not refused,
                "stated_confidence": confidence,
            }
        },
    }


def _vec(slot0: float) -> dict:
    return {
        "L0": np.zeros(WIDTH, dtype=np.float32),
        "L1": np.asarray([0.0, 0.0, 0.0, slot0, 0.0, 1.0], dtype=np.float32),
    }


def _write_fixture(root: Path) -> Path:
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
    (extraction_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    rng = np.random.default_rng(0)
    rows = []
    tensors = {}

    def add(key, *, label, refused, correct, confidence, slot0):
        rows.append(_row(key, label=label, refused=refused, correct=correct, confidence=confidence))
        tensors[key] = _vec(slot0 + float(rng.normal(0, 1e-3)))

    # Failure-axis construction groups (unknown answered-wrong vs unknown refused).
    for i in range(6):
        add(f"uaw_{i}", label="unknown", refused=False, correct=False, confidence=0.8, slot0=1.0)
        add(f"ur_{i}", label="unknown", refused=True, correct=False, confidence=0.1, slot0=-1.0)
    # Within-label correctness variance so the read test is NON-degenerate:
    # some known answered are WRONG (high read, high stated confidence -> a
    # confident error the read should still flag), some known answered correct.
    for i in range(6):
        add(f"kw_{i}", label="known", refused=False, correct=False, confidence=0.9, slot0=0.9)
        add(f"kc_{i}", label="known", refused=False, correct=True, confidence=0.6, slot0=-0.8)
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    for key, t in tensors.items():
        save_file(t, str(extraction_dir / f"{key}__h_lora.safetensors"))
    return extraction_dir


def _failure_json(extraction_dir: Path, out_root: Path) -> Path:
    spec = {
        "label": "failure",
        "behavior_arm": "arm",
        "arm_role": "h_lora",
        "extraction_dir": str(extraction_dir),
        "extraction_manifest": str(extraction_dir / "manifest.json"),
        "contrast": {
            "name": "unknown_answered_wrong_vs_unknown_refused",
            "min_rows_per_group": 2,
            "positive": {"label": "unknown", "refused": False, "correct": False},
            "negative": {"label": "unknown", "refused": True},
        },
        "targets": [{"layer": 1, "head": 1}],
    }
    steering.build_directions(spec, output_root=out_root)
    return out_root / "failure" / "steering_directions.json"


def test_read_predicts_wrong_on_known_population(tmp_path):
    extraction_dir = _write_fixture(tmp_path)
    failure_path = _failure_json(extraction_dir, tmp_path / "failure_out")
    summary = readproj.run(failure_path, tmp_path / "read_out")

    assert summary["ok"] is True
    known = summary["populations"]["known_answered_GENERALIZATION"]
    # 6 wrong + 6 correct known-answered -> non-degenerate, read separates them.
    assert known["n_answered"] == 12
    assert 0 < known["n_wrong"] < known["n_answered"]
    assert known["auroc_read_predicts_wrong"] == pytest.approx(1.0, abs=0.05)
    # The confidence comparison path populates a numeric gap.
    assert known["read_minus_confidence"] is not None
    assert Path(summary["_written"]).exists()


def test_degenerate_population_returns_none(tmp_path):
    # All-correct known population -> AUROC undefined, reported as None not a crash.
    extraction_dir = tmp_path / "extraction"
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
    (extraction_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    rng = np.random.default_rng(1)
    rows, tensors = [], {}
    for i in range(6):
        rows.append(_row(f"uaw_{i}", label="unknown", refused=False, correct=False, confidence=0.8))
        tensors[f"uaw_{i}"] = _vec(1.0 + float(rng.normal(0, 1e-3)))
        rows.append(_row(f"ur_{i}", label="unknown", refused=True, correct=False, confidence=0.1))
        tensors[f"ur_{i}"] = _vec(-1.0 + float(rng.normal(0, 1e-3)))
        # known answered are ALL correct -> degenerate for the wrongness test.
        rows.append(_row(f"kc_{i}", label="known", refused=False, correct=True, confidence=0.6))
        tensors[f"kc_{i}"] = _vec(-0.8 + float(rng.normal(0, 1e-3)))
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    for key, t in tensors.items():
        save_file(t, str(extraction_dir / f"{key}__h_lora.safetensors"))

    failure_path = _failure_json(extraction_dir, tmp_path / "failure_out")
    summary = readproj.run(failure_path, tmp_path / "read_out")
    known = summary["populations"]["known_answered_GENERALIZATION"]
    assert known["n_wrong"] == 0
    assert known["auroc_read_predicts_wrong"] is None
    assert "INCONCLUSIVE" in summary["verdict"]
