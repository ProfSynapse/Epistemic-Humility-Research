from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import phase3_residual_intervention as ri  # noqa: E402


# --- intervention math ---------------------------------------------------

def test_ablate_removes_component():
    theta = np.array([3.0, 0.0, 0.0])  # not unit; should be normalized internally
    h = np.array([[5.0, 2.0, 1.0], [9.0, -1.0, 4.0]])
    out = ri.apply_intervention(h, theta, mode="ablate")
    # component along x removed; y,z preserved
    assert np.allclose(out[:, 0], 0.0)
    assert np.allclose(out[:, 1:], h[:, 1:])


def test_ablate_is_idempotent():
    rng = np.random.default_rng(1)
    theta = rng.normal(size=8)
    h = rng.normal(size=(5, 8))
    once = ri.apply_intervention(h, theta, mode="ablate")
    twice = ri.apply_intervention(once, theta, mode="ablate")
    assert np.allclose(once, twice, atol=1e-9)


def test_shift_adds_alpha_sigma_unit():
    theta = np.array([0.0, 2.0, 0.0])  # unit = [0,1,0]
    h = np.array([[1.0, 1.0, 1.0]])
    out = ri.apply_intervention(h, theta, mode="shift", alpha=3.0, sigma=2.0)
    # +alpha*sigma along unit theta = +6 on the y axis
    assert np.allclose(out, [[1.0, 7.0, 1.0]])


def test_baseline_is_noop():
    h = np.array([[1.0, 2.0]])
    assert np.allclose(ri.apply_intervention(h, np.array([1.0, 0.0]), mode="baseline"), h)


def test_unknown_mode_raises():
    with pytest.raises(ri.ResidualInterventionError):
        ri.apply_intervention(np.zeros((1, 2)), np.array([1.0, 0.0]), mode="nope")


# --- spec / arms ---------------------------------------------------------

def test_build_intervention_spec_normalizes_theta_and_maps_block():
    spec = ri.build_intervention_spec({"layer": 35, "theta": [3.0, 4.0], "sigma": 2.0})
    assert spec["block"] == 34
    assert pytest.approx(np.linalg.norm(spec["theta"]), abs=1e-9) == 1.0
    assert spec["sigma"] == 2.0


def test_parse_arms_requires_baseline():
    with pytest.raises(ri.ResidualInterventionError):
        ri.parse_arms([{"arm_id": "ablate", "mode": "ablate"}])


def test_parse_arms_rejects_duplicate_and_bad_mode():
    with pytest.raises(ri.ResidualInterventionError):
        ri.parse_arms([{"arm_id": "baseline", "mode": "baseline"},
                       {"arm_id": "baseline", "mode": "ablate"}])
    with pytest.raises(ri.ResidualInterventionError):
        ri.parse_arms([{"arm_id": "baseline", "mode": "baseline"},
                       {"arm_id": "x", "mode": "weird"}])


def test_parse_arms_normalizes():
    arms = ri.parse_arms([
        {"arm_id": "baseline", "mode": "baseline"},
        {"arm_id": "ablate", "mode": "ablate"},
        {"arm_id": "amp", "mode": "shift", "alpha": 4.0},
    ])
    assert [a["arm_id"] for a in arms] == ["baseline", "ablate", "amp"]
    assert arms[2]["alpha"] == 4.0


# --- write hook (fake tensor) -------------------------------------------

class _FakeTensor:
    def __init__(self, arr):
        self.arr = np.asarray(arr, dtype=np.float64)

    def new_tensor(self, data):
        return _FakeTensor(data)

    def __matmul__(self, other):
        return _FakeTensor(self.arr @ other.arr)

    def unsqueeze(self, axis):
        return _FakeTensor(np.expand_dims(self.arr, axis))

    def __mul__(self, other):
        o = other.arr if isinstance(other, _FakeTensor) else other
        return _FakeTensor(self.arr * o)

    __rmul__ = __mul__

    def __sub__(self, other):
        return _FakeTensor(self.arr - other.arr)

    def __add__(self, other):
        return _FakeTensor(self.arr + other.arr)


def test_write_hook_ablate_matches_reference():
    spec = ri.build_intervention_spec({"layer": 3, "theta": [1.0, 0.0, 0.0], "sigma": 1.0})
    hook = ri.make_residual_write_hook(spec, {"arm_id": "ablate", "mode": "ablate", "alpha": 0.0})
    hs = _FakeTensor([[[5.0, 2.0, 1.0], [9.0, -1.0, 4.0]]])
    out = hook(None, (None,), (hs,))
    got = out[0].arr
    ref = ri.apply_intervention(hs.arr, np.array(spec["theta"]), mode="ablate")
    assert np.allclose(got, ref)


def test_write_hook_shift_matches_reference():
    spec = ri.build_intervention_spec({"layer": 3, "theta": [0.0, 1.0, 0.0], "sigma": 2.0})
    hook = ri.make_residual_write_hook(spec, {"arm_id": "amp", "mode": "shift", "alpha": 3.0})
    hs = _FakeTensor([[[1.0, 1.0, 1.0]]])
    out = hook(None, (None,), (hs,))
    ref = ri.apply_intervention(hs.arr, np.array(spec["theta"]), mode="shift", alpha=3.0, sigma=2.0)
    assert np.allclose(out[0].arr, ref)


# --- analysis / verdict --------------------------------------------------

def _rows(arm_id, cell, n, refused_rate, correct_rate=0.0):
    rows = []
    n_ref = int(round(refused_rate * n))
    for i in range(n):
        refused = i < n_ref
        rows.append({"arm_id": arm_id, "behavior_cell": cell,
                     "refused": refused, "correct": (not refused) and (i < int(correct_rate * n))})
    return rows


def test_analyze_load_bearing_verdict():
    rows = []
    rows += _rows("baseline", ri.KNOWN_REFUSED, 100, 1.0)
    rows += _rows("baseline", ri.KNOWN_ANSWERED, 100, 0.0)
    rows += _rows("ablate", ri.KNOWN_REFUSED, 100, 0.4)   # big drop
    rows += _rows("ablate", ri.KNOWN_ANSWERED, 100, 0.05)  # control stays low
    out = ri.analyze_arms(rows)
    assert out["by_arm"]["ablate"][ri.KNOWN_REFUSED]["refusal_rate"] == 0.4
    assert out["verdict"].startswith("LOAD-BEARING")


def test_analyze_not_load_bearing_verdict():
    rows = []
    rows += _rows("baseline", ri.KNOWN_REFUSED, 100, 1.0)
    rows += _rows("baseline", ri.KNOWN_ANSWERED, 100, 0.0)
    rows += _rows("ablate", ri.KNOWN_REFUSED, 100, 0.95)  # barely moves
    rows += _rows("ablate", ri.KNOWN_ANSWERED, 100, 0.0)
    out = ri.analyze_arms(rows)
    assert out["verdict"].startswith("NOT-LOAD-BEARING")


def test_analyze_inverted_verdict():
    rows = []
    rows += _rows("baseline", ri.KNOWN_REFUSED, 100, 0.6)
    rows += _rows("baseline", ri.KNOWN_ANSWERED, 100, 0.0)
    rows += _rows("ablate", ri.KNOWN_REFUSED, 100, 0.9)  # ablation raised refusal
    rows += _rows("ablate", ri.KNOWN_ANSWERED, 100, 0.0)
    out = ri.analyze_arms(rows)
    assert out["verdict"].startswith("INVERTED")
