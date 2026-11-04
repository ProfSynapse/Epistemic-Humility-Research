"""Frozen R1 paired bootstrap; excludes unused SciPy/McNemar closure."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Sequence
import numpy as np
DEFAULT_BOOTSTRAP_RESAMPLES=10000
DEFAULT_CI_LEVEL=.95
DEFAULT_SEED=12345

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

