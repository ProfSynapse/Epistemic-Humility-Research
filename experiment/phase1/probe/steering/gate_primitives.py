#!/usr/bin/env python3
"""Reusable gate-scoring primitives for declarative steering/readout cells.

Every primitive here is pure, CPU-only, and free of model loads: it takes flat
per-row records (the provenance JSONL the steer-cell runner writes) plus scalar
parameters and returns a small result dict or number. The declarative gate layer
(score_gates.py) composes these into named gates via a gates.yaml.

The gate vocabulary mirrors what the hand-built steering amendments computed
inline (AA/AC/AG/AL/AN): count a kind of flip, compare a steered arm to a
matched control with a seeded row bootstrap CI, run a seeded label-permutation
test, and floor an AUROC with an analytic (Hanley-McNeil) standard error plus a
bootstrap lower bound. Keeping them in one library means a new amendment writes a
gates.yaml, not a fresh bootstrap loop.

Determinism contract: every function that samples takes an integer ``seed`` and
draws from ``numpy.random.default_rng(seed)`` so a re-run is byte-identical.
"""
from __future__ import annotations

import math
from typing import Callable, Optional, Sequence

import numpy as np

Record = dict
Predicate = Callable[[Record], bool]


# ---------------------------------------------------------------------------
# Flip counting
# ---------------------------------------------------------------------------

def count_flips(
    records: Sequence[Record],
    before: Predicate,
    after: Predicate,
    universe: Optional[Predicate] = None,
) -> dict:
    """Count rows that satisfy ``before`` at baseline and ``after`` post-arm.

    A "flip" is a row for which ``before(row)`` and ``after(row)`` both hold, so
    the two predicates encode the transition of interest (e.g. before = baseline
    confab, after = steered refusal => a killed confab). ``universe`` optionally
    restricts the denominator (e.g. only flagged rows).

    Returns ``{"universe": N, "before": M, "flips": K, "rate": K/M}`` where the
    rate is flips over the before-population (0.0 when that population is empty).
    """
    rows = [r for r in records if universe(r)] if universe else list(records)
    before_rows = [r for r in rows if before(r)]
    flips = [r for r in before_rows if after(r)]
    m = len(before_rows)
    return {
        "universe": len(rows),
        "before": m,
        "flips": len(flips),
        "rate": (len(flips) / m) if m else 0.0,
    }


# ---------------------------------------------------------------------------
# Steered-vs-control difference with a seeded row bootstrap CI
# ---------------------------------------------------------------------------

def kill_diff_vs_control(
    treatment_indicator: Sequence[int],
    control_indicator: Sequence[int],
    *,
    seed: int,
    n_boot: int = 1000,
    ci: float = 0.95,
) -> dict:
    """Specificity contrast: sum(treatment) - sum(control) with a paired row
    bootstrap CI over a shared row universe.

    ``treatment_indicator`` and ``control_indicator`` are aligned 0/1 arrays over
    the SAME ordered universe (e.g. the baseline-confab rows): index i is 1 when
    that row was killed under the treatment / control arm respectively. The point
    estimate is the raw count difference; the CI resamples rows (paired: the same
    resampled index is read from both arms so the correlation is preserved) and
    reports the difference-of-sums per resample.

    Returns the point diff, the per-arm counts, the bootstrap mean, and the CI
    bounds. ``ci_excludes_zero`` is True when the lower bound is strictly > 0.
    """
    t = np.asarray(treatment_indicator, dtype=np.int64)
    c = np.asarray(control_indicator, dtype=np.int64)
    if t.shape != c.shape:
        raise ValueError(
            f"indicator length mismatch: treatment {t.shape} vs control {c.shape}")
    n = t.shape[0]
    diff_per_row = t - c
    point = int(t.sum() - c.sum())
    rng = np.random.default_rng(seed)
    boots = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, size=n) if n else np.empty(0, dtype=int)
        boots[b] = diff_per_row[idx].sum() if n else 0.0
    lo_q = (1.0 - ci) / 2.0
    hi_q = 1.0 - lo_q
    ci_lo = float(np.quantile(boots, lo_q)) if n else 0.0
    ci_hi = float(np.quantile(boots, hi_q)) if n else 0.0
    return {
        "treatment_count": int(t.sum()),
        "control_count": int(c.sum()),
        "diff": point,
        "n_rows": n,
        "bootstrap_mean": float(boots.mean()) if n else 0.0,
        "ci": [round(ci_lo, 4), round(ci_hi, 4)],
        "ci_level": ci,
        "ci_excludes_zero": bool(ci_lo > 0.0),
    }


# ---------------------------------------------------------------------------
# Seeded label-permutation test
# ---------------------------------------------------------------------------

