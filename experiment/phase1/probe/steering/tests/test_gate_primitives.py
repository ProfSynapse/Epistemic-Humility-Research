#!/usr/bin/env python3
"""Unit tests for gate_primitives.py (declarative steer-cell gate library).

CPU-only, tiny synthetic fixtures — no model loads, no GPU, no network. Every
sampling primitive is exercised for both its point estimate and its seeded
determinism (same seed => byte-identical result). Runs under pytest OR standalone
(pytest is not installed in every local env):

    python -m pytest test_gate_primitives.py          # if pytest present
    python test_gate_primitives.py                    # plain runner otherwise
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

STEER_DIR = Path(__file__).resolve().parent.parent
if str(STEER_DIR) not in sys.path:
    sys.path.insert(0, str(STEER_DIR))

import gate_primitives as gp  # noqa: E402


class TestCountFlips:
    def _rows(self):
        # 4 rows: 2 baseline-confab flagged, of which 1 killed; 1 confab unflagged
        return [
            {"k": "a", "flagged": True, "base_confab": True, "killed": True},
            {"k": "b", "flagged": True, "base_confab": True, "killed": False},
            {"k": "c", "flagged": False, "base_confab": True, "killed": True},
            {"k": "d", "flagged": True, "base_confab": False, "killed": False},
        ]

    def test_flip_over_full_universe(self):
        rows = self._rows()
        res = gp.count_flips(rows, before=lambda r: r["base_confab"],
                             after=lambda r: r["killed"])
        assert res["before"] == 3
        assert res["flips"] == 2  # a and c
        assert abs(res["rate"] - 2 / 3) < 1e-9

    def test_universe_restriction_to_flagged(self):
        rows = self._rows()
        res = gp.count_flips(rows, before=lambda r: r["base_confab"],
                             after=lambda r: r["killed"],
                             universe=lambda r: r["flagged"])
        assert res["universe"] == 3  # a, b, d flagged
        assert res["before"] == 2   # a, b flagged confabs
        assert res["flips"] == 1    # only a killed
        assert abs(res["rate"] - 0.5) < 1e-9

    def test_empty_before_population_zero_rate(self):
        res = gp.count_flips([{"x": 1}], before=lambda r: False,
                             after=lambda r: True)
        assert res["before"] == 0
        assert res["rate"] == 0.0


class TestKillDiffVsControl:
    def test_point_diff_and_ci_excludes_zero(self):
        # treatment kills 8 of 10; control kills 1 of 10 -> strong positive diff
        t = [1] * 8 + [0] * 2
        c = [1] + [0] * 9
        res = gp.kill_diff_vs_control(t, c, seed=7, n_boot=500)
        assert res["diff"] == 7
        assert res["treatment_count"] == 8
        assert res["control_count"] == 1
        assert res["ci_excludes_zero"] is True

    def test_null_diff_ci_includes_zero(self):
        # identical arms -> zero diff, CI should straddle zero
        ind = [1, 0, 1, 0, 1, 0]
        res = gp.kill_diff_vs_control(ind, ind, seed=3, n_boot=500)
        assert res["diff"] == 0
        assert res["ci_excludes_zero"] is False

    def test_seeded_determinism(self):
        t = [1, 1, 0, 1, 0, 0, 1]
        c = [0, 1, 0, 0, 0, 0, 1]
        r1 = gp.kill_diff_vs_control(t, c, seed=42, n_boot=300)
        r2 = gp.kill_diff_vs_control(t, c, seed=42, n_boot=300)
        assert r1 == r2

    def test_length_mismatch_raises(self):
        try:
            gp.kill_diff_vs_control([1, 0], [1], seed=1)
        except ValueError:
            return
        raise AssertionError("expected ValueError on length mismatch")


class TestPermutationP:
    def test_clear_separation_low_p(self):
        # 4 vs 4 fully separated: only 1 of C(8,4)=70 label assignments is as
        # extreme, so the true one-tailed p is well under 0.05.
        values = [10.0, 11.0, 12.0, 13.0, 0.0, 1.0, 2.0, 3.0]
        labels = [1, 1, 1, 1, 0, 0, 0, 0]
        res = gp.permutation_p(values, labels, seed=5, n_perm=5000)
        assert res["observed"] > 0
        assert res["p_value"] < 0.05

    def test_no_separation_high_p(self):
        values = [1.0, 2.0, 3.0, 1.0, 2.0, 3.0]
        labels = [1, 0, 1, 0, 1, 0]
        res = gp.permutation_p(values, labels, seed=5, n_perm=2000)
        assert res["p_value"] > 0.05

    def test_seeded_determinism(self):
        values = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0]
        labels = [1, 0, 1, 0, 1, 0]
        r1 = gp.permutation_p(values, labels, seed=11, n_perm=1000)
        r2 = gp.permutation_p(values, labels, seed=11, n_perm=1000)
        assert r1 == r2

    def test_empty_group_raises(self):
        try:
            gp.permutation_p([1.0, 2.0], [1, 1], seed=1)
        except ValueError:
            return
        raise AssertionError("expected ValueError when a group is empty")

    def test_add_one_correction_never_zero(self):
        values = [100.0, 99.0, 0.0, 1.0]
        labels = [1, 1, 0, 0]
        res = gp.permutation_p(values, labels, seed=1, n_perm=50)
        assert res["p_value"] >= 1.0 / (50 + 1)


class TestAurocFloor:
    def test_perfect_separation_auroc_one(self):
        scores = [0.1, 0.2, 0.3, 0.8, 0.9, 1.0]
        labels = [0, 0, 0, 1, 1, 1]
        res = gp.auroc_floor(scores, labels, floor=0.7, seed=9, n_boot=300)
        assert abs(res["auroc"] - 1.0) < 1e-9
        assert res["pass"] is True

    def test_random_auroc_near_half_fails_floor(self):
        scores = [0.5, 0.4, 0.6, 0.5, 0.45, 0.55, 0.5, 0.5]
        labels = [1, 0, 1, 0, 1, 0, 1, 0]
        res = gp.auroc_floor(scores, labels, floor=0.8, seed=9, n_boot=300)
        assert res["pass"] is False

    def test_ties_handled_auroc_half(self):
        # all identical scores -> AUROC exactly 0.5 (Mann-Whitney with full ties)
        scores = [0.5, 0.5, 0.5, 0.5]
        labels = [1, 1, 0, 0]
        res = gp.auroc_floor(scores, labels, floor=0.4, seed=1, n_boot=100)
        assert abs(res["auroc"] - 0.5) < 1e-9

    def test_hanley_mcneil_se_present(self):
        scores = [0.1, 0.3, 0.2, 0.7, 0.8, 0.9]
        labels = [0, 0, 0, 1, 1, 1]
        res = gp.auroc_floor(scores, labels, floor=0.5, seed=2, n_boot=100)
        assert res["hanley_mcneil_se"] is not None

    def test_seeded_determinism(self):
        scores = [0.2, 0.8, 0.3, 0.7, 0.4, 0.6]
        labels = [0, 1, 0, 1, 0, 1]
        r1 = gp.auroc_floor(scores, labels, floor=0.5, seed=13, n_boot=200)
        r2 = gp.auroc_floor(scores, labels, floor=0.5, seed=13, n_boot=200)
        assert r1 == r2


class TestThresholdHelpers:
    def test_at_most(self):
        assert gp.at_most(2, 2)["pass"] is True
        assert gp.at_most(3, 2)["pass"] is False

    def test_at_least(self):
        assert gp.at_least(5, 5)["pass"] is True
        assert gp.at_least(4, 5)["pass"] is False

    def test_within(self):
        assert gp.within(0.0, -1.0, 1.0)["pass"] is True
        assert gp.within(2.0, -1.0, 1.0)["pass"] is False


def _run_without_pytest() -> int:
    """Plain runner (pytest is not installed in every local env)."""
    classes = [TestCountFlips, TestKillDiffVsControl, TestPermutationP,
               TestAurocFloor, TestThresholdHelpers]
    failures = 0
    total = 0
    for cls in classes:
        inst = cls()
        for name in dir(inst):
            if not name.startswith("test_"):
                continue
            total += 1
            try:
                getattr(inst, name)()
                print(f"PASS {cls.__name__}.{name}")
            except Exception:  # noqa: BLE001
                failures += 1
                print(f"FAIL {cls.__name__}.{name}")
                traceback.print_exc()
    print(f"\n{total - failures}/{total} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_run_without_pytest())
