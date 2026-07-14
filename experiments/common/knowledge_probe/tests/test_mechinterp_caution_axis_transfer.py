from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import caution_axis_transfer as cat  # noqa: E402


def _arms(monkeypatch, shared_dim: bool):
    """Patch load_known so each regimen's caution label is separated on a chosen dim."""
    rng = np.random.default_rng(0)

    def fake(extraction_dir, behavior_rows, *, layer, source="h_lora"):
        name = str(behavior_rows)
        n = 120
        y = np.array([1] * 40 + [0] * 80)
        X = rng.normal(size=(n, 8))
        # shared_dim: all regimens load caution on dim0 -> aligned.
        # else: regimen A on dim0, B on dim1, C on dim2 -> orthogonal.
        if shared_dim:
            d = 0
        else:
            d = {"A": 0, "B": 1, "C": 2}[name]
        X[:, d] += y * 6.0
        keys = [f"{name}::{i}" for i in range(n)]
        return X, y, keys

    monkeypatch.setitem(cat.caution_axis_transfer.__globals__, "load_known", fake)
    return [{"name": n, "extraction_dir": f"/ext/{n}", "behavior_rows": n} for n in ("A", "B", "C")]


def test_shared_axis(monkeypatch):
    arms = _arms(monkeypatch, shared_dim=True)
    res = cat.caution_axis_transfer(arms, layer=35)
    assert res["mean_cross_cosine"] > 0.5
    assert res["verdict"] in {"SHARED-AXIS", "PARTIAL-SHARED"}
    assert res["mean_cross_cosine"] > res["mean_random_floor"]


def test_regimen_specific(monkeypatch):
    arms = _arms(monkeypatch, shared_dim=False)
    res = cat.caution_axis_transfer(arms, layer=35)
    assert res["mean_cross_cosine"] < 0.4
    assert res["verdict"] in {"REGIMEN-SPECIFIC", "PARTIAL-SHARED"}


def test_matrix_diagonal_is_one(monkeypatch):
    arms = _arms(monkeypatch, shared_dim=True)
    res = cat.caution_axis_transfer(arms, layer=35)
    for name in ("A", "B", "C"):
        assert res["cosine_matrix"][f"{name}|{name}"] == pytest.approx(1.0, abs=1e-6)


def test_parse_arm():
    a = cat._parse_arm("grpo_v2:/path/to/ext:/path/to/rows.jsonl")
    assert a["name"] == "grpo_v2"
    assert a["extraction_dir"] == "/path/to/ext"
    assert a["behavior_rows"] == "/path/to/rows.jsonl"
