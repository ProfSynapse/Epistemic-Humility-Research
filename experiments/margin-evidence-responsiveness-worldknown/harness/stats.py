"""AUROC + bootstrap machinery for margin-evidence-responsiveness-worldknown
(M4-WK). Pure CPU, no model.

`auroc` / `bootstrap_auroc_ci` are ported (logic, byte-identical) from
`susceptibility-as-probe/harness/stats.py` (read in full before writing
this): positive class = role=='confab' (registered score already oriented
confab-positive per cell.yaml `readout`). `bootstrap_paired_diff` is a
generic percentile-bootstrap CI on a paired difference of two same-length
arrays (median shift, specificity difference, or survival-rate difference),
resampling ROW INDICES WITHIN ROLE GROUPS is not always applicable here (D1/
D2 operate on a single row set, confab rows only, for the paired shift), so
this module offers both a plain paired-rows resampler (`bootstrap_paired_diff`,
used for D1 leg1/leg2 and D2) and the role-stratified AUROC resampler
(`bootstrap_auroc_ci`, used for the transfer-firing / native-reproduction
gates), matching gates.yaml `statistics.resampling_unit`: "row indices within
role groups" for AUROC, and "paired bootstrap ... over confab rows" for the
shift/survival differences (a single role group, so the two conventions
coincide there).
"""

from __future__ import annotations

import numpy as np


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney U AUROC, positive class = labels==1, ties split 0.5."""
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    if np.any(np.isnan(scores)):
        raise ValueError("auroc: NaN score present; caller must filter to a pairwise-complete set first")
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    if len(pos) == 0 or len(neg) == 0:
        raise ValueError("auroc: one class is empty")
    count = 0.0
    for p in pos:
        count += float(np.sum(neg < p)) + 0.5 * float(np.sum(neg == p))
    return count / (len(pos) * len(neg))


def _resample_indices_within_groups(rng: np.random.Generator, pos_idx: np.ndarray, neg_idx: np.ndarray) -> np.ndarray:
    draw_pos = pos_idx[rng.integers(0, len(pos_idx), len(pos_idx))]
    draw_neg = neg_idx[rng.integers(0, len(neg_idx), len(neg_idx))]
    return np.concatenate([draw_pos, draw_neg])


def bootstrap_auroc_ci(scores: np.ndarray, labels: np.ndarray, *, n_boot: int = 10000, seed: int = 48260724) -> dict:
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    point = auroc(scores, labels)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = _resample_indices_within_groups(rng, pos_idx, neg_idx)
        boots[i] = auroc(scores[idx], labels[idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": point, "bootstrap_ci_95": [float(lo), float(hi)], "n_boot": n_boot, "seed": seed, "n_pos": len(pos_idx), "n_neg": len(neg_idx)}


def bootstrap_paired_diff(a: np.ndarray, b: np.ndarray, *, n_boot: int = 10000, seed: int = 48260724, statistic: str = "mean") -> dict:
    """Paired bootstrap 95% CI of a summary statistic of (a - b), resampling
    ROW INDICES (the same draw applied to both a and b, preserving pairing).
    `statistic`: "mean" (used for rate differences, e.g. D2 survival) or
    "median" (used for D1 leg1's median shift-of-shift framing is actually a
    median of a single array; this function handles the two-array paired
    case used by D1 leg2 / D2, where the natural point estimate is the mean
    of the per-row differences for a rate, or -- for D1 leg2's specificity
    check on continuous shifts -- the mean paired difference, per gates.yaml
    `D1_projection_collapse.leg_2_specificity`: "paired bootstrap 95% CI of
    (true_answer shift - false_answer shift)", i.e. the CI is on the
    DIFFERENCE array's central tendency)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    if len(a) != len(b):
        raise ValueError(f"bootstrap_paired_diff: length mismatch {len(a)} != {len(b)}")
    n = len(a)
    diff = a - b
    stat_fn = np.mean if statistic == "mean" else np.median
    point = float(stat_fn(diff))
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        boots[i] = float(stat_fn(diff[idx]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    excludes_zero = (lo > 0.0) or (hi < 0.0)
    return {
        "point": point, "bootstrap_ci_95": [float(lo), float(hi)],
        "excludes_zero": bool(excludes_zero), "n": n, "n_boot": n_boot, "seed": seed, "statistic": statistic,
    }


def bootstrap_median_ci(values: np.ndarray, *, n_boot: int = 10000, seed: int = 48260724) -> dict:
    """Percentile bootstrap 95% CI on the median of a single array of
    per-row values (D1 leg1's "median over confab rows of
    (no_answer_baseline_z - true_answer_z)")."""
    arr = np.asarray(values, dtype=np.float64)
    n = len(arr)
    point = float(np.median(arr))
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = rng.integers(0, n, n)
        boots[i] = float(np.median(arr[idx]))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": point, "bootstrap_ci_95": [float(lo), float(hi)], "n": n, "n_boot": n_boot, "seed": seed}


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> dict:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {"n": n, "successes": successes, "rate": phat, "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)]}
