"""Wilson and paired-bootstrap confidence intervals for
wide-instrument-control-rescore.

Ported verbatim (logic, not import; this repo's convention of each experiment
directory owning its own copy) from
`experiments/idk-switch-naming-confirmatory/stats_lib.py`
(`wilson`/`rate_wilson`/`bootstrap_paired_diff_ci`, read in full before
writing this), itself descending from the program's canonical Wilson-interval
lineage (`rr2-mistral-adjudicated-refusal-confirm/gates_lib.py:wilson`). No
formula is re-derived here.
"""

from __future__ import annotations

import random
from typing import Any, Sequence

_Z95 = 1.959963984540054


def wilson(successes: int, n: int, z: float = _Z95) -> dict[str, Any]:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n,
        "successes": successes,
        "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }


def rate_wilson(flags: Sequence[bool]) -> dict[str, Any]:
    return wilson(sum(1 for f in flags if f), len(flags))


def bootstrap_paired_diff_ci(
    flags_a: Sequence[bool], flags_b: Sequence[bool],
    n_resamples: int = 10000, seed: int = 0, ci: float = 0.95,
) -> dict[str, Any]:
    """Paired bootstrap CI on rate(flags_b) - rate(flags_a), resampling ROW
    INDICES with replacement. `flags_a`/`flags_b` must be the same length and
    index-aligned by caller (same row order across the two compared arms).
    Returns the point estimate and a percentile CI; does not itself decide
    whether the interval "excludes zero" -- that is a registered gate this
    module does not set."""
    n = len(flags_a)
    if n == 0 or len(flags_b) != n:
        raise ValueError(f"flags_a and flags_b must be the same nonzero length, got {len(flags_a)} and {len(flags_b)}")
    a = [1 if f else 0 for f in flags_a]
    b = [1 if f else 0 for f in flags_b]
    point = (sum(b) / n) - (sum(a) / n)

    rng = random.Random(seed)
    diffs: list[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        ra = sum(a[i] for i in idx) / n
        rb = sum(b[i] for i in idx) / n
        diffs.append(rb - ra)
    diffs.sort()
    lo_p = (1 - ci) / 2
    hi_p = 1 - lo_p
    lo = diffs[max(0, int(lo_p * n_resamples))]
    hi = diffs[min(n_resamples - 1, int(hi_p * n_resamples) - 1)]

    return {
        "n": n, "point_diff": point,
        "ci": ci, "n_resamples": n_resamples, "seed": seed,
        "bootstrap_ci": [lo, hi],
    }


def bootstrap_paired_diff_ci_from_draws(
    draws_a: Sequence[float], draws_b: Sequence[float],
) -> dict[str, Any]:
    """Elementwise-sums two ALREADY-COMPUTED same-length bootstrap draw
    sequences (e.g. from two independent `bootstrap_paired_diff_ci` calls
    over disjoint populations, same n_resamples/seed count) into a single
    joint percentile CI on the combined statistic. Used for WG-G2's
    selectivity-gap combination of a confab-population draw set and a
    known-population draw set (see score_wide.py for the combination
    definition and its flagged-ambiguity status)."""
    if len(draws_a) != len(draws_b):
        raise ValueError(f"draw sequences must be the same length, got {len(draws_a)} and {len(draws_b)}")
    combined = sorted(x + y for x, y in zip(draws_a, draws_b))
    n_resamples = len(combined)
    ci = 0.95
    lo_p = (1 - ci) / 2
    hi_p = 1 - lo_p
    lo = combined[max(0, int(lo_p * n_resamples))]
    hi = combined[min(n_resamples - 1, int(hi_p * n_resamples) - 1)]
    return {"ci": ci, "n_resamples": n_resamples, "bootstrap_ci": [lo, hi]}
