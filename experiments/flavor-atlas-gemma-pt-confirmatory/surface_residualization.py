#!/usr/bin/env python3
"""G5 style-residualization secondary for flavor-atlas-gemma-pt-confirmatory
(AMENDMENT.md "Design" G5, gates.yaml gg5_residualization_controls).

Pattern adapted from `experiments/family-atlas-surface-residualization-
control/reanalyze_surface_residualization.py`'s crossfit_ridge /
activation_oof_r2 / standardized_surface_plant, but the surface basis is
NOT that reference's `build_surface_features` unchanged: that function's
one-hot `source`/`category` columns are exactly the prohibited signal for
THIS cell (dataset source, panel identity, KUQ category, flavor, and label
may not enter the surface matrix here -- AMENDMENT.md G5, gates.yaml gg5
prohibited_surface_inputs). This module's surface basis is built ONLY from
the question string's own text-shape statistics and hashed lexical n-grams,
with no row-identity or label-derived column of any kind.

Pipeline:
  1. build_surface_matrix(rows) -> Z, question-text-only, unsupervised.
  2. crossfit_ridge(H, Z) -> per-layer activation matrix H residualized on
     Z out of fold, alpha selected per outer fold by inner three-fold
     activation MSE from the registered grid.
  3. The pinned probe (internal_panel_probe_gate._cv_auroc_with_oof) reruns
     unchanged on the residual.
  4. Controls: permuted-surface negative control (20 reps of the alpha
     selection + residualization pipeline with Z's rows independently
     shuffled), and a planted-channel positive control at hidden state 0
     (a linear-in-surface direction planted on the provably-null hs0
     anchor, which residualization must remove).

Secondary readout only (gates.yaml gg5, pass_required_for_secondary_only):
failure here makes P4/F3 indeterminate and never touches P1/P2/P3.
"""

from __future__ import annotations

import string
import sys
from pathlib import Path
from typing import Sequence

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
ITEM26_DIR = REPO_ROOT / "experiments" / "ood-breadth-beyond-selfaware"
sys.path.insert(0, str(ITEM26_DIR))
import internal_panel_probe_gate as ipg  # pinned module, unmodified

ALPHA_GRID = [0.01, 0.1, 1, 10, 100, 1000]
OUTER_FOLDS = 5
INNER_FOLDS = 3
N_PERMUTATIONS = 20
PLANT_HIDDEN_STATE = 0

# Columns explicitly excluded from the surface basis (AMENDMENT.md G5
# prohibited-input rule, gates.yaml gg5 prohibited_surface_inputs). Listed
# here as documentation; build_surface_matrix never reads any of these
# fields from a row even if present.
PROHIBITED_SURFACE_INPUTS = frozenset({
    "source", "panel", "category", "flavor", "label",
    "generated_text", "completion_length", "answer_correctness",
    "answer_text", "aliases",
})


class ResidualizationError(SystemExit):
    pass


def _question_scalars(question: str) -> np.ndarray:
    n_chars = len(question)
    denom = max(n_chars, 1)
    digit = sum(ch.isdigit() for ch in question)
    punctuation = sum(ch in string.punctuation for ch in question)
    newline = question.count("\n")
    uppercase = sum(ch.isupper() for ch in question)
    return np.asarray([
        n_chars, len(question.split()), newline + 1,
        digit, digit / denom,
        punctuation, punctuation / denom,
        newline, newline / denom,
        uppercase, uppercase / denom,
    ], dtype=np.float64)


