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

import phase3_head_axis_geometry as geom  # noqa: E402
import phase3_head_steering_directions as steering  # noqa: E402

# One signal head (head 1, head_dim 3) with three interpretable slots:
#   slot0 = refuse-ness (high when refused), slot1 = unknown-ness (high when
#   unknown), slot2 = constant. Head 0 is pure noise. With this planting the
#   failure axis F = mean(unknown_answered_wrong) - mean(unknown_refused) points
#   along -slot0 (anti-refuse), the refuse-vs-answer axis R points along +slot0,
#   and the knowledge-boundary axis K points along +slot1 -- so cos(F,R) ~ -1 and
#   cos(F,K) ~ 0 by construction.
NUM_HEADS = 2
HEAD_DIM = 3
WIDTH = NUM_HEADS * HEAD_DIM
N_PER_GROUP = 6


def _row(row_key: str, *, label: str, refused: bool, correct: bool) -> dict:
    return {
        "row_key": row_key,
        "label": label,
        "question": f"Q {row_key}",
        "strata": [],
        "source_arms": {
            "fixture_arm": {
                "refused": refused,
                "correct": correct,
                "truthful": correct and not refused,
                "stated_confidence": 0.0 if refused else 0.9,
            }
        },
    }


def _vec(refuseness: float, unknownness: float) -> dict:
    # head 0 = noise (zeros); head 1 slots = [refuseness, unknownness, const]
    return {
        "L0": np.zeros(WIDTH, dtype=np.float32),
        "L1": np.asarray([0.0, 0.0, 0.0, refuseness, unknownness, 1.0], dtype=np.float32),
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

    groups = {
        # (label, refused, correct, refuseness, unknownness)
        "ur": ("unknown", True, False, 1.0, 1.0),  # unknown_refused
        "uaw": ("unknown", False, False, 0.0, 1.0),  # unknown_answered_wrong
        "kr": ("known", True, False, 1.0, 0.0),  # known_refused (over-refusal)
        "kc": ("known", False, True, 0.0, 0.0),  # known_correct_answered
    }
    rows = []
    tensors = {}
    rng = np.random.default_rng(0)
    for gkey, (label, refused, correct, rf, uk) in groups.items():
        for i in range(N_PER_GROUP):
            key = f"{gkey}_{i}"
            rows.append(_row(key, label=label, refused=refused, correct=correct))
            jitter = float(rng.normal(0, 1e-3))
            tensors[key] = _vec(rf + jitter, uk + jitter)
    with (extraction_dir / "rows.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")
    for key, t in tensors.items():
        save_file(t, str(extraction_dir / f"{key}__h_lora.safetensors"))
    return extraction_dir


def _failure_json(extraction_dir: Path, out_root: Path) -> Path:
    """Build a real failure-axis artifact via the validated builder."""
    spec = {
        "label": "failure",
        "behavior_arm": "fixture_arm",
        "arm_role": "h_lora",
        "extraction_dir": str(extraction_dir),
        "extraction_manifest": str(extraction_dir / "manifest.json"),
        "contrast": {
            "name": "unknown_answered_wrong_vs_unknown_refused",
            "min_rows_per_group": 2,
            "positive": {"label": "unknown", "refused": False, "correct": False},
            "negative": {"label": "unknown", "refused": True},
        },
        # Only the signal head: zero-theta noise heads are never localization
        # targets in practice, and an undefined (zero) theta has no parity.
        "targets": [{"layer": 1, "head": 1}],
    }
    artifact = steering.build_directions(spec, output_root=out_root)
    return out_root / artifact["label"] / "steering_directions.json"


def test_geometry_planted_axes_and_parity(tmp_path):
    extraction_dir = _write_fixture(tmp_path)
    failure_path = _failure_json(extraction_dir, tmp_path / "failure_out")
    summary = geom.run(failure_path, tmp_path / "geom_out", min_rows=2)

    assert summary["ok"] is True
    # Parity self-check must pass: rebuilding F matches the stored theta exactly.
    assert summary["parity_self_check"]["all_heads_match"] is True

    by_head = {(h["layer"], h["head"]): h for h in summary["per_head"]}
    signal = by_head[(1, 1)]
    # Planted geometry: F anti-parallel to the refuse motor, orthogonal to knowledge.
    assert signal["cos_failure_refuse_motor"] == pytest.approx(-1.0, abs=0.05)
    assert abs(signal["cos_failure_knowledge_boundary"]) < 0.1
    # Output artifact written.
    assert Path(summary["_written"]).exists()


def test_verdict_branches():
    parity = True
    # Decision-axis dominant (the real-data shape): strong |cos| to refuse motor,
    # near-zero to knowledge boundary, anti-aligned sign.
    v = geom._verdict(np.full(11, 0.80), np.full(11, 0.12), parity, mean_signed_fr=-0.80)
    assert "DECISION-AXIS DOMINANT" in v and "ANTI-aligned" in v

    # Knowledge-boundary dominant -> H_monitor geometry supported.
    v = geom._verdict(np.full(11, 0.15), np.full(11, 0.70), parity, mean_signed_fr=0.10)
    assert "H_monitor SUPPORTED" in v

    # Naive refusal motor (collinear).
    v = geom._verdict(np.full(11, 0.98), np.full(11, 0.05), parity, mean_signed_fr=0.98)
    assert "H_refusal_motor" in v

    # Broken parity invalidates the cosines.
    v = geom._verdict(np.full(11, 0.80), np.full(11, 0.12), False, mean_signed_fr=-0.80)
    assert v.startswith("INVALID")


def test_cos_helpers():
    assert geom._cos(np.array([1.0, 0, 0]), np.array([1.0, 0, 0])) == pytest.approx(1.0)
    assert geom._cos(np.array([1.0, 0, 0]), np.array([-1.0, 0, 0])) == pytest.approx(-1.0)
    assert geom._cos(np.array([1.0, 0, 0]), np.array([0.0, 1, 0])) == pytest.approx(0.0)
    assert geom._cos(np.zeros(3), np.array([1.0, 0, 0])) == 0.0
