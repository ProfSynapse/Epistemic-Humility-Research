#!/usr/bin/env python3
"""experiment/phase1/eval/stats.py

Statistical analysis layer (WS-4, architecture doc §6.6). Single responsibility:
turn per-question binary/scalar outcome vectors (from scorers.py) into paired
bootstrap confidence intervals and McNemar comparisons between arms evaluated on
the SAME question set. No model inference, no scoring logic here.

Determinism: every bootstrap takes an explicit integer seed; the same seed +
same inputs reproduce the same CI exactly (numpy default_rng). This is required
by the provenance discipline (raw generations committed, stats re-runnable).

Consumed by: run_eval.py (per-arm CIs, pairwise McNemar -> bootstrap_ci.json,
mcnemar.csv). Tested by: tests/test_stats.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np
from scipy.stats import chi2

DEFAULT_BOOTSTRAP_RESAMPLES = 10_000
DEFAULT_CI_LEVEL = 0.95
DEFAULT_SEED = 12345  # pinned default; configs may override per run


@dataclass
class BootstrapCI:
    """Percentile bootstrap CI for a single metric."""

    point: float
    lo: float
    hi: float
    level: float
    n_resamples: int
    seed: int

    def as_dict(self) -> dict[str, float | int]:
        return {
            "point": round(self.point, 6),
            "ci_lo": round(self.lo, 6),
            "ci_hi": round(self.hi, 6),
            "ci_level": self.level,
            "n_resamples": self.n_resamples,
            "seed": self.seed,
        }


def _mean_statistic(values: np.ndarray) -> float:
    return float(values.mean()) if values.size else 0.0


def bootstrap_ci(
    outcomes: Sequence[float],
    *,
    statistic: Callable[[np.ndarray], float] = _mean_statistic,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    level: float = DEFAULT_CI_LEVEL,
    seed: int = DEFAULT_SEED,
) -> BootstrapCI:
    """Percentile bootstrap CI over a per-question outcome vector.

    Resamples QUESTIONS with replacement (the unit of analysis), recomputes the
    statistic (mean by default = a rate), and takes percentile bounds. For paired
    comparisons, pass the per-question difference vector as `outcomes`.
    """
    arr = np.asarray(outcomes, dtype=float)
    n = arr.size
    if n == 0:
        return BootstrapCI(0.0, 0.0, 0.0, level, n_resamples, seed)
    rng = np.random.default_rng(seed)
    point = statistic(arr)
    boot = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        boot[i] = statistic(arr[idx])
    alpha = (1.0 - level) / 2.0
    lo = float(np.percentile(boot, 100 * alpha))
    hi = float(np.percentile(boot, 100 * (1.0 - alpha)))
    return BootstrapCI(point, lo, hi, level, n_resamples, seed)


def paired_bootstrap_diff_ci(
    arm_a: Sequence[float],
    arm_b: Sequence[float],
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    level: float = DEFAULT_CI_LEVEL,
    seed: int = DEFAULT_SEED,
) -> BootstrapCI:
    """Paired CI on the mean difference (arm_a - arm_b) over the SAME questions.

    arm_a[i] and arm_b[i] MUST be the same question i (paired). Resamples question
    indices once per replicate and applies the SAME index to both arms, preserving
    the pairing (architecture doc §6.6: "Paired = same questions across arms").
    """
    a = np.asarray(arm_a, dtype=float)
    b = np.asarray(arm_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError(
            f"paired arms must align 1:1 on questions: {a.shape} vs {b.shape}"
        )
    diff = a - b
    return bootstrap_ci(
        diff, n_resamples=n_resamples, level=level, seed=seed
    )


@dataclass
class McNemarResult:
    """McNemar test on a paired binary outcome between two arms.

    b = #questions where arm_a correct/refused and arm_b not; c = the reverse.
    """

    b: int
    c: int
    statistic: float
    p_value: float
    n_discordant: int
    continuity_correction: bool

    def as_dict(self) -> dict[str, float | int | bool]:
        return {
            "b_a_not_b": self.b,
            "c_b_not_a": self.c,
            "statistic": round(self.statistic, 6),
            "p_value": round(self.p_value, 8),
            "n_discordant": self.n_discordant,
            "continuity_correction": self.continuity_correction,
        }


def mcnemar(
    arm_a: Sequence[int],
    arm_b: Sequence[int],
    *,
    continuity_correction: bool = True,
) -> McNemarResult:
    """McNemar test between two arms' paired binary outcomes on the same questions.

    arm_a[i], arm_b[i] in {0, 1} for question i (e.g. truthful-or-not). Uses the
    chi-square approximation with Edwards continuity correction by default; for
    small discordant counts (b + c < 25) the caller should prefer an exact test,
    which we flag via n_discordant in the result for downstream judgment.
    """
    a = np.asarray(arm_a, dtype=int)
    b_arr = np.asarray(arm_b, dtype=int)
    if a.shape != b_arr.shape:
        raise ValueError(
            f"paired arms must align 1:1 on questions: {a.shape} vs {b_arr.shape}"
        )
    b = int(np.sum((a == 1) & (b_arr == 0)))
    c = int(np.sum((a == 0) & (b_arr == 1)))
    n_discordant = b + c
    if n_discordant == 0:
        return McNemarResult(b, c, 0.0, 1.0, 0, continuity_correction)
    if continuity_correction:
        statistic = (abs(b - c) - 1) ** 2 / (b + c)
        statistic = max(statistic, 0.0)
    else:
        statistic = (b - c) ** 2 / (b + c)
    p_value = float(chi2.sf(statistic, df=1))
    return McNemarResult(b, c, float(statistic), p_value, n_discordant,
                         continuity_correction)
