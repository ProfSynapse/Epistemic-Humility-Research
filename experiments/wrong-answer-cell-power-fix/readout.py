#!/usr/bin/env python3
"""wrong-answer-cell-power-fix -- pure numeric readout primitives (CPU-only).

Pre-registered in experiments/wrong-answer-cell-power-fix/AMENDMENT.md (SIGNED),
section 2.5 (internal readout) and section 2.6 (metrics). No torch/transformers;
numpy + scikit-learn only, so this is fully exercisable on synthetic vectors
without a GPU or any extracted tensor (score_gates.py's --self-test path).

Implements, in the vocabulary of cell.yaml `internal_readout` / `metrics` /
`ece_reporting`:

  fold_wise_refit_oof   -- A1's estimator. 5-fold stratified CV; per fold the
                            axis anchors (unit(mean(known_correct_answered) -
                            mean(unknown_refused))) are fit on the TRAIN fold's
                            known_correct_answered rows only (the held-out
                            fold's rows never contribute to the axis that scores
                            them), then a 1-D logistic reads P(correct) from the
                            held-out fold's axis projection. unknown_refused
                            rows are never part of the answered-known CV
                            population, so they are not fold-split (see
                            AMENDMENT.md section 2.5 and the spec-ambiguity note
                            in the build report: the two readings of "rows
                            outside the held-out fold" converge here because
                            unknown_refused is never in the held-out fold under
                            either reading).
  frozen_axis_projection_auroc -- A2 (raw projection AUROC on the FROZEN
                            doubt_direction_L35.json axis; descriptive, never
                            gated). Distinct from A1: no per-fold refit, no
                            logistic calibration, just the historical instrument
                            projected onto this cell's population.
  ece / ece_reweighted   -- A5/A6/A7 raw and base-rate-reweighted accounting
                            (cell.yaml `ece_reporting`).
  bootstrap_ci           -- single-metric 95% CI (used for E1's A1 CI).
  paired_bootstrap_delta -- paired-over-rows 95% CI of a metric delta (used for
                            A4, A7 raw/reweighted; generalizes the AUROC-only
                            helper in amendment_s_correctness_probe_score.py to
                            an injectable metric_fn so it also serves ECE).
"""

from __future__ import annotations

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold


# ---------------------------------------------------------------------------
# A1: fold-wise refit axis + 1-D logistic readout, out-of-fold.
# ---------------------------------------------------------------------------

def fold_wise_refit_oof(
    h_answered: np.ndarray, y_answered: np.ndarray, h_unknown_refused: np.ndarray,
    *, n_splits: int = 5, seed: int = 20260808,
) -> np.ndarray:
    """Out-of-fold P(correct) for the answered-known population.

    h_answered: [n, d] h_lora vectors for answered-known rows (correct+wrong).
    y_answered: [n] int, 1=correct 0=wrong (matches h_answered row order).
    h_unknown_refused: [m, d] h_lora vectors for the unknown_refused cell
      (negative anchor pool; never fold-split, see module docstring).

    Raises ValueError if h_unknown_refused is empty (axis undefined) or a fold
    has zero train-side correct rows (positive anchor undefined).
    """
    n = len(y_answered)
    if h_answered.shape[0] != n:
        raise ValueError("h_answered and y_answered length mismatch")
    if h_unknown_refused.shape[0] == 0:
        raise ValueError("h_unknown_refused is empty; negative anchor undefined")
    neg_anchor = h_unknown_refused.mean(axis=0)

    oof = np.full(n, np.nan)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for train_idx, test_idx in skf.split(h_answered, y_answered):
        train_correct = train_idx[y_answered[train_idx] == 1]
        if len(train_correct) == 0:
            raise ValueError(
                "a fold's train split has zero known_correct_answered rows; "
                "positive anchor undefined (increase n_splits down or check class balance)"
            )
        pos_anchor = h_answered[train_correct].mean(axis=0)
        axis = pos_anchor - neg_anchor
        norm = np.linalg.norm(axis)
        if norm == 0:
            raise ValueError("degenerate axis (pos_anchor == neg_anchor)")
        axis = axis / norm

        proj_train = (h_answered[train_idx] @ axis).reshape(-1, 1)
        proj_test = (h_answered[test_idx] @ axis).reshape(-1, 1)
        clf = LogisticRegression(C=1.0, max_iter=2000)
        clf.fit(proj_train, y_answered[train_idx])
        oof[test_idx] = clf.predict_proba(proj_test)[:, 1]
    assert not np.isnan(oof).any()
    return oof


# ---------------------------------------------------------------------------
# A2: frozen (cold-transport) axis, raw projection, descriptive only.
# ---------------------------------------------------------------------------

def frozen_axis_projection_auroc(h_answered: np.ndarray, y_answered: np.ndarray,
                                  theta: np.ndarray) -> float:
    """AUROC of the raw dot-product projection onto the frozen `theta` axis.

    `theta` is doubt_direction_L35.json's raw (mean_pos - mean_neg) vector
    (sha256 f5843ea5... pinned in cell.yaml internal_readout.cold_transport_
    companion). AUROC is scale-invariant so theta's normalization does not
    matter; sign matters (theta's notice: "positive = knows-it", i.e. higher
    projection should rank toward correct=1, matching this call's y convention).
    """
    score = h_answered @ theta
    return float(roc_auc_score(y_answered, score))


# ---------------------------------------------------------------------------
# ECE, raw and base-rate-reweighted (cell.yaml ece_reporting).
# ---------------------------------------------------------------------------

