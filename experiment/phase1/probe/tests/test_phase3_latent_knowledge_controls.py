from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROBE_DIR))

import phase3_latent_knowledge_controls as ctl  # noqa: E402


def test_lexical_separable_vs_random():
    # class 1 questions all share a token absent from class 0 -> perfectly separable.
    texts = [f"alpha widget {i}" for i in range(20)] + [f"beta gadget {i}" for i in range(20)]
    y = np.array([0] * 20 + [1] * 20)
    assert ctl.lexical_cv_auroc(texts, y) > 0.9
    # shared vocabulary -> no lexical signal (chance).
    same = [f"same words here {i % 3}" for i in range(40)]
    auc = ctl.lexical_cv_auroc(same, y)
    assert 0.3 < auc < 0.7


def test_verdict_margin_bands():
    assert ctl._verdict_margin(0.99, 0.70)[0] == "INTERNAL-STATE"
    assert ctl._verdict_margin(0.99, 0.985)[0] == "LEXICAL-CONFOUND"
    assert ctl._verdict_margin(0.80, 0.95)[0] == "LEXICAL-DOMINATES"


def test_load_rows_roundtrip(tmp_path):
    p = tmp_path / "rows.jsonl"
    recs = [
        {"probe_pool_row_key": "a::b::000000::c", "label": "known",
         "behavior_cell": "known_refused", "question": "Q1?"},
        {"probe_pool_row_key": "a::b::000001::d", "label": "unknown",
         "behavior_cell": "unknown_refused", "question": "Q2?"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in recs), encoding="utf-8")
    rows = ctl.load_rows(p)
    assert len(rows) == 2
    assert rows[0]["row_key"] == "a::b::000000::c" and rows[0]["question"] == "Q1?"


def _fake_rows(n_known_ans=12, n_known_ref=10, n_unknown=12):
    rows = []
    i = 0
    for _ in range(n_known_ans):
        rows.append({"row_key": f"k::ans::{i:06d}::r", "label": "known",
                     "behavior_cell": "known_correct_answered", "question": f"capital fact {i}"})
        i += 1
    for _ in range(n_known_ref):
        rows.append({"row_key": f"k::ref::{i:06d}::r", "label": "known",
                     "behavior_cell": "known_refused", "question": f"obscure trivia {i}"})
        i += 1
    for _ in range(n_unknown):
        rows.append({"row_key": f"u::ref::{i:06d}::r", "label": "unknown",
                     "behavior_cell": "unknown_refused", "question": f"unanswerable riddle {i}"})
        i += 1
    return rows


def _patch_load_layers(monkeypatch, separable_label_fn):
    """Patch lkp.load_layers so a chosen binary label is linearly separable in the activations."""
    rng = np.random.default_rng(0)

    def fake(extraction_dir, row_keys, layers, *, source="h_lora"):
        labels = np.array([separable_label_fn(rk) for rk in row_keys])
        out = {}
        for L in layers:
            X = rng.normal(size=(len(row_keys), 8))
            X[:, 0] += labels * 6.0  # strong separating dim
            out[L] = X
        return out

    monkeypatch.setattr(ctl.lkp, "load_layers", fake)


def test_a1_internal_state(monkeypatch):
    rows = _fake_rows()
    # residual separates known(0)/unknown(1) perfectly; question text is per-class distinct too,
    # but the activation margin is engineered larger -> still INTERNAL-STATE or at worst confound.
    _patch_load_layers(monkeypatch, lambda rk: 1 if rk.startswith("u::") else 0)
    res = ctl.a1_lexical_baseline(Path("/nope"), rows, layers=[10, 20])
    assert res["residual_best"]["auroc"] > 0.9
    assert res["verdict"] in {"INTERNAL-STATE", "LEXICAL-CONFOUND", "LEXICAL-DOMINATES"}


def test_a2_within_known_split(monkeypatch):
    rows = _fake_rows()
    # residual separates known_refused from known_answered; unknown rows excluded by A2.
    _patch_load_layers(monkeypatch, lambda rk: 1 if rk.startswith("k::ref") else 0)
    res = ctl.a2_within_known(Path("/nope"), rows, layers=[10, 20])
    assert res["n_known_refused"] == 10 and res["n_known_answered"] == 12
    assert res["residual_best"]["auroc"] > 0.9


def test_a2_degenerate_raises(monkeypatch):
    rows = _fake_rows(n_known_ref=0)
    with pytest.raises(ctl.ControlError):
        ctl.a2_within_known(Path("/nope"), rows, layers=[10])
