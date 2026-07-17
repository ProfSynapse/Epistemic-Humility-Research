"""AUROC + class-stratified bootstrap machinery for susceptibility-as-probe
(M2). Pure CPU, no model.

`auroc` is the standard Mann-Whitney U rank statistic (ties split 0.5),
positive class = role=='confab' (every channel's score is already oriented
so higher score = more confab-like: susceptibility is NEGATIVE tipping dose,
confidence and readout are scored as-is and reported with whatever sign the
data gives -- see capture.py's docstring on the readout sign question).

`bootstrap_auroc_ci` / `bootstrap_paired_diff_ci` resample ROW INDICES
WITHIN ROLE GROUPS (gates.yaml `statistics.resampling_unit`: "row indices
within role groups") -- i.e. each bootstrap draw resamples n_confab confab
rows (with replacement, from the confab rows) and n_known known rows
independently, then recomputes the statistic on the concatenated resampled
set. For paired differences, the SAME resampled indices are used for both
scores being compared (that is what makes it a paired bootstrap).
"""

from __future__ import annotations

from typing import Optional

import numpy as np


def auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney U AUROC, positive class = labels==1, ties split 0.5.
    NaN scores are treated as an error (caller must pre-filter to a
    pairwise-complete set)."""
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


def _resample_indices_within_groups(
    rng: np.random.Generator, confab_idx: np.ndarray, known_idx: np.ndarray,
) -> np.ndarray:
    draw_confab = confab_idx[rng.integers(0, len(confab_idx), len(confab_idx))]
    draw_known = known_idx[rng.integers(0, len(known_idx), len(known_idx))]
    return np.concatenate([draw_confab, draw_known])


def bootstrap_auroc_ci(
    scores: np.ndarray, labels: np.ndarray, *,
    n_boot: int = 10000, seed: int = 48260717,
) -> dict:
    scores = np.asarray(scores, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    confab_idx = np.where(labels == 1)[0]
    known_idx = np.where(labels == 0)[0]
    point = auroc(scores, labels)
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = _resample_indices_within_groups(rng, confab_idx, known_idx)
        boots[i] = auroc(scores[idx], labels[idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "point": point, "bootstrap_ci_95": [float(lo), float(hi)],
        "n_boot": n_boot, "seed": seed, "n_confab": len(confab_idx), "n_known": len(known_idx),
    }


def bootstrap_paired_diff_ci(
    scores_a: np.ndarray, scores_b: np.ndarray, labels: np.ndarray, *,
    n_boot: int = 10000, seed: int = 48260717,
) -> dict:
    """Paired bootstrap 95% CI of AUROC(a) - AUROC(b), same resampled row
    indices (within role groups) used for both scores on every draw."""
    scores_a = np.asarray(scores_a, dtype=np.float64)
    scores_b = np.asarray(scores_b, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    confab_idx = np.where(labels == 1)[0]
    known_idx = np.where(labels == 0)[0]
    point_a = auroc(scores_a, labels)
    point_b = auroc(scores_b, labels)
    point_diff = point_a - point_b
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = _resample_indices_within_groups(rng, confab_idx, known_idx)
        boots[i] = auroc(scores_a[idx], labels[idx]) - auroc(scores_b[idx], labels[idx])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    excludes_zero = (lo > 0.0) or (hi < 0.0)
    return {
        "auroc_a": point_a, "auroc_b": point_b, "point_diff": point_diff,
        "bootstrap_ci_95": [float(lo), float(hi)], "excludes_zero": bool(excludes_zero),
        "a_beats_b": bool(excludes_zero and point_diff > 0),
        "b_beats_a": bool(excludes_zero and point_diff < 0),
        "n_boot": n_boot, "seed": seed,
    }


def cross_fitted_combination_auroc(
    readout_z: np.ndarray, susceptibility: np.ndarray, labels: np.ndarray, *,
    n_folds: int = 5, fold_seed: int = 48260718,
) -> np.ndarray:
    """5-fold cross-fitted logistic regression on (readout_z,
    susceptibility): for each fold, fit on the OTHER folds, predict on the
    held-out fold, return out-of-fold predicted probabilities aligned to the
    input row order (no row ever scored by a model that saw it in training).
    Stratified by label so every fold gets both classes."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import StandardScaler

    X = np.column_stack([readout_z, susceptibility])
    y = np.asarray(labels, dtype=np.int64)
    oof = np.full(len(y), np.nan, dtype=np.float64)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=fold_seed)
    for train_idx, test_idx in skf.split(X, y):
        scaler = StandardScaler().fit(X[train_idx])
        clf = LogisticRegression(solver="lbfgs", max_iter=2000, random_state=fold_seed)
        clf.fit(scaler.transform(X[train_idx]), y[train_idx])
        oof[test_idx] = clf.predict_proba(scaler.transform(X[test_idx]))[:, 1]
    if np.any(np.isnan(oof)):
        raise RuntimeError("cross_fitted_combination_auroc: some rows never held out; fold assignment bug")
    return oof


def incremental_auroc_ci(
    readout_z: np.ndarray, susceptibility: np.ndarray, labels: np.ndarray, *,
    n_folds: int = 5, fold_seed: int = 48260718,
    n_boot: int = 10000, seed: int = 48260717,
) -> dict:
    """Incremental AUROC of the cross-fitted (readout_z, susceptibility)
    combination over readout_z alone. The cross-fit is refit inside EVERY
    bootstrap resample (not just once) so the CI reflects both the
    combiner's fold variance and the resampling variance -- the fold seed is
    held fixed across resamples (only the resampled rows change) so the
    fold-assignment mechanism itself is not an extra source of registered
    randomness beyond gates.yaml's two named seeds."""
    readout_z = np.asarray(readout_z, dtype=np.float64)
    susceptibility = np.asarray(susceptibility, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    confab_idx = np.where(labels == 1)[0]
    known_idx = np.where(labels == 0)[0]

    def _point(z, s, y):
        oof = cross_fitted_combination_auroc(z, s, y, n_folds=n_folds, fold_seed=fold_seed)
        return auroc(oof, y), auroc(z, y)

    combo_point, readout_point = _point(readout_z, susceptibility, labels)
    point_incremental = combo_point - readout_point

    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        idx = _resample_indices_within_groups(rng, confab_idx, known_idx)
        z_r, s_r, y_r = readout_z[idx], susceptibility[idx], labels[idx]
        combo_b, readout_b = _point(z_r, s_r, y_r)
        boots[i] = combo_b - readout_b
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {
        "combo_auroc": combo_point, "readout_auroc": readout_point,
        "incremental_point": point_incremental,
        "bootstrap_ci_95": [float(lo), float(hi)],
        "n_boot": n_boot, "seed": seed, "n_folds": n_folds, "fold_seed": fold_seed,
    }


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> dict:
    if n == 0:
        return {"n": 0, "successes": 0, "rate": 0.0, "wilson_ci_95": [0.0, 0.0]}
    phat = successes / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * ((phat * (1 - phat) / n + z * z / (4 * n * n)) ** 0.5)) / denom
    return {
        "n": n, "successes": successes, "rate": phat,
        "wilson_ci_95": [max(0.0, center - half), min(1.0, center + half)],
    }