def build_surface_matrix(questions: Sequence[str], seed: int = 0,
                          word_svd_components: int = 16,
                          char_svd_components: int = 16,
                          word_hash_features: int = 512,
                          char_hash_features: int = 512) -> np.ndarray:
    """Question-text-only unsupervised surface basis Z. No row identity, no
    dataset source, no label. See module docstring."""
    from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
    from sklearn.decomposition import TruncatedSVD
    from sklearn.preprocessing import StandardScaler

    if not questions:
        raise ResidualizationError("cannot build a surface matrix from zero rows")

    scalar_raw = np.stack([_question_scalars(q) for q in questions])
    scalar_z = StandardScaler().fit_transform(scalar_raw)

    word_hash = HashingVectorizer(
        n_features=word_hash_features, alternate_sign=False,
        analyzer="word", ngram_range=(1, 2), norm=None, lowercase=True,
    ).transform(questions)
    char_hash = HashingVectorizer(
        n_features=char_hash_features, alternate_sign=False,
        analyzer="char", ngram_range=(3, 5), norm=None, lowercase=True,
    ).transform(questions)
    word_tfidf = TfidfTransformer(sublinear_tf=True).fit_transform(word_hash)
    char_tfidf = TfidfTransformer(sublinear_tf=True).fit_transform(char_hash)

    max_rank = max(1, min(len(questions) - 1, word_tfidf.shape[1] - 1))
    word_rank = min(word_svd_components, max_rank)
    char_rank = min(char_svd_components, max_rank)
    word_svd = TruncatedSVD(n_components=word_rank, random_state=seed).fit_transform(word_tfidf)
    char_svd = TruncatedSVD(n_components=char_rank, random_state=seed + 1).fit_transform(char_tfidf)
    lexical = StandardScaler().fit_transform(np.concatenate([word_svd, char_svd], axis=1))

    return np.concatenate([scalar_z, lexical], axis=1)


def _make_strata(values: Sequence, n_splits: int) -> np.ndarray:
    labels = np.asarray([str(v) for v in values])
    unique, counts = np.unique(labels, return_counts=True)
    rare = set(unique[counts < n_splits])
    if rare:
        labels = np.asarray(["__rare__" if v in rare else v for v in labels])
    _, counts = np.unique(labels, return_counts=True)
    if counts.size == 0 or counts.min() < n_splits:
        labels = np.zeros(len(labels), dtype=int).astype(str)
    return labels


def crossfit_ridge(H: np.ndarray, Z: np.ndarray, strata: Sequence, *,
                    alpha_grid: Sequence[float] = ALPHA_GRID,
                    outer_folds: int = OUTER_FOLDS, inner_folds: int = INNER_FOLDS,
                    seed: int = 0) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """Cross-fitted ridge H ~ Z, out of fold. Returns (residual, yhat,
    chosen_alphas_per_outer_fold). Alpha selected per outer fold by inner
    three-fold activation MSE, exactly as AMENDMENT.md G5 registers."""
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_squared_error
    from sklearn.model_selection import StratifiedKFold

    if H.ndim != 2 or Z.ndim != 2 or H.shape[0] != Z.shape[0]:
        raise ResidualizationError("crossfit inputs must be aligned 2D matrices")
    yhat = np.empty_like(H, dtype=np.float64)
    chosen: list[float] = []
    outer_labels = _make_strata(strata, outer_folds)
    outer = StratifiedKFold(n_splits=outer_folds, shuffle=True, random_state=seed)
    for fold, (train, test) in enumerate(outer.split(Z, outer_labels)):
        inner_labels = _make_strata(np.asarray(strata)[train], inner_folds)
        inner = StratifiedKFold(n_splits=inner_folds, shuffle=True, random_state=seed + 100 + fold)
        losses: dict[float, list[float]] = {float(a): [] for a in alpha_grid}
        for inner_train, inner_valid in inner.split(Z[train], inner_labels):
            tr, va = train[inner_train], train[inner_valid]
            for alpha in losses:
                model = Ridge(alpha=alpha, fit_intercept=True)
                model.fit(Z[tr], H[tr])
                pred = model.predict(Z[va])
                losses[alpha].append(mean_squared_error(H[va], pred))
        alpha = min(losses, key=lambda a: (float(np.mean(losses[a])), a))
        chosen.append(alpha)
        model = Ridge(alpha=alpha, fit_intercept=True)
        model.fit(Z[train], H[train])
        yhat[test] = model.predict(Z[test])
    return H.astype(np.float64) - yhat, yhat, chosen