def ece(prob: np.ndarray, y: np.ndarray, n_bins: int = 15,
        weights: np.ndarray | None = None) -> float:
    """Expected calibration error, optionally sample-weighted.

    weights=None reproduces amendment_s_correctness_probe_score.py's `ece`
    exactly (equal per-row weight). A supplied `weights` array reweights each
    row's contribution to both the bin mass and the bin's mean-prob/mean-y.
    """
    if weights is None:
        weights = np.ones_like(prob, dtype=float)
    total_w = weights.sum()
    if total_w <= 0:
        raise ValueError("ece: total weight must be positive")
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    e = 0.0
    for i in range(n_bins):
        lo, hi = edges[i], edges[i + 1]
        m = (prob >= lo) & (prob < hi) if i < n_bins - 1 else (prob >= lo) & (prob <= hi)
        if not m.any():
            continue
        w = weights[m]
        bin_mass = w.sum() / total_w
        mean_prob = float(np.average(prob[m], weights=w))
        mean_y = float(np.average(y[m], weights=w))
        e += bin_mass * abs(mean_prob - mean_y)
    return float(e)


def base_rate_reweight(y: np.ndarray, target_rate: float) -> np.ndarray:
    """Per-row importance weight so the weighted sample's P(y=1) == target_rate.

    weight_i = target_rate / p1        if y_i == 1
             = (1 - target_rate) / (1 - p1)  if y_i == 0
    where p1 = mean(y) (this sample's own empirical correct-rate). Recomputed
    from whatever `y` is passed in (the caller's job to pass the resample when
    used inside a bootstrap loop, per AMENDMENT.md section 2.6 base-rate
    handling: "ECE is base-rate sensitive").
    """
    p1 = float(y.mean())
    if not (0.0 < p1 < 1.0):
        raise ValueError(f"base_rate_reweight: degenerate empirical rate p1={p1}")
    if not (0.0 < target_rate < 1.0):
        raise ValueError(f"base_rate_reweight: target_rate={target_rate} out of (0,1)")
    weights = np.where(y == 1, target_rate / p1, (1.0 - target_rate) / (1.0 - p1))
    return weights.astype(float)


def ece_reweighted(prob: np.ndarray, y: np.ndarray, target_rate: float,
                    n_bins: int = 15) -> float:
    weights = base_rate_reweight(y, target_rate)
    return ece(prob, y, n_bins=n_bins, weights=weights)


# ---------------------------------------------------------------------------
# Bootstrap CIs.
# ---------------------------------------------------------------------------

def bootstrap_ci(y: np.ndarray, score: np.ndarray, metric_fn, n_boot: int,
                  seed: int) -> dict:
    """95% CI of metric_fn(y, score) via resampling rows with replacement."""
    rng = np.random.default_rng(seed)
    n = len(y)
    vals = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yb = y[idx]
        if len(np.unique(yb)) < 2:
            continue
        vals.append(metric_fn(yb, score[idx]))
    vals = np.asarray(vals, dtype=float)
    point = metric_fn(y, score)
    return {
        "point": float(point),
        "n_boot_effective": int(len(vals)),
        "ci_lo": float(np.percentile(vals, 2.5)) if len(vals) else float("nan"),
        "ci_hi": float(np.percentile(vals, 97.5)) if len(vals) else float("nan"),
        "mean": float(vals.mean()) if len(vals) else float("nan"),
    }


def paired_bootstrap_delta(y: np.ndarray, score_a: np.ndarray, score_b: np.ndarray,
                            metric_fn, n_boot: int, seed: int) -> dict:
    """Paired-over-rows 95% CI of metric_fn(y, score_a) - metric_fn(y, score_b).

    Generalizes amendment_s_correctness_probe_score.py's paired_bootstrap_delta
    (which is this function with metric_fn=roc_auc_score) to any row-level
    metric callable, so the same helper serves A4 (AUROC delta) and A7 (ECE
    delta, raw and base-rate-reweighted).
    """
    rng = np.random.default_rng(seed)
    n = len(y)
    deltas = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        yb = y[idx]
        if len(np.unique(yb)) < 2:
            continue
        deltas.append(metric_fn(yb, score_a[idx]) - metric_fn(yb, score_b[idx]))
    deltas = np.asarray(deltas, dtype=float)
    point = metric_fn(y, score_a) - metric_fn(y, score_b)
    ci_lo = float(np.percentile(deltas, 2.5)) if len(deltas) else float("nan")
    ci_hi = float(np.percentile(deltas, 97.5)) if len(deltas) else float("nan")
    return {
        "point": float(point),
        "n_boot_effective": int(len(deltas)),
        "ci_lo": ci_lo,
        "ci_hi": ci_hi,
        "mean": float(deltas.mean()) if len(deltas) else float("nan"),
        "excludes_zero": bool(ci_lo > 0.0 or ci_hi < 0.0),
    }


def metric_auroc(y: np.ndarray, score: np.ndarray) -> float:
    return float(roc_auc_score(y, score))


def make_metric_ece(n_bins: int = 15):
    def _metric(y: np.ndarray, prob: np.ndarray) -> float:
        return ece(prob, y, n_bins=n_bins)
    return _metric


def make_metric_ece_reweighted(target_rate: float, n_bins: int = 15):
    def _metric(y: np.ndarray, prob: np.ndarray) -> float:
        return ece_reweighted(prob, y, target_rate, n_bins=n_bins)
    return _metric
