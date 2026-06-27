from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import phase3_residual_read_trajectory as rrt  # noqa: E402


# --- direction fit -------------------------------------------------------

def test_mass_mean_direction_is_unit_and_points_pos_minus_neg():
    x_pos = np.array([[2.0, 0.0], [2.0, 0.0]])
    x_neg = np.array([[0.0, 0.0], [0.0, 0.0]])
    theta = rrt.mass_mean_direction(x_pos, x_neg)
    assert pytest.approx(np.linalg.norm(theta), abs=1e-9) == 1.0
    assert theta[0] > 0 and abs(theta[1]) < 1e-9


def test_mass_mean_direction_degenerate_raises():
    x = np.array([[1.0, 1.0], [1.0, 1.0]])
    with pytest.raises(rrt.ResidualReadTrajectoryError):
        rrt.mass_mean_direction(x, x)


def test_projection_sigma_and_auroc_separate():
    rng = np.random.default_rng(0)
    x_pos = rng.normal(3.0, 0.5, size=(40, 4))
    x_neg = rng.normal(-3.0, 0.5, size=(40, 4))
    theta = rrt.mass_mean_direction(x_pos, x_neg)
    sigma = rrt.projection_sigma(np.vstack([x_pos, x_neg]), theta)
    assert sigma > 0
    auroc = rrt.projection_auroc(x_pos, x_neg, theta)
    assert auroc > 0.95


# --- spec / hook ---------------------------------------------------------

def test_build_residual_read_spec_maps_layer_to_block():
    spec = rrt.build_residual_read_spec({"layer": 35, "theta": [0.1, 0.2], "sigma": 1.5})
    assert spec["layer"] == 35
    assert spec["block"] == 34
    assert spec["theta"] == [0.1, 0.2]
    assert spec["sigma"] == 1.5


def test_build_residual_read_spec_rejects_embedding_layer():
    with pytest.raises(rrt.ResidualReadTrajectoryError):
        rrt.build_residual_read_spec({"layer": 0, "theta": [0.1], "sigma": 1.0})


def test_build_residual_read_spec_rejects_nonpositive_sigma():
    with pytest.raises(rrt.ResidualReadTrajectoryError):
        rrt.build_residual_read_spec({"layer": 5, "theta": [0.1], "sigma": 0.0})


class _FakeTensor:
    """Minimal tensor-like supporting the hook's .float()/.new_tensor()/@/.item()."""

    def __init__(self, arr):
        self.arr = np.asarray(arr, dtype=np.float64)

    def __getitem__(self, idx):
        return _FakeTensor(self.arr[idx])

    def float(self):
        return self

    def new_tensor(self, data):
        return _FakeTensor(data)

    def __matmul__(self, other):
        return _FakeTensor(self.arr @ other.arr)

    def item(self):
        return float(self.arr)


def test_make_residual_read_hook_records_last_position_projection():
    spec = {"layer": 3, "block": 2, "theta": [1.0, 0.0, 0.0], "sigma": 1.0}
    store: list[float] = []
    hook = rrt.make_residual_read_hook(spec, store=store)
    # block output as a tuple; hidden states [batch=1, seq=2, hidden=3]
    hs = _FakeTensor([[[9.0, 9.0, 9.0], [5.0, 1.0, 2.0]]])
    ret = hook(None, (None,), (hs,))
    assert ret is None
    # last position = [5,1,2]; dot theta=[1,0,0] -> 5.0
    assert store == [5.0]
    # second forward: bare tensor (not a tuple)
    hs2 = _FakeTensor([[[7.0, 0.0, 0.0]]])
    hook(None, (None,), hs2)
    assert store == [5.0, 7.0]


# --- lexical onset -------------------------------------------------------

def test_find_lexical_onset_returns_trajectory_index():
    toks = ['{"', "answer", '": "', "I", " don't", " know", " the", " answer"]
    onset = rrt.find_lexical_onset(toks)
    # cumulative hits "i don't know" at token index 5 -> trajectory index 6
    assert onset == 6


def test_find_lexical_onset_none_when_no_refusal():
    toks = ['{"', "answer", '": "', "Paris", '"}']
    assert rrt.find_lexical_onset(toks) is None


# --- per-row summary -----------------------------------------------------

def test_summarize_row_trajectory_windows():
    # prompt + 4 generated positions; onset at trajectory idx 3 (gen tokens 0,1 pre; 2,3 post)
    projections = [2.0, 4.0, 6.0, 8.0, 10.0]
    summ = rrt.summarize_row_trajectory(projections, sigma=2.0, lexical_onset_idx=3)
    assert summ["n_forward"] == 5
    assert summ["prompt_read_std"] == 1.0  # 2/2
    # gen positions std = [2,3,4,5]; mean 3.5
    assert summ["gen_read_std"] == pytest.approx(3.5)
    # pre = std[1:3] = [2,3] -> 2.5 ; post = std[3:] = [4,5] -> 4.5
    assert summ["pre_lexical_read_std"] == pytest.approx(2.5)
    assert summ["post_lexical_read_std"] == pytest.approx(4.5)


def test_summarize_row_trajectory_no_onset_all_pre_lexical():
    projections = [1.0, 2.0, 3.0]
    summ = rrt.summarize_row_trajectory(projections, sigma=1.0, lexical_onset_idx=None)
    assert summ["lexical_onset_idx"] is None
    assert summ["pre_lexical_read_std"] == pytest.approx(2.5)  # mean([2,3])
    assert np.isnan(summ["post_lexical_read_std"])


# --- analysis / verdict --------------------------------------------------

def _row(cell, prompt, pre, post):
    return {"behavior_cell": cell, "prompt_read_std": prompt,
            "gen_read_std": (pre + post) / 2, "pre_lexical_read_std": pre,
            "post_lexical_read_std": post}


def test_analyze_pre_commitment_verdict():
    rows = (
        [_row(rrt.KNOWN_REFUSED, 1.5, 1.2, 1.8) for _ in range(10)]
        + [_row(rrt.KNOWN_ANSWERED, -1.5, -1.0, -1.2) for _ in range(10)]
    )
    out = rrt.analyze_trajectories(rows)
    assert out["groups"][rrt.KNOWN_REFUSED] == 10
    assert out["separation"]["pre_lexical_read_std"]["separation_pos_minus_neg"] > 0
    assert out["verdict"].startswith("PRE-COMMITMENT")


def test_analyze_decision_echo_verdict():
    # pre-lexical separation ~0, post-lexical large
    rows = (
        [_row(rrt.KNOWN_REFUSED, 1.5, 0.01, 2.0) for _ in range(10)]
        + [_row(rrt.KNOWN_ANSWERED, -1.5, -0.01, -2.0) for _ in range(10)]
    )
    out = rrt.analyze_trajectories(rows)
    assert out["verdict"].startswith("DECISION-ECHO")


def test_analyze_inconclusive_when_group_empty():
    rows = [_row(rrt.KNOWN_REFUSED, 1.0, 1.0, 1.0) for _ in range(3)]
    out = rrt.analyze_trajectories(rows)
    assert out["verdict"].startswith("INCONCLUSIVE")