def activation_oof_r2(H: np.ndarray, residual: np.ndarray) -> float:
    centered = H.astype(np.float64) - H.mean(axis=0, keepdims=True)
    total = float(np.sum(centered ** 2))
    if total <= 1e-30:
        return 0.0
    return float(1.0 - np.sum(residual.astype(np.float64) ** 2) / total)


def standardized_surface_plant(Z: np.ndarray, hidden_width: int, target_H: np.ndarray, seed: int) -> np.ndarray:
    """Plant a linear-in-surface direction at hs0 (the provably-null layer:
    Y measures 0.4979 on this substrate, Qwen atlas exactly 0.5000), scaled
    to the target activation's own RMS so the plant is neither trivially
    dominant nor negligible."""
    from sklearn.preprocessing import StandardScaler

    Z_std = StandardScaler().fit_transform(Z)
    rng = np.random.default_rng(seed)
    projection = rng.normal(size=(Z_std.shape[1], hidden_width)) / np.sqrt(Z_std.shape[1])
    surface = Z_std @ projection
    surface -= surface.mean(axis=0, keepdims=True)
    target_centered = target_H - target_H.mean(axis=0, keepdims=True)
    source_rms = float(np.sqrt(np.mean(surface ** 2)))
    target_rms = float(np.sqrt(np.mean(target_centered ** 2)))
    if source_rms <= 1e-30 or target_rms <= 1e-30:
        raise ResidualizationError("planted-signal RMS scaling is degenerate")
    return surface * (target_rms / source_rms)


def residualized_probe_auroc(H_residual: np.ndarray, y: np.ndarray) -> float:
    mean_auc, _std, _oof = ipg._cv_auroc_with_oof(H_residual, y, folds=5, C=0.5, seed=0)
    return float(mean_auc)


def permutation_negative_control(H: np.ndarray, Z: np.ndarray, strata: Sequence, y: np.ndarray, *,
                                  n_permutations: int = N_PERMUTATIONS, seed: int = 0) -> dict:
    """Independently shuffle Z's rows (breaking any real question<->
    activation correspondence while preserving Z's own marginal
    distribution) and rerun the crossfit + probe pipeline. Registered
    pass: >= 18/20 permuted runs still clear 0.90 on the primary probe."""
    rng = np.random.default_rng(seed)
    passes = 0
    r2s = []
    for rep in range(n_permutations):
        perm = rng.permutation(len(Z))
        Z_perm = Z[perm]
        residual, _yhat, _alphas = crossfit_ridge(H, Z_perm, strata, seed=seed + rep)
        r2s.append(activation_oof_r2(H, residual))
        auc = residualized_probe_auroc(residual, y)
        if auc >= 0.90:
            passes += 1
    return {"n_permutations": n_permutations, "n_passing_0_90": passes, "permuted_r2": r2s}


def planted_channel_positive_control(H0: np.ndarray, Z: np.ndarray, strata: Sequence, y: np.ndarray, *,
                                      seed: int = 0) -> dict:
    """Plant at hidden state 0, require pooled AUROC >= 0.90 unresidualized
    and <= 0.75 after residualization (gates.yaml gg5)."""
    plant = standardized_surface_plant(Z, H0.shape[1], H0, seed)
    planted_H = H0 + plant
    raw_auc = residualized_probe_auroc(planted_H, y)
    residual, _yhat, _alphas = crossfit_ridge(planted_H, Z, strata, seed=seed)
    controlled_auc = residualized_probe_auroc(residual, y)
    return {
        "planted_pooled_auroc": round(raw_auc, 4),
        "residualized_planted_pooled_auroc": round(controlled_auc, 4),
        "planted_pass": bool(raw_auc >= 0.90),
        "residualized_pass": bool(controlled_auc <= 0.75),
    }
