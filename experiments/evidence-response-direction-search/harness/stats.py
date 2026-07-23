"""AUROC + bootstrap machinery for evidence-response-direction-search (M4c).
Pure CPU, no model.

`auroc` and `bootstrap_auroc_ci` are ported byte-for-byte (except this
docstring) from `margin-evidence-responsiveness-worldknown/harness/stats.py`
(read in full before writing this), which itself ports from
`susceptibility-as-probe/harness/stats.py`: positive class = role=='confab'
(registered score already oriented confab-positive per cell.yaml
`fit.sign_convention`). `bootstrap_paired_diff` is the generic paired
percentile-bootstrap CI used for the native-comparator AUROC-difference
(gates.yaml `D_c_rung_c_primary_companion`), matching gates.yaml
`statistics.resampling_unit`: "row indices within role groups" for AUROC,
"paired resampling for the comparator AUROC-difference".
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


def bootstrap_paired_auroc_diff_ci(
    scores_a: np.ndarray, scores_b: np.ndarray, labels: np.ndarray, *, n_boot: int = 10000, seed: int = 48260724,
) -> dict:
    """Paired bootstrap 95% CI of AUROC(a) - AUROC(b) on the SAME rows
    (same label vector), resampling row indices within role groups so the
    same draw is applied to both score arrays (gates.yaml
    `statistics.resampling_unit`: "paired resampling for the comparator
    AUROC-difference")."""
    scores_a = np.asarray(scores_a, dtype=np.float64)
    scores_b = np.asarray(scores_b, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    if len(scores_a) != len(scores_b) or len(scores_a) != len(labels):
        raise ValueError("bootstrap_paired_auroc_diff_ci: length mismatch across scores_a/scores_b/labels")
    pos_idx = np.where(labels == 1)[0]
    neg_idx = np.where(labels == 0)[0]
    point = auroc(scores_a, labels) - auroc(scores_b, labels)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = _resample_indices_within_groups(rng, pos_idx, neg_idx)
        boots[i] = auroc(scores_a[idx], labels[idx]) - auroc(scores_b[idx], labels[idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "point": point, "bootstrap_ci_95": [float(lo), float(hi)],
        "excludes_zero_from_above": bool(lo > 0.0), "excludes_zero_from_below": bool(hi < 0.0),
        "n_boot": n_boot, "seed": seed,
    }


def bootstrap_ci_covers_point5(scores: np.ndarray, labels: np.ndarray, *, n_boot: int = 10000, seed: int = 48260724) -> dict:
    """Convenience wrapper: bootstrap AUROC CI plus an explicit covers-0.5
    flag, used to adjudicate the M-A falsifier branch split (a1: CI covers
    0.5 vs a2: CI excludes 0.5 from below)."""
    result = bootstrap_auroc_ci(scores, labels, n_boot=n_boot, seed=seed)
    lo, hi = result["bootstrap_ci_95"]
    result["ci_covers_0p5"] = bool(lo <= 0.5 <= hi)
    result["ci_excludes_0p5_from_below"] = bool(hi < 0.5)
    return result
