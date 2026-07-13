from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("sklearn")

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import latent_knowledge_probe as lkp  # noqa: E402


def test_row_key_to_tensor_file():
    p = lkp.row_key_to_tensor_file(Path("/x"), "selfaware::selfaware::000000::selfaware-1")
    assert p.name == "selfaware__selfaware__000000__selfaware-1__h_lora.safetensors"


def test_cv_auroc_separable_high():
    rng = np.random.default_rng(0)
    n, d = 120, 8
    y = np.array([0] * (n // 2) + [1] * (n // 2))
    X = rng.normal(size=(n, d))
    X[:, 0] += y * 4.0  # one strongly informative dimension
    assert lkp.cv_auroc(X, y) > 0.9


def test_cv_auroc_random_chance():
    rng = np.random.default_rng(1)
    y = np.array([0, 1] * 60)
    X = rng.normal(size=(120, 8))
    assert 0.35 < lkp.cv_auroc(X, y) < 0.65


def test_fit_score_probe_direction():
    rng = np.random.default_rng(2)
    Xk = rng.normal(loc=0.0, size=(40, 6))   # class 0 (known)
    Xu = rng.normal(loc=3.0, size=(40, 6))   # class 1 (unknown)
    Xtr = np.vstack([Xk, Xu])
    ytr = np.array([0] * 40 + [1] * 40)
    p_known = lkp.fit_score_probe(Xtr, ytr, Xk).mean()
    p_unknown = lkp.fit_score_probe(Xtr, ytr, Xu).mean()
    assert p_known < 0.5 < p_unknown


def test_gap_verdict_bands():
    assert "LATENT-KNOWLEDGE" in lkp._gap_verdict(0.1)
    assert "INTERNAL-UNCERTAINTY" in lkp._gap_verdict(0.9)
    assert "MIXED" in lkp._gap_verdict(0.5)


def test_analyze_synthetic(monkeypatch):
    # Build a synthetic 3-cell world; known cells separable from unknown on layer 5.
    rng = np.random.default_rng(3)
    behavior = {}
    cells = ([("known_correct_answered", "known")] * 20
             + [("known_refused", "known")] * 10
             + [("unknown_refused", "unknown")] * 20)
    vecs = {}
    for i, (cell, label) in enumerate(cells):
        rk = f"a::b::{i:06d}::r{i}"
        behavior[rk] = {"label": label, "behavior_cell": cell}
        base = 0.0 if label == "known" else 5.0
        vecs[rk] = (rng.normal(size=6) + base).astype(np.float64)

    def fake_load(_dir, row_keys, layers, source="h_lora"):
        m = np.asarray([vecs[k] for k in row_keys], dtype=np.float64)
        return {L: m for L in layers}

    monkeypatch.setitem(lkp.analyze.__globals__, "load_layers", fake_load)
    res = lkp.analyze(Path("/unused"), behavior, layers=[5])
    assert res["best_layer"]["auroc"] > 0.9
    # known_refused was drawn from the KNOWN distribution -> should look known-answered.
    assert "LATENT-KNOWLEDGE" in res["over_refusal_gap"]["verdict"]
