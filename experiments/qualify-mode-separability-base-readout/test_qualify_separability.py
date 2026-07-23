"""Fast, model-free unit tests for the resumable extraction writer and the
scoring/banding logic in fit_readouts.py. No model load, no GPU, no network.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest

from extract_hidden_states import ResumableFeatureWriter
from fit_readouts import banded_predict, bootstrap_auroc_ci, confusion_and_prf


def test_resumable_writer_round_trip_and_resume():
    with tempfile.TemporaryDirectory() as td:
        idx = Path(td) / "index.jsonl"
        feats = Path(td) / "features" / "combined.f32.bin"
        w = ResumableFeatureWriter(idx, feats, n_depths=2, hidden_size=3)
        assert w.n_done() == 0
        v1 = np.arange(6, dtype=np.float32)
        w.append("row_a", "fit", "QUALIFY", 15, v1)
        assert w.is_done("row_a")
        assert w.n_done() == 1

        # simulate a fresh process resuming: re-open, index should reflect prior work
        w2 = ResumableFeatureWriter(idx, feats, n_depths=2, hidden_size=3)
        assert w2.is_done("row_a")
        assert not w2.is_done("row_b")
        v2 = np.arange(6, 12, dtype=np.float32)
        w2.append("row_b", "dev", "ABSTAIN", 2, v2)
        assert w2.n_done() == 2

        # verify on-disk bytes are exactly the two concatenated records, in order
        raw = np.fromfile(feats, dtype=np.float32)
        assert raw.shape == (12,)
        assert np.allclose(raw[:6], v1)
        assert np.allclose(raw[6:], v2)

        lines = [json.loads(l) for l in open(idx)]
        assert [l["row_key"] for l in lines] == ["row_a", "row_b"]


def test_resumable_writer_rejects_wrong_record_length():
    with tempfile.TemporaryDirectory() as td:
        idx = Path(td) / "index.jsonl"
        feats = Path(td) / "features" / "combined.f32.bin"
        w = ResumableFeatureWriter(idx, feats, n_depths=2, hidden_size=3)
        with pytest.raises(AssertionError):
            w.append("row_a", "fit", "QUALIFY", 15, np.arange(5, dtype=np.float32))


def test_banded_predict_matches_registered_thresholds():
    thresholds = {"abstain_max": 10, "qualify_max": 21}
    k = np.array([0, 10, 11, 16, 21, 22, 32])
    labels = banded_predict(k, thresholds)
    assert list(labels) == ["ABSTAIN", "ABSTAIN", "QUALIFY", "QUALIFY", "QUALIFY", "ANSWER", "ANSWER"]


def test_confusion_and_prf_perfect_and_imperfect():
    y_true = np.array(["ABSTAIN", "QUALIFY", "ANSWER", "QUALIFY"])
    y_pred_perfect = np.array(["ABSTAIN", "QUALIFY", "ANSWER", "QUALIFY"])
    perfect = confusion_and_prf(y_true, y_pred_perfect)
    assert perfect["accuracy"] == 1.0
    assert perfect["per_mode"]["QUALIFY"]["recall"] == 1.0

    y_pred_bad = np.array(["ABSTAIN", "ABSTAIN", "ANSWER", "ANSWER"])
    bad = confusion_and_prf(y_true, y_pred_bad)
    assert bad["accuracy"] == 0.5
    assert bad["per_mode"]["QUALIFY"]["recall"] == 0.0


def test_bootstrap_auroc_ci_perfect_separation_and_determinism():
    rng = np.random.RandomState(0)
    y = np.array([0] * 50 + [1] * 50)
    score_perfect = np.array([0.0] * 50 + [1.0] * 50)
    result = bootstrap_auroc_ci(y, score_perfect, n_resamples=200, seed=123)
    assert result["point"] == 1.0
    assert result["ci_lower"] > 0.9

    # same seed -> byte-identical bootstrap draws -> identical CI
    result2 = bootstrap_auroc_ci(y, score_perfect, n_resamples=200, seed=123)
    assert result == result2


def test_bootstrap_auroc_ci_chance_separation():
    rng = np.random.RandomState(0)
    y = np.array([0, 1] * 100)
    score_random = rng.rand(200)
    result = bootstrap_auroc_ci(y, score_random, n_resamples=500, seed=7)
    assert 0.3 < result["point"] < 0.7  # near chance, loose bound to avoid flakiness
