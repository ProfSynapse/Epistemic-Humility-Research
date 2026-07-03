"""Amendment AC offline tests: couple-mode math, doubt gain map, analysis.

SPEC: experiment/protocol/AMENDMENT-AC-doubt-regulated-caution.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

PROBE_DIR = Path(__file__).resolve().parents[1]
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

import build_doubt_gain_map as bgm  # noqa: E402
import phase3_ac_doubt_coupled_analysis as aca  # noqa: E402
import phase3_residual_intervention as ri  # noqa: E402
import phase3_residual_intervention_runner as runner  # noqa: E402


# --- couple intervention math ---------------------------------------------

def test_couple_with_zero_gain_is_exactly_ablate():
    rng = np.random.default_rng(7)
    theta = rng.normal(size=16)
    h = rng.normal(size=(4, 16))
    coupled = ri.apply_intervention(h, theta, mode="couple", alpha=0.0, sigma=3.0)
    ablated = ri.apply_intervention(h, theta, mode="ablate")
    assert np.allclose(coupled, ablated, atol=1e-12)


def test_couple_sets_theta_coordinate_to_alpha_sigma():
    theta = np.array([0.0, 5.0, 0.0])  # unit = [0,1,0]
    h = np.array([[7.0, -3.0, 2.0]])
    out = ri.apply_intervention(h, theta, mode="couple", alpha=1.5, sigma=2.0)
    # theta coordinate erased then set to alpha*sigma = 3.0; others untouched
    assert np.allclose(out, [[7.0, 3.0, 2.0]])


def test_couple_write_hook_matches_reference():
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
            o = other.arr if isinstance(other, _FakeTensor) else other
            return _FakeTensor(self.arr + o)

        __radd__ = __add__

    spec = ri.build_intervention_spec({"layer": 3, "theta": [0.0, 1.0, 0.0], "sigma": 2.0})
    hook = ri.make_residual_write_hook(
        spec, {"arm_id": "coupled", "mode": "couple", "alpha": -1.25})
    hs = _FakeTensor([[[1.0, 4.0, 1.0], [2.0, -6.0, 0.5]]])
    out = hook(None, (None,), (hs,))
    ref = ri.apply_intervention(hs.arr, np.array(spec["theta"]),
                                mode="couple", alpha=-1.25, sigma=2.0)
    assert np.allclose(out[0].arr, ref)


# --- parse_arms / resolve_couple_alpha -------------------------------------

def _base():
    return {"arm_id": "baseline", "mode": "baseline"}


def test_parse_arms_couple_requires_gain_map():
    with pytest.raises(ri.ResidualInterventionError):
        ri.parse_arms([_base(), {"arm_id": "coupled", "mode": "couple"}])


def test_parse_arms_couple_rejects_bad_gain_key():
    with pytest.raises(ri.ResidualInterventionError):
        ri.parse_arms([_base(), {"arm_id": "coupled", "mode": "couple",
                                 "gain_map": "x.json", "gain_key": "nope"}])


def test_parse_arms_couple_carries_map_and_key():
    arms = ri.parse_arms([
        _base(),
        {"arm_id": "coupled", "mode": "couple", "gain_map": "m.json"},
        {"arm_id": "permuted", "mode": "couple", "gain_map": "m.json",
         "gain_key": "gains_permuted"},
    ])
    assert arms[1]["gain_key"] == "gains"
    assert arms[2]["gain_key"] == "gains_permuted"
    assert arms[1]["gain_map"] == "m.json"


def test_resolve_couple_alpha_reads_gain_and_hard_errors():
    gm = {"gains": {"r1": {"cell": "known_refused", "z": 1.0, "gain": -1.0}}}
    assert ri.resolve_couple_alpha(gm, "gains", "r1") == -1.0
    with pytest.raises(ri.ResidualInterventionError):
        ri.resolve_couple_alpha(gm, "gains", "missing-row")
    with pytest.raises(ri.ResidualInterventionError):
        ri.resolve_couple_alpha(gm, "gains_permuted", "r1")


# --- doubt gain map builder -------------------------------------------------

def _synthetic_cells(n=20, d=8, seed=3):
    """Known cells clustered at +axis, unknown_refused at -axis."""
    rng = np.random.default_rng(seed)
    axis = np.zeros(d)
    axis[0] = 1.0
    h = {
        "known_refused": rng.normal(scale=0.1, size=(n, d)) + 2.0 * axis,
        "known_correct_answered": rng.normal(scale=0.1, size=(n, d)) + 2.5 * axis,
        "unknown_refused": rng.normal(scale=0.1, size=(n, d)) - 2.0 * axis,
    }
    keys = {c: [f"{c}:{i}" for i in range(n)] for c in h}
    return h, keys


def test_gain_map_sign_convention():
    h, keys = _synthetic_cells()
    gm = bgm.build_gain_map(h, keys, alpha=1.0, clip=2.0)
    # doubt axis points known-ward: known cells positive z, unknown negative
    assert gm["per_cell_mean_z"]["known_correct_answered"] > 0
    assert gm["per_cell_mean_z"]["known_refused"] > 0
    assert gm["per_cell_mean_z"]["unknown_refused"] < 0
    # g = -alpha*z: known rows get NEGATIVE gain (push toward answering),
    # unknown rows POSITIVE gain (push toward refusing)
    for k in keys["known_correct_answered"]:
        assert gm["gains"][k]["gain"] < 0
    for k in keys["unknown_refused"]:
        assert gm["gains"][k]["gain"] > 0
    assert all(abs(v["gain"]) <= 2.0 for v in gm["gains"].values())


def test_gain_map_permutation_seed_stable_and_value_preserving():
    h, keys = _synthetic_cells()
    gm1 = bgm.build_gain_map(h, keys, alpha=1.0, clip=2.0)
    gm2 = bgm.build_gain_map(h, keys, alpha=1.0, clip=2.0)
    assert gm1["gains_permuted"] == gm2["gains_permuted"]
    # permutation shuffles values across rows but preserves the multiset
    real = sorted(v["gain"] for v in gm1["gains"].values())
    perm = sorted(v["gain"] for v in gm1["gains_permuted"].values())
    assert np.allclose(real, perm)
    assert set(gm1["gains_permuted"]) == set(gm1["gains"])
    # and actually differs row-wise (not the identity permutation)
    assert any(gm1["gains"][k]["gain"] != gm1["gains_permuted"][k]["gain"]
               for k in gm1["gains"])


def test_gain_map_validation_errors():
    h, keys = _synthetic_cells()
    h_missing = {c: v for c, v in h.items() if c != "unknown_refused"}
    with pytest.raises(ValueError):
        bgm.build_gain_map(h_missing, keys, alpha=1.0, clip=2.0)
    keys_short = dict(keys)
    keys_short["known_refused"] = keys["known_refused"][:-1]
    with pytest.raises(ValueError):
        bgm.build_gain_map(h, keys_short, alpha=1.0, clip=2.0)
    keys_dup = dict(keys)
    keys_dup["known_refused"] = list(keys["known_refused"])
    keys_dup["known_refused"][0] = keys["unknown_refused"][0]
    with pytest.raises(ValueError):
        bgm.build_gain_map(h, keys_dup, alpha=1.0, clip=2.0)


def test_compute_gains_clip():
    g = bgm.compute_gains(np.array([-5.0, 0.0, 5.0]), alpha=1.0, clip=2.0)
    assert np.allclose(g, [2.0, 0.0, -2.0])


# --- analyze_arms groups param ----------------------------------------------

def _arm_rows(arm_id, cell, n, refused_rate, correct_rate=0.0):
    rows = []
    n_ref = int(round(refused_rate * n))
    for i in range(n):
        refused = i < n_ref
        rows.append({"arm_id": arm_id, "behavior_cell": cell,
                     "probe_pool_row_key": f"{cell}:{i}",
                     "refused": refused,
                     "correct": (not refused) and (i < int(correct_rate * n))})
    return rows


def test_analyze_arms_accepts_extra_group():
    rows = []
    for arm, kr, ka, ur in (("baseline", 1.0, 0.0, 1.0), ("ablate", 0.5, 0.0, 0.5)):
        rows += _arm_rows(arm, ri.KNOWN_REFUSED, 40, kr)
        rows += _arm_rows(arm, ri.KNOWN_ANSWERED, 40, ka)
        rows += _arm_rows(arm, ri.UNKNOWN_REFUSED, 40, ur)
    out = ri.analyze_arms(rows, groups=(ri.KNOWN_REFUSED, ri.KNOWN_ANSWERED,
                                        ri.UNKNOWN_REFUSED))
    assert ri.UNKNOWN_REFUSED in out["by_arm"]["ablate"]
    assert out["by_arm"]["ablate"][ri.UNKNOWN_REFUSED]["refusal_rate"] == 0.5


# --- runner load_rows max_rows_per_cell --------------------------------------

def test_load_rows_max_rows_per_cell(tmp_path):
    import json
    p = tmp_path / "rows.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for cell, n in (("known_refused", 10), ("unknown_refused", 4)):
            for i in range(n):
                fh.write(json.dumps({"behavior_cell": cell, "label": "x",
                                     "probe_pool_row_key": f"{cell}:{i}"}) + "\n")
    rows = runner.load_rows(p, max_rows=None, labels=None,
                            cells={"known_refused", "unknown_refused"},
                            max_rows_per_cell=5)
    by_cell = {}
    for r in rows:
        by_cell[r["behavior_cell"]] = by_cell.get(r["behavior_cell"], 0) + 1
    assert by_cell == {"known_refused": 5, "unknown_refused": 4}
    # deterministic: first-N in file order
    assert rows[0]["probe_pool_row_key"] == "known_refused:0"


# --- AC analysis (selectivity gap + gates) -----------------------------------

def _ac_rows(*, coupled_kr, coupled_ur, permuted_kr, permuted_ur, n=100):
    rows = []
    rows += _arm_rows("baseline", "known_refused", n, 1.0)
    rows += _arm_rows("baseline", "unknown_refused", n, 1.0)
    rows += _arm_rows("baseline", "known_correct_answered", n, 0.0, correct_rate=0.9)
    rows += _arm_rows("coupled", "known_refused", n, coupled_kr, correct_rate=0.3)
    rows += _arm_rows("coupled", "unknown_refused", n, coupled_ur)
    rows += _arm_rows("coupled", "known_correct_answered", n, 0.0, correct_rate=0.9)
    rows += _arm_rows("permuted", "known_refused", n, permuted_kr, correct_rate=0.2)
    rows += _arm_rows("permuted", "unknown_refused", n, permuted_ur)
    rows += _arm_rows("permuted", "known_correct_answered", n, 0.0, correct_rate=0.9)
    rows += _arm_rows("ablate", "known_refused", n, 0.5, correct_rate=0.3)
    rows += _arm_rows("ablate", "unknown_refused", n, 0.5)
    rows += _arm_rows("ablate", "known_correct_answered", n, 0.0, correct_rate=0.9)
    return rows


def test_ac_analysis_pass_case():
    # coupled de-refuses selectively (kr 0.6, ur 0.1 -> gap 0.5);
    # permuted de-refuses indiscriminately (gap 0.0)
    rows = _ac_rows(coupled_kr=0.4, coupled_ur=0.9, permuted_kr=0.7, permuted_ur=0.7)
    out = aca.analyze(rows, n_boot=500)
    assert out["selectivity_gaps"]["coupled"] == pytest.approx(0.5)
    assert out["selectivity_gaps"]["permuted"] == pytest.approx(0.0)
    assert out["ac_g1"]["point"] == pytest.approx(0.5)
    assert out["ac_g1"]["pass"] is True
    assert out["specificity_guard"]["pass"] is True
    assert out["verdict"].startswith("AC-G1 PASS")
    assert out["ac_g2"] is not None  # estimate present, no pass/fail key


def test_ac_analysis_falsifier_case():
    # permuted matches coupled -> the doubt wire carries nothing
    rows = _ac_rows(coupled_kr=0.6, coupled_ur=0.6, permuted_kr=0.6, permuted_ur=0.6)
    out = aca.analyze(rows, n_boot=500)
    assert out["ac_g1"]["point"] == pytest.approx(0.0)
    assert out["ac_g1"]["pass"] is False
    assert out["verdict"].startswith("FALSIFIER-FIRED")


def test_ac_analysis_requires_core_arms_and_cells():
    rows = _ac_rows(coupled_kr=0.4, coupled_ur=0.9, permuted_kr=0.7, permuted_ur=0.7)
    with pytest.raises(ValueError):
        aca.analyze([r for r in rows if r["arm_id"] != "permuted"], n_boot=10)
    with pytest.raises(ValueError):
        aca.analyze([r for r in rows if r["behavior_cell"] != "unknown_refused"],
                    n_boot=10)
