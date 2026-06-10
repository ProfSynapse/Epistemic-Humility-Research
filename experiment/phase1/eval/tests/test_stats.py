#!/usr/bin/env python3
"""Unit tests for stats.py: bootstrap determinism, paired pairing, McNemar."""

from __future__ import annotations

import pytest

import stats


def test_bootstrap_is_deterministic_for_seed():
    outcomes = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    a = stats.bootstrap_ci(outcomes, n_resamples=500, seed=7)
    b = stats.bootstrap_ci(outcomes, n_resamples=500, seed=7)
    assert (a.point, a.lo, a.hi) == (b.point, b.lo, b.hi)


def test_bootstrap_seed_is_recorded():
    """The CI records the seed it used so a run is reproducible from its output.
    (Different seeds may yield identical percentile bounds on small discrete
    vectors because percentiles snap to the same discrete values, so we assert
    the seed is faithfully recorded rather than that bounds always differ.)
    """
    outcomes = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1]
    a = stats.bootstrap_ci(outcomes, n_resamples=500, seed=7)
    b = stats.bootstrap_ci(outcomes, n_resamples=500, seed=8)
    assert a.seed == 7 and b.seed == 8
    assert a.point == b.point  # point statistic is seed-independent (the mean)


def test_bootstrap_point_is_mean():
    out = stats.bootstrap_ci([1, 1, 0, 0], n_resamples=100, seed=1)
    assert out.point == pytest.approx(0.5)
    assert out.lo <= out.point <= out.hi


def test_bootstrap_empty():
    out = stats.bootstrap_ci([], n_resamples=100, seed=1)
    assert (out.point, out.lo, out.hi) == (0.0, 0.0, 0.0)


def test_paired_diff_requires_alignment():
    with pytest.raises(ValueError):
        stats.paired_bootstrap_diff_ci([1, 0, 1], [1, 0])


def test_paired_diff_point_is_mean_difference():
    a = [1, 1, 1, 0]
    b = [0, 1, 0, 0]
    res = stats.paired_bootstrap_diff_ci(a, b, n_resamples=200, seed=3)
    # mean(a)-mean(b) = 0.75 - 0.25 = 0.5
    assert res.point == pytest.approx(0.5)


def test_mcnemar_counts_discordant_pairs():
    # a beats b on 2 questions, b beats a on 0 -> b=2, c=0
    arm_a = [1, 1, 1, 0]
    arm_b = [0, 0, 1, 0]
    res = stats.mcnemar(arm_a, arm_b)
    assert res.b == 2
    assert res.c == 0
    assert res.n_discordant == 2


def test_mcnemar_no_discordant_is_p1():
    res = stats.mcnemar([1, 0, 1], [1, 0, 1])
    assert res.p_value == 1.0
    assert res.n_discordant == 0


def test_mcnemar_alignment_required():
    with pytest.raises(ValueError):
        stats.mcnemar([1, 0], [1, 0, 1])


def test_mcnemar_symmetric_split_high_p():
    # equal discordance both directions -> not significant
    arm_a = [1] * 10 + [0] * 10
    arm_b = [0] * 10 + [1] * 10
    res = stats.mcnemar(arm_a, arm_b)
    assert res.b == 10 and res.c == 10
    assert res.p_value > 0.5
