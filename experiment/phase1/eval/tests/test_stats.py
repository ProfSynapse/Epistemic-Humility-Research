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


def test_bootstrap_ci_width_matches_analytic_se():
    """MT2: the percentile CI half-width tracks the analytic Bernoulli SE.

    The determinism/point/empty tests above never pin the percentile bounds, so
    a broken percentile computation would pass them. For a large-n Bernoulli
    sample the 95% percentile bootstrap half-width should approximate the
    analytic 1.96 * sqrt(p(1-p)/n). With n=2000, p=0.3 that is ~0.0201; the
    observed bootstrap half-width is ~0.0203. Tolerance is loose enough to
    absorb resampling noise across numpy versions but tight enough that a wrong
    percentile (e.g. returning min/max, or the wrong alpha) fails.
    """
    import math

    import numpy as np

    rng = np.random.default_rng(0)
    data = rng.binomial(1, 0.3, size=2000).tolist()
    out = stats.bootstrap_ci(data, n_resamples=2000, seed=42)
    analytic_half_width = 1.96 * math.sqrt(0.3 * 0.7 / 2000)
    observed_half_width = (out.hi - out.lo) / 2.0
    assert out.point == pytest.approx(0.3, abs=0.02)
    assert observed_half_width == pytest.approx(analytic_half_width, abs=0.005)


def test_bootstrap_ci_degenerate_all_ones():
    """A constant vector has zero variance: every resample is all ones, so the
    point and both percentile bounds collapse to exactly 1.0 (a no-spread CI)."""
    out = stats.bootstrap_ci([1.0] * 50, n_resamples=200, seed=1)
    assert (out.point, out.lo, out.hi) == (1.0, 1.0, 1.0)


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


# ---------------------------------------------------------------------------
# McNemar known-value pins (MT1). The discordant-count and p>0.5 tests above
# exercise the counting and the no-discordant branch but leave the continuity-
# correction FORMULA (abs(b-c)-1)**2/(b+c) unpinned: a review mutation probe
# showed that dropping the correction, flipping its sign (-1 -> +1), or routing
# the CC path through the no-CC formula all survive those tests. These pins kill
# those mutations by fixing each branch to its analytically-known value. Inputs
# below give b=10, c=0 (ten questions where arm_a is correct and arm_b is not,
# plus one concordant-correct and one concordant-wrong question).
# ---------------------------------------------------------------------------

_B10_C0_ARM_A = [1] * 10 + [1, 0]
_B10_C0_ARM_B = [0] * 10 + [1, 0]


def test_mcnemar_continuity_corrected_known_value():
    # b=10, c=0, with Edwards continuity correction:
    #   statistic = (|10-0| - 1)**2 / (10+0) = 81/10 = 8.1
    #   p = chi2.sf(8.1, df=1) = 0.00442653...
    res = stats.mcnemar(_B10_C0_ARM_A, _B10_C0_ARM_B, continuity_correction=True)
    assert res.b == 10 and res.c == 0
    assert res.statistic == pytest.approx(8.1, abs=1e-6)
    assert res.p_value == pytest.approx(0.00442653, abs=1e-7)


def test_mcnemar_uncorrected_known_value():
    # Same b=10, c=0, WITHOUT the correction:
    #   statistic = (10-0)**2 / (10+0) = 100/10 = 10.0
    #   p = chi2.sf(10.0, df=1) = 0.00156540...
    res = stats.mcnemar(_B10_C0_ARM_A, _B10_C0_ARM_B, continuity_correction=False)
    assert res.statistic == pytest.approx(10.0, abs=1e-6)
    assert res.p_value == pytest.approx(0.00156540, abs=1e-7)


def test_mcnemar_correction_changes_the_statistic():
    # Belt-and-suspenders against a drop-CC mutation that routes the corrected
    # path through the uncorrected formula: the two branches MUST differ on the
    # same inputs (8.1 != 10.0), so a "correction" that no-ops is caught even if
    # one of the two known-value pins above were ever relaxed.
    cc = stats.mcnemar(_B10_C0_ARM_A, _B10_C0_ARM_B, continuity_correction=True)
    no_cc = stats.mcnemar(_B10_C0_ARM_A, _B10_C0_ARM_B, continuity_correction=False)
    assert cc.statistic < no_cc.statistic
    assert cc.statistic != no_cc.statistic
