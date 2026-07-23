#!/usr/bin/env python3
"""CPU tests for Amendment AK Stage 2 (commitment-window steering).

Covers the AK-specific logic (the steering engine itself is already regression-
tested in steering/tests/test_steering_common.py):

  * matched_set_indices: within-flavor caliper match reproduces the arm-B design
  * build_commitment_perp: d_perp is orthogonal to the caution axis (B1 convention)
    and sigma is the projected std
  * caution_axis_raw: raw-space normal = w / scale
  * anchor-only == the certified controller 'anchor' mode (item-11 residual
    resolution): anchor mode steers exactly the prefill's last token and NOTHING
    during decode -- the AK "anchor-only" position condition
  * AK-G3 scoring: the window/anchor ratio, the 2x floor + CI, the guards, and
    the falsifier wording on a MISS
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

AMENDMENTS_DIR = Path(__file__).resolve().parents[1]
if str(AMENDMENTS_DIR) not in sys.path:
    sys.path.insert(0, str(AMENDMENTS_DIR))

from path_compat import phase1_eval_dir, phase1_probe_dir, repo_root  # noqa: E402

PROBE_DIR = phase1_probe_dir()
EVAL_DIR = phase1_eval_dir()
STEER_DIR = repo_root() / "archive/experiment/phase1/probe/steering"
for p in (str(AMENDMENTS_DIR), str(PROBE_DIR), str(EVAL_DIR), str(STEER_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

import amendment_ak_stage2_steer as st  # noqa: E402
import amendment_ak_stage2_score as sc  # noqa: E402


# ---------------------------------------------------------------------------
# matched_set_indices
# ---------------------------------------------------------------------------

def _pool_row(rk, confab, z, flavor="ambiguous"):
    return {"row_key": rk, "question": "q", "confab_on_unanswerable": confab,
            "caution_dist_z": z, "category_canon": flavor}


class TestMatchedSet:
    def test_pairs_confab_to_nearest_refuse_within_caliper(self):
        pool = [
            _pool_row("c1", True, 0.10),
            _pool_row("r1", False, 0.12),   # within caliper of c1
            _pool_row("r2", False, 5.00),   # far -> unmatched
        ]
        idx = st.matched_set_indices(pool, caliper=0.20)
        keys = {pool[i]["row_key"] for i in idx}
        assert keys == {"c1", "r1"}

    def test_no_cross_flavor_match(self):
        pool = [
            _pool_row("c1", True, 0.10, "ambiguous"),
            _pool_row("r1", False, 0.10, "controversial"),  # same z, other flavor
        ]
        idx = st.matched_set_indices(pool, caliper=0.20)
        assert idx == []

    def test_deterministic_under_seed(self):
        pool = [_pool_row(f"c{i}", True, 0.1 * i) for i in range(5)] + \
               [_pool_row(f"r{i}", False, 0.1 * i + 0.05) for i in range(5)]
        a = st.matched_set_indices(pool, caliper=0.2, seed=7)
        b = st.matched_set_indices(pool, caliper=0.2, seed=7)
        assert a == b

    def test_refuse_not_reused(self):
        # two confabs, one nearby refuse -> only one pair (no replacement)
        pool = [
            _pool_row("c1", True, 0.10),
            _pool_row("c2", True, 0.11),
            _pool_row("r1", False, 0.105),
        ]
        idx = st.matched_set_indices(pool, caliper=0.20)
        kept = [pool[i]["row_key"] for i in idx]
        assert kept.count("r1") == 1
        assert len([k for k in kept if k.startswith("c")]) == 1


# ---------------------------------------------------------------------------
# build_commitment_perp orthogonality (B1 convention) via a fake stage1 dir
# ---------------------------------------------------------------------------

class _FakeTrunk:
    """Stand-in DoubtTrunk with known w/scale so caution_axis_raw is exact."""
    def __init__(self, w, scale):
        self._w = np.asarray(w, dtype=np.float64)
        self._scale = np.asarray(scale, dtype=np.float64)


def test_caution_axis_raw_is_w_over_scale(monkeypatch):
    w = np.array([2.0, 0.0, 0.0, 0.0])
    scale = np.array([2.0, 1.0, 1.0, 1.0])
    monkeypatch.setattr(st.ak.DoubtTrunk, "load",
                        classmethod(lambda cls, d, layer: _FakeTrunk(w, scale)))
    axis = st.caution_axis_raw(Path("/nonexistent"), "L24")
    # w/scale = [1,0,0,0] -> unit = e0
    assert np.allclose(axis, np.array([1.0, 0.0, 0.0, 0.0]))


def test_build_commitment_perp_orthogonal_to_caution(tmp_path, monkeypatch):
    from safetensors.numpy import save_file
    hidden = 4
    layer = "L24"
    # caution axis along e0
    caution_u = np.array([1.0, 0.0, 0.0, 0.0])
    # confab mean and refuse mean differ along e0 (caution) AND e1 (commitment).
    # d = mc - mr = [big along e0, some along e1]; d_perp must kill the e0 part.
    pool, matched = [], []
    def _write(rk, vec):
        sk = f"safe_{rk}"
        save_file({f"{layer}@anchor": np.asarray(vec, dtype=np.float32)},
                  str(tmp_path / f"{sk}.safetensors"))
    monkeypatch.setattr(st, "safe_key_for", lambda rk: f"safe_{rk}")
    # confab rows centered at [3, 1, 0, 0]; refuse at [0, 0, 0, 0]
    for i in range(6):
        rk = f"c{i}"
        pool.append(_pool_row(rk, True, 0.1))
        _write(rk, [3.0, 1.0, 0.0, 0.0])
    for i in range(6):
        rk = f"r{i}"
        pool.append(_pool_row(rk, False, 0.1))
        _write(rk, [0.0, 0.0, 0.0, 0.0])
    matched = list(range(len(pool)))
    info = st.build_commitment_perp(tmp_path, pool, matched, layer, caution_u)
    theta = np.asarray(info["theta"])
    # theta_u must be orthogonal to the caution axis
    assert abs(float(theta @ caution_u)) < 1e-9
    # d had a large e0 component; perp_fraction < 1 (some removed)
    assert 0.0 < info["perp_fraction_of_commitment"] < 1.0
    # theta points along e1 (the only surviving commitment component)
    assert abs(abs(theta[1]) - 1.0) < 1e-9
    assert info["sigma"] >= 0.0


# ---------------------------------------------------------------------------
# anchor-only == certified controller 'anchor' mode (item-11 residual resolution)
# ---------------------------------------------------------------------------

torch = pytest.importorskip("torch",
                            reason="torch required for the controller assertion")


def test_anchor_only_uses_certified_controller_anchor_mode():
    """The AK 'anchor-only' position condition IS GenerationHookController's
    'anchor' mode: steer exactly the prefill's last token, nothing at decode.
    This documents that item-11's flagged residual (anchor-only during the
    generate path) needs no new engine code."""
    from confidence_steer import SteeringHook
    from steering_common import GenerationHookController
    hd = 8
    d = torch.zeros(hd)
    d[0] = 1.0
    controller = GenerationHookController(SteeringHook(d=d, alpha=0.0,
                                                       position="anchor"))
    alpha = 2.5
    controller.begin_pass("anchor", alpha)
    # prefill (seq_len > 1): only the last token moves, by exactly alpha along d
    x = torch.zeros(1, 6, hd)
    out = controller(None, None, (x.clone(),))[0]
    assert out[0, -1, 0].item() == pytest.approx(alpha)
    assert out[0, :-1, :].abs().max().item() == 0.0
    # decode step (seq_len == 1): NOT steered in anchor mode
    x1 = torch.zeros(1, 1, hd)
    out1 = controller(None, None, (x1.clone(),))[0]
    assert out1.abs().max().item() == 0.0


def test_gen_stream_is_the_answer_window_condition():
    """The AK 'answer-window' condition IS 'gen_stream': skip prefill, steer
    every decode step."""
    from confidence_steer import SteeringHook
    from steering_common import GenerationHookController
    hd = 8
    d = torch.zeros(hd)
    d[0] = 1.0
    controller = GenerationHookController(SteeringHook(d=d, alpha=0.0,
                                                       position="anchor"))
    alpha = 1.5
    controller.begin_pass("gen_stream", alpha)
    x = torch.zeros(1, 6, hd)
    assert controller(None, None, (x.clone(),))[0].abs().max().item() == 0.0
    for _ in range(3):
        x1 = torch.zeros(1, 1, hd)
        out1 = controller(None, None, (x1.clone(),))[0]
        assert out1[0, 0, 0].item() == pytest.approx(alpha)


# ---------------------------------------------------------------------------
# AK-G3 scoring
# ---------------------------------------------------------------------------

def _rows_for(confab_by_arm: dict[tuple[str, float], list[int]],
              n_rows: int, gen_len: int = 20, degen: int = 0):
    """Build stage2 rows.jsonl records: confab_by_arm maps (position, alpha) to
    a length-n_rows list of confab 0/1. All arms share the same row_keys."""
    rows = []
    for (position, alpha), confabs in confab_by_arm.items():
        assert len(confabs) == n_rows
        for i, c in enumerate(confabs):
            rows.append({
                "row_key": f"row{i}", "safe_key": f"s{i}",
                "confab_baseline": True, "caution_dist_z": 0.1,
                "category_canon": "ambiguous",
                "position": position, "alpha": alpha,
                "alpha_sigma": alpha * 1.0, "arm_id": f"{position}@a{alpha:+g}",
                "refused": (c == 0), "answered": bool(c), "confab": int(c),
                "degenerate": degen, "n_generated": gen_len, "prompt_len": 10,
                "config_sha": "deadbeef",
            })
    return rows


class TestG3Scoring:
    def test_window_2x_anchor_passes(self):
        # A clean pass: a small, tight anchor shift and a large window shift so
        # the row-paired bootstrap ratio CI clears 2.0 (n=120).
        n = 120
        base = [0] * n
        # anchor shifts +~8% (10/120), window shifts +~75% (90/120)
        anchor = [1] * 10 + [0] * (n - 10)
        window = [1] * 90 + [0] * (n - 90)
        rows = _rows_for({
            ("anchor", 0.0): base, ("gen_stream", 0.0): base,
            ("anchor", 1.0): anchor, ("gen_stream", 1.0): window,
        }, n_rows=n)
        rep = sc.score(rows)
        assert rep["guards"]["schema_ok"]
        assert rep["guards"]["coherence_ok"]
        assert rep["AK_G3"]["pass"] is True
        assert rep["AK_G3"]["passing_ratio"] >= 2.0
        assert rep["AK_G3"]["passing_ratio_ci95"][0] >= 2.0

    def test_flat_asymmetry_misses_and_fires_falsifier(self):
        n = 40
        base = [0] * n
        # anchor and window move the SAME amount -> ratio ~1, MISS
        same = [1] * 20 + [0] * 20
        rows = _rows_for({
            ("anchor", 0.0): base, ("gen_stream", 0.0): base,
            ("anchor", 1.0): same, ("gen_stream", 1.0): same,
        }, n_rows=n)
        rep = sc.score(rows)
        assert rep["AK_G3"]["pass"] is False
        assert "falsifier" in rep["AK_G3"]["verdict"].lower()

    def test_degenerate_floor_blocks_pass(self):
        n = 40
        base = [0] * n
        anchor = [1] * 10 + [0] * 30
        window = [1] * 30 + [0] * 10
        rows = _rows_for({
            ("anchor", 0.0): base, ("gen_stream", 0.0): base,
            ("anchor", 1.0): anchor, ("gen_stream", 1.0): window,
        }, n_rows=n, degen=1)  # 100% degenerate -> coherence floor breached
        rep = sc.score(rows)
        assert rep["guards"]["coherence_ok"] is False
        assert rep["AK_G3"]["pass"] is False

    def test_schema_guard_detects_missing_arm_rows(self):
        n = 40
        base = [0] * n
        anchor = [1] * 10 + [0] * 30
        window = [1] * 30 + [0] * 10
        rows = _rows_for({
            ("anchor", 0.0): base, ("gen_stream", 0.0): base,
            ("anchor", 1.0): anchor, ("gen_stream", 1.0): window,
        }, n_rows=n)
        rows = [r for r in rows if not (r["position"] == "anchor"
                                        and r["alpha"] == 1.0
                                        and r["row_key"] == "row0")]
        rep = sc.score(rows)
        assert rep["guards"]["schema_ok"] is False

    def test_no_window_shift_is_not_a_pass(self):
        n = 40
        base = [0] * n
        anchor = [1] * 10 + [0] * 30   # anchor moves
        window = [0] * n               # window flat
        rows = _rows_for({
            ("anchor", 0.0): base, ("gen_stream", 0.0): base,
            ("anchor", 1.0): anchor, ("gen_stream", 1.0): window,
        }, n_rows=n)
        rep = sc.score(rows)
        assert rep["AK_G3"]["pass"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