def permutation_p(
    values: Sequence[float],
    labels: Sequence[int],
    *,
    seed: int,
    n_perm: int = 10000,
    tail: str = "greater",
) -> dict:
    """Two-group permutation test on a difference of means.

    ``values`` are per-row scalars, ``labels`` are 0/1 group assignments over the
    same rows. The observed statistic is mean(values[label==1]) -
    mean(values[label==0]); the null permutes the labels ``n_perm`` times (seeded)
    and counts how often the permuted statistic is at least as extreme.

    ``tail`` is "greater", "less", or "two-sided". The p-value uses the
    add-one correction (``(hits + 1) / (n_perm + 1)``) so it is never exactly 0.
    """
    v = np.asarray(values, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    if v.shape != y.shape:
        raise ValueError(f"values/labels length mismatch: {v.shape} vs {y.shape}")
    if set(np.unique(y).tolist()) - {0, 1}:
        raise ValueError("labels must be 0/1")
    n1 = int(y.sum())
    n0 = int((1 - y).sum())
    if n1 == 0 or n0 == 0:
        raise ValueError("both groups must be non-empty")

    def stat(mask):
        return float(v[mask == 1].mean() - v[mask == 0].mean())

    obs = stat(y)
    rng = np.random.default_rng(seed)
    perms = np.empty(n_perm)
    for i in range(n_perm):
        perms[i] = stat(rng.permutation(y))
    if tail == "greater":
        hits = int(np.sum(perms >= obs))
    elif tail == "less":
        hits = int(np.sum(perms <= obs))
    elif tail == "two-sided":
        hits = int(np.sum(np.abs(perms) >= abs(obs)))
    else:
        raise ValueError(f"tail must be greater|less|two-sided, got {tail!r}")
    p = (hits + 1) / (n_perm + 1)
    return {
        "observed": round(obs, 6),
        "n_perm": n_perm,
        "tail": tail,
        "p_value": p,
        "n_treatment": n1,
        "n_control": n0,
    }


# ---------------------------------------------------------------------------
# AUROC with an analytic SE floor and a bootstrap CI lower bound
# ---------------------------------------------------------------------------

def _auroc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUROC (equivalent to the Mann-Whitney U statistic), tie-safe."""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    n_pos, n_neg = len(pos), len(neg)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(len(scores), dtype=np.float64)
    ranks[order] = np.arange(1, len(scores) + 1, dtype=np.float64)
    # average ranks within tie groups
    s_sorted = scores[order]
    i = 0
    while i < len(s_sorted):
        j = i
        while j + 1 < len(s_sorted) and s_sorted[j + 1] == s_sorted[i]:
            j += 1
        if j > i:
            avg = (ranks[order[i]] + ranks[order[j]]) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
        i = j + 1
    sum_pos_ranks = ranks[labels == 1].sum()
    u = sum_pos_ranks - n_pos * (n_pos + 1) / 2.0
    return float(u / (n_pos * n_neg))


def _hanley_mcneil_se(auc: float, n_pos: int, n_neg: int) -> float:
    """Hanley-McNeil analytic standard error of an AUROC point estimate."""
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    q1 = auc / (2.0 - auc)
    q2 = 2.0 * auc * auc / (1.0 + auc)
    var = (auc * (1.0 - auc)
           + (n_pos - 1) * (q1 - auc * auc)
           + (n_neg - 1) * (q2 - auc * auc)) / (n_pos * n_neg)
    return math.sqrt(var) if var > 0 else 0.0


def auroc_floor(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    floor: float,
    seed: int,
    n_boot: int = 1000,
    ci: float = 0.95,
) -> dict:
    """AUROC point estimate plus a Hanley-McNeil SE and a seeded bootstrap CI-LB,
    tested against a floor.

    Returns the point AUROC, the analytic SE, the bootstrap CI [lo, hi], and
    ``pass`` = the bootstrap lower bound is >= ``floor`` (the conservative test;
    the analytic SE is reported alongside for context, not used for the gate).
    """
    s = np.asarray(scores, dtype=np.float64)
    y = np.asarray(labels, dtype=np.int64)
    if s.shape != y.shape:
        raise ValueError(f"scores/labels length mismatch: {s.shape} vs {y.shape}")
    n_pos = int(y.sum())
    n_neg = int((1 - y).sum())
    point = _auroc(s, y)
    se = _hanley_mcneil_se(point, n_pos, n_neg)
    rng = np.random.default_rng(seed)
    n = len(s)
    boots = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        a = _auroc(s[idx], y[idx])
        if not math.isnan(a):
            boots.append(a)
    if boots:
        lo_q = (1.0 - ci) / 2.0
        ci_lo = float(np.quantile(boots, lo_q))
        ci_hi = float(np.quantile(boots, 1.0 - lo_q))
    else:
        ci_lo = ci_hi = float("nan")
    return {
        "auroc": round(point, 4),
        "hanley_mcneil_se": round(se, 4) if not math.isnan(se) else None,
        "ci": [round(ci_lo, 4) if not math.isnan(ci_lo) else None,
               round(ci_hi, 4) if not math.isnan(ci_hi) else None],
        "ci_level": ci,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "floor": floor,
        "pass": bool((not math.isnan(ci_lo)) and ci_lo >= floor),
    }


# ---------------------------------------------------------------------------
# Threshold helpers (leaf comparisons a gates.yaml composes)
# ---------------------------------------------------------------------------

def at_most(value: float, ceiling: float) -> dict:
    """value <= ceiling."""
    return {"value": value, "threshold": f"<= {ceiling}",
            "pass": bool(value <= ceiling)}


def at_least(value: float, floor: float) -> dict:
    """value >= floor."""
    return {"value": value, "threshold": f">= {floor}",
            "pass": bool(value >= floor)}


def within(value: float, lo: float, hi: float) -> dict:
    """lo <= value <= hi (a precise-zero / no-regression band)."""
    return {"value": value, "threshold": f"in [{lo}, {hi}]",
            "pass": bool(lo <= value <= hi)}
