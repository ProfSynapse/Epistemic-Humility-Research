#!/usr/bin/env python3
"""Shared primitives for the correctness-geometry scale-ladder cell (v2).

Pre-registered in experiments/correctness-geometry-scale-ladder/AMENDMENT.md
(design source: scale_identifiability_design.md, lead adjudication section 12
+ v2 rebuild sections 13-21). Pure library module (no CLI entrypoint, no
independent execution loop) -- `instrument.persistence` in experiment.yaml
declares it `short-run` because importing it does no fitting of its own; all
fitting happens in the two entrypoints that import it
(scale_ladder_real.py, scale_ladder_planted_sim.py), each of which declares
its own `incremental` persistence.

Reuses, by import (never reimplemented), the primitives the packet names as
prior art:
  - experiments/correctness-direction-rotation/cd_rotation_analysis.py:
    `full_direction` (PCA-space logistic normal mapped to ambient, unit-norm),
    `cv_auroc` (5-fold pooled OOF AUROC), `cos` (cosine of two vectors).
  - experiments/correctness-subspace-overlap/subspace_overlap_analysis.py:
    `sub_seed`/`rng_for` (deterministic, order-independent sub-seeding keyed
    by explicit strings), `parallel_map`/`_run_capped`/`_default_workers`
    (joblib/loky layer-level parallelism with per-call BLAS thread caps),
    `deflation_subspace` (ordered, deterministic k>1 discriminative
    subspace estimator -- the only k>1 path this cell is permitted to use;
    the k>1 bootstrap-SVD path is FORBIDDEN per the design packet section 3
    "FORBIDDEN estimator" and the mechanism note
    library/concepts/mechanisms/l2-logistic-bootstrap-svd-cannot-resolve-multidim-discriminative-subspace.md).

Estimators E1/E2/E3/E4 are implemented here once and called identically by
both the real-ladder driver and the planted-signal validation harness, so a
planted-signal PASS is evidence about the exact code path that will run on
real labels after sign (not a look-alike reimplementation).

=== v2 REBUILD (2026-07-20, after the v1 G_val stop) ===

v1's synthetic generator (`synthetic_planted_features`, now REMOVED, not kept
around as a known-broken code path) planted a single mean-shift vector
regardless of nominal "rank," which is Bayes-optimal-linear-rank-1 in every
condition -- the protocol could not express a genuinely multi-direction
discriminative object, and E2's "top-1 vs full" ratio was mathematically
tautological for ANY linear signal (the fitted logistic normal IS the top-1
direction, scored by its own projection). See design packet section 13 for
the full diagnosis and experiments/correctness-geometry-scale-ladder's
NOTEBOOK.md 2026-07-20 for the v1 run record.

v2 replaces the generator with a CORRELATED-REDUNDANT flat-Rashomon
construction (section 14): an r-axis block whose within-block covariance is
equicorrelated (rho), not identity, so the r axes are correlated, redundant
readouts of the label rather than r independent slivers of one vector. This
produces genuine near-multicollinearity in the logistic MLE at finite n --
many near-tied linear combinations of the r axes reach nearly the same
AUROC (a real Rashomon-flat set), unstable argmax direction, stable AUROC --
which is the CD/SO "stable AUROC, unstable direction" fingerprint, not an
artifact of construction. E1 (per-half PCA refit, full-n primary), E2
(nested best-single-axis, not the joint normal), and E4 (null-subtracted
participation ratio) are rebuilt per section 15; E3-k1 is unchanged (its
FAILURE in v1 traced entirely to the generator, not its own code).

=== v3 (2026-07-20, after the v2 G_construction stop) ===

v2's OWN construction-validity criterion (a) -- "k=1 must be genuinely
insufficient to decode a planted rank r>1 signal" -- turned out to be
unsatisfiable by ANY two-class Gaussian mean-shift construction, correlated
or not (the Bayes-optimal linear boundary is always rank-1, LDA argument;
verified empirically at every (scale, r) cell). The lead and the designer
both concurred this criterion tests the WRONG axis (decodability rank)
against a real target (SO's committed correctness object) that is itself
nearly k=1-decodable while directionally unstable -- retired, not patched.
v3 replaces it with (a-new) monotone E1 full-n degradation across the
r-ladder (the axis the cell actually measures: identifiability, not
decodability) and (b-new) a derived index-resolution criterion
(sigma_c <= R_max) in place of the old hand-picked absolute-0.70 E1 floor;
see scale_ladder_planted_sim.py `check_construction_validity`. This module
adds ONE estimator-level fix that both the construction-validity gate and
every reported E1 number now use: `e1_split_half_reliability_avg`, which
averages E1 over R_SH independent split-half draws instead of relying on
v2's single noisy draw (section 22.6.4).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]
_CD_DIR = _REPO_ROOT / "experiments" / "correctness-direction-rotation"
_SO_DIR = _REPO_ROOT / "experiments" / "correctness-subspace-overlap"
for _d in (_CD_DIR, _SO_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import cd_rotation_analysis as cd  # noqa: E402  full_direction, cv_auroc, cos
import subspace_overlap_analysis as so  # noqa: E402  sub_seed, rng_for,
# parallel_map, _run_capped, _default_workers, deflation_subspace

sub_seed = so.sub_seed
rng_for = so.rng_for
parallel_map = so.parallel_map
_run_capped = so._run_capped
default_workers = so._default_workers
deflation_subspace = so.deflation_subspace
full_direction = cd.full_direction
cv_auroc = cd.cv_auroc
cos = cd.cos

# --- pinned constants (cell.yaml; packet section 2/3/9, lead adjudication) --
PCA_DIM = 128
N_FOLDS = 5
MIN_CLASS = 30
R_DRAWS = 30          # matched-n stratified draws (control 1)
R_RAND = 20           # E3 random-slice draws
R_SIM = 30            # G_val planted-signal replicates per (scale, condition)
N_STAR = 377          # matched-n floor, per section 2/12.4: min class count = 1.7B correct
K_GATE_LAYERS_WINDOW = 3   # +/- 3 layers around best-dial, E1/E2 robustness only

# --- v3 fix (i): E1 split-half AVERAGING count (design packet section
# 22.6.4 / lead ruling item 3(i), 2026-07-20). v2's E1 was a SINGLE
# split-half draw per rep -- very noisy at these n, which inflated
# `diffuse_hw` (especially at 1.7B) and, per section 22.7, was the leading
# suspect for the 1.7B index-resolution marginal-fail. Averaging over R_SH
# independent split-half draws shrinks that RNG component consistently on
# BOTH synthetic and real data (the fix is applied identically wherever E1
# is computed), reporting E1 as a stable statistic rather than one noisy
# draw. Locked at 15 -- within the lead-authorized [10, 20] range -- after a
# timing smoke confirmed the official R_SIM=30 run stays comfortably under
# the ~30 min / 8-worker budget at this value (see NOTEBOOK.md v3 entry);
# NOT tuned against any gate result.
R_SH = 15

# --- v2 correlated-redundant flat-Rashomon generator constants (section 14) -
# The r-ladder {1,2,4,8} is evaluated at a single FIXED "moderate" block
# correlation, locked BEFORE any construction-validity or G_val result is
# read (packet: "at fixed moderate rho, for monotonicity checks"). "Moderate"
# is read as: strong enough to produce visible redundancy (not near-
# independent axes, which would just be r separate weak signals, not a
# Rashomon-flat set) but not so strong the r axes collapse into near-exact
# duplicates. This value is NOT retuned after seeing any result -- it is a
# pre-committed generative-model constant, exactly like v1's PCA_DIM=128.
RHO_LADDER = 0.7

# Grid the "diffuse" reference's (r, rho) is chosen from, per lead ruling
# 21.1: anchor to CD's 0.174 half-sample split-half reliability (priority)
# and SO's ~0.04 random-slice margin (secondary, within reported slack).
# This is a calibration of what "diffuse" MEANS in the simulation against an
# already-published empirical fingerprint from a DIFFERENT prior experiment
# -- not a retuning of any threshold this cell's own estimators are judged
# against, so it does not violate the no-goalpost-drift rule.
DIFFUSE_R_GRID = (8, 16, 32, 64, 128)
DIFFUSE_RHO_GRID = (0.3, 0.5, 0.7, 0.85, 0.95)
DIFFUSE_FINGERPRINT_TARGET = {
    "e1_full_n": 0.174,          # CD Outcome line 217, half-sample split-half floor
    "e3_k1_margin": 0.04,        # SO Outcome lines 606-610, discriminative-minus-random-slice
}

# Per-scale layer geometry (packet section 2/3; X Outcome lines 176/196/214
# for best-dial layers; fixed fractional depth = round(0.6 * n_layers)).
SCALES = ("1.7b", "8b", "14b")
N_LAYERS = {"1.7b": 28, "8b": 36, "14b": 40}
HIDDEN_DIM = {"1.7b": 2048, "8b": 4096, "14b": 5120}
BEST_DIAL_LAYER = {"1.7b": 21, "8b": 20, "14b": 28}
FIXED_DEPTH_LAYER = {s: round(0.6 * N_LAYERS[s]) for s in SCALES}
EXPECTED_CLASS_COUNTS = {  # packet section 2 table; verified against rows.jsonl 2026-07-20
    "1.7b": (377, 1476), "8b": (648, 1205), "14b": (741, 1112),
}
# archive/experiment/phase1-data/ is gitignored (generated, large): it exists
# only in the canonical checkout's local filesystem, not replicated into a
# `git worktree add` checkout. Read it from the canonical checkout by
# absolute path rather than repo-relative, matching the project convention
# that generated/local data is not duplicated per worktree (see root
# CLAUDE.md "Generated outputs... are not source of truth unless a checked-in
# manifest... says otherwise"). Read-only access; never written here.
_CANONICAL_CHECKOUT = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DATA_DIRS = {
    "1.7b": _CANONICAL_CHECKOUT / "archive/experiment/phase1-data/probe/qwen3-1.7b-bnb-4bit/amendment_x/stage2",
    "8b": _CANONICAL_CHECKOUT / "archive/experiment/phase1-data/probe/qwen3-8b-bnb-4bit/amendment_x/stage2",
    "14b": _CANONICAL_CHECKOUT / "archive/experiment/phase1-data/probe/qwen3-14b-bnb-4bit/amendment_x/stage2",
}


def best_dial_window(scale: str) -> list[int]:
    """+/- 3 layers around the scale's best-dial layer, clipped to [0, n_layers].
    Robustness-only scan for E1/E2 (packet section 3); NOT part of the G1
    require-both conjunction, which uses exactly {best-dial, fixed-depth}."""
    c = BEST_DIAL_LAYER[scale]
    n = N_LAYERS[scale]
    return [l for l in range(c - K_GATE_LAYERS_WINDOW, c + K_GATE_LAYERS_WINDOW + 1)
            if 0 <= l <= n]


def gate_layers(scale: str) -> dict[str, int]:
    """The two G1 require-both layer choices for one scale."""
    return {"best_dial": BEST_DIAL_LAYER[scale], "fixed_depth": FIXED_DEPTH_LAYER[scale]}


# --- matched-n stratified subsampling (control 1) ---------------------------
def stratified_subsample_indices(y: np.ndarray, n_per_class: int, seed: int) -> np.ndarray:
    """Draw a balanced n_per_class/n_per_class index set without replacement,
    class-stratified. Deterministic given seed; order of the returned indices
    is class-major (all class-1 indices first) but callers never rely on
    positional order, only on (X[idx], y[idx]) pairing."""
    rng = np.random.default_rng(seed)
    idx_pos = np.where(y == 1)[0]
    idx_neg = np.where(y == 0)[0]
    if len(idx_pos) < n_per_class or len(idx_neg) < n_per_class:
        raise ValueError(f"cannot draw {n_per_class}/{n_per_class}: have "
                          f"{len(idx_pos)} pos / {len(idx_neg)} neg")
    sel_pos = rng.choice(idx_pos, size=n_per_class, replace=False)
    sel_neg = rng.choice(idx_neg, size=n_per_class, replace=False)
    return np.concatenate([sel_pos, sel_neg])


def fit_pca128(X_amb: np.ndarray, seed: int = 20260719):
    pca = PCA(n_components=PCA_DIM, svd_solver="randomized", random_state=seed)
    Xp = pca.fit_transform(X_amb)
    return pca, Xp


def _stratified_half_split(y: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    idx_pos = rng.permutation(np.where(y == 1)[0])
    idx_neg = rng.permutation(np.where(y == 0)[0])
    kp, kn = len(idx_pos) // 2, len(idx_neg) // 2
    ia = np.concatenate([idx_pos[:kp], idx_neg[:kn]])
    ib = np.concatenate([idx_pos[kp:2 * kp], idx_neg[kn:2 * kn]])
    return ia, ib


# --- E1: split-half k=1 direction reliability (PRIMARY, gate-able; v2) ------
def e1_split_half_reliability(Xp: np.ndarray, y: np.ndarray, seed: int) -> float:
    """v2 fix (i): PER-HALF PCA REFIT (SO's convention), replacing v1's
    shared-basis-across-both-halves fit (diagnosis 5, an optimism leak).
    Xp already lives in the working D=pca_dim basis (either the real
    per-draw PCA-128 space, or -- for the planted sim -- the generator's
    direct D=128 output, matching packet section 14's literal framing). The
    refit here is therefore a FULL-RANK PCA(n_components=Xp.shape[1]) on
    each half separately: no dimensionality is discarded, so this is not a
    truncation-leak fix, but it IS a real fix regardless -- each half's own
    empirical covariance has a different eigenbasis (sampling noise, even at
    full rank), and cd.full_direction's L2-regularized-logistic-plus-per-
    axis-StandardScaler fit is NOT invariant to which orthonormal frame it
    runs in (unlike an unregularized logistic, whose fitted decision
    boundary is rotation-invariant). Fitting PCA on the FULL sample before
    splitting lets each half's chosen frame be weakly correlated with the
    other half's data through the shared basis, which is exactly the leak
    the per-half refit removes.

    Returns |cosine| of the two half-fit ambient-mapped normals; NaN if a
    half is underpowered (MIN_CLASS floor per class per half)."""
    ia, ib = _stratified_half_split(y, seed)
    ya, yb = y[ia], y[ib]
    if min((ya == 1).sum(), (ya == 0).sum()) < MIN_CLASS or \
       min((yb == 1).sum(), (yb == 0).sum()) < MIN_CLASS:
        return float("nan")
    d = Xp.shape[1]
    pca_a = PCA(n_components=d, svd_solver="full").fit(Xp[ia])
    pca_b = PCA(n_components=d, svd_solver="full").fit(Xp[ib])
    Xp_a = pca_a.transform(Xp[ia])
    Xp_b = pca_b.transform(Xp[ib])
    da = full_direction(Xp_a, ya, pca_a.components_)
    db = full_direction(Xp_b, yb, pca_b.components_)
    return abs(cos(da, db))


# --- v3 fix (i): E1 averaged over R_SH independent split-half draws --------
def e1_split_half_reliability_avg(Xp: np.ndarray, y: np.ndarray, seed: int,
                                   r_sh: int = R_SH) -> float:
    """Design packet section 22.6.4 / lead ruling item 3(i): average
    |cosine| over `r_sh` INDEPENDENT split-half draws (each with its own
    explicit sub-seed, never call order), replacing v2's single-draw E1.
    NaN draws (an underpowered half) are dropped from the mean rather than
    treated as zero. This is the estimator wherever E1 is reported after
    v3 -- the planted sim's official reps, the diffuse-calibration search
    (at a cheaper r_sh, since that search's own numbers are never gated or
    reported, only used to pick (r, rho)), and the real driver's real-mode
    fits (`e1_split_half_reliability` below remains the single-draw
    primitive this wraps, retained for that use plus any future
    diagnostic that wants one draw)."""
    vals = []
    for sh in range(r_sh):
        sh_seed = sub_seed(seed, "sh", f"draw{sh}")
        v = e1_split_half_reliability(Xp, y, sh_seed)
        if np.isfinite(v):
            vals.append(v)
    return float(np.mean(vals)) if vals else float("nan")


# --- nested nested-CV restricted-subspace AUROC (E3/construction-validity) --
def restricted_cv_auroc(Xp: np.ndarray, y: np.ndarray, k: int, seed: int,
                         direction_override: np.ndarray | None = None) -> float:
    """OOF AUROC of a k-dim discriminative subspace, fit on TRAIN FOLDS ONLY
    per fold (the SO-trap discipline: label-dependent fit nested inside CV,
    never fit on the full labels before scoring). k=1 uses cd.full_direction
    (identical machinery to E1's per-fold building block); k>1 uses SO's
    deflation_subspace (the only permitted k>1 estimator). For k=1 the
    fold's OOF score is the raw projection onto the train-fit unit
    direction, which reproduces the logistic decision_function up to a
    positive scale and additive constant (both AUROC-invariant).

    If direction_override is given (shape (pca_dim,) for k=1 only), skip the
    per-fold fit and score every row against this FIXED direction instead --
    used by E3's random-slice control, where the "direction" is a random
    draw rather than something fit on data (so there is no OOF leak risk;
    the same fixed random direction is legitimately used at every fold).

    Also used, unchanged, by the v2 construction-validity gate's k-sweep
    (section 14 criterion (a)): k=1..8 deflation AUROC, checking that k=1 is
    genuinely insufficient for a planted rank r>1 -- unlike v1, where the
    mean-shift construction made k=1 always sufficient regardless of r."""
    n = len(y)
    oof = np.zeros(n, dtype=float)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    eye = np.eye(Xp.shape[1])
    for tr, te in skf.split(Xp, y):
        if direction_override is not None:
            oof[te] = Xp[te] @ direction_override
            continue
        if k == 1:
            d = full_direction(Xp[tr], y[tr], eye)
            oof[te] = Xp[te] @ d
        else:
            basis = deflation_subspace(Xp[tr], y[tr], k, eye)  # pca_dim x k
            proj_tr = Xp[tr] @ basis
            proj_te = Xp[te] @ basis
            sc = StandardScaler().fit(proj_tr)
            clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000,
                                      random_state=seed)
            clf.fit(sc.transform(proj_tr), y[tr])
            oof[te] = clf.decision_function(sc.transform(proj_te))
    return float(roc_auc_score(y, oof))


def random_direction(pca_dim: int, rng: np.random.Generator) -> np.ndarray:
    v = rng.standard_normal(pca_dim)
    return v / np.linalg.norm(v)


def random_subspace(pca_dim: int, k: int, rng: np.random.Generator) -> np.ndarray:
    g = rng.standard_normal((pca_dim, k))
    q, _ = np.linalg.qr(g)
    return q[:, :k]


# --- vectorized per-column AUROC via the Mann-Whitney U identity -----------
# AUC = U / (n_pos * n_neg), U = sum(ranks of positives) - n_pos*(n_pos+1)/2.
# No explicit fit, no scipy dependency. Ties assumed negligible (continuous
# Gaussian-derived synthetic features / continuous real activations); a
# tie-corrected average-rank would be needed for discretized data, not
# needed here (filled gap, documented; verified against sklearn.roc_auc_score
# column-by-column in the pre-flight sanity check, see NOTEBOOK.md).
def _column_ranks(X: np.ndarray) -> np.ndarray:
    n, d = X.shape
    order = np.argsort(X, axis=0)
    ranks = np.empty_like(order, dtype=float)
    rank_vals = np.broadcast_to(np.arange(1, n + 1, dtype=float)[:, None], (n, d))
    cols = np.broadcast_to(np.arange(d), (n, d))
    ranks[order, cols] = rank_vals
    return ranks


def _auroc_from_ranks(ranks: np.ndarray, y: np.ndarray) -> np.ndarray:
    n_pos = int(np.sum(y == 1))
    n_neg = int(np.sum(y == 0))
    if n_pos == 0 or n_neg == 0:
        return np.full(ranks.shape[1], 0.5)
    sum_ranks_pos = ranks[y == 1].sum(axis=0)
    u = sum_ranks_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def _column_aurocs(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    return _auroc_from_ranks(_column_ranks(X), y)


# --- E2: best-single-axis concentration ratio (PRIMARY, gate-able; v2) -----
def e2_concentration_ratio(Xp: np.ndarray, y: np.ndarray, seed: int) -> dict:
    """v2 REDEFINITION (lead's option (a), section 15): replaces v1's
    top-1-vs-full ratio, whose "top-1" was cd.full_direction itself -- the
    SAME fitted logistic normal scored by projecting onto itself, which
    diagnosis 13.2 proved is mathematically near-tautological (ratio ~1 for
    ANY linear-decodable signal, confirmed empirically at 0.997-1.013 across
    every v1 planted rank including diffuse).

    Here "top-1" is the single PCA AXIS (not a fitted linear combination)
    with the strongest TRAIN-FOLD univariate |AUROC-0.5|, selected on train
    and scored OOF (nested selection -- removes the max-of-128
    selection-bias inflation a full-sample selection would carry, the SO-trap
    discipline applied to axis choice). A compact (r=1) signal concentrates
    on exactly one axis -> ratio near 1 (that axis alone recovers nearly all
    the joint AUROC). A redundant r>1 block spreads the signal across r
    correlated copies -> any single copy alone carries less of the joint
    signal than the combined fit -> ratio < 1. Not the joint normal, so not
    tautological by the same argument as v1's E2."""
    auroc_full = cv_auroc(Xp, y)
    n = len(y)
    oof = np.zeros(n, dtype=float)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    chosen_axes = []
    for tr, te in skf.split(Xp, y):
        aucs_tr = _column_aurocs(Xp[tr], y[tr])
        scores = np.abs(aucs_tr - 0.5)
        j = int(np.argmax(scores))
        sign = 1.0 if aucs_tr[j] >= 0.5 else -1.0
        oof[te] = sign * Xp[te, j]
        chosen_axes.append(j)
    auroc_top1 = float(roc_auc_score(y, oof))
    denom = auroc_full - 0.5
    ratio = float((auroc_top1 - 0.5) / denom) if abs(denom) > 1e-9 else float("nan")
    return {"auroc_full": auroc_full, "auroc_top1": auroc_top1, "ratio": ratio,
            "chosen_axes_per_fold": chosen_axes}


# --- E3: within-stage random-slice recovery margin (k=1 gate, k=8 desc) ----
# UNCHANGED from v1 (design packet section 15: "Implementation unchanged; it
# now *varies* because the construction now varies"). The v1 failure was
# entirely a property of the generator (a mean-shift signal is Bayes-
# optimal-rank-1 regardless of construction, so a well-fit direction beats a
# random direction by a similar margin under any nominal "rank"), not of
# this estimator's own code.
def e3_random_slice_margin(Xp: np.ndarray, y: np.ndarray, k: int, seed: int) -> dict:
    disc_auroc = restricted_cv_auroc(Xp, y, k, seed)
    rand_aurocs = []
    for r in range(R_RAND):
        rand_rng = rng_for(seed, f"e3_rand_k{k}", f"r{r}")
        if k == 1:
            d = random_direction(Xp.shape[1], rand_rng)
            rand_aurocs.append(restricted_cv_auroc(Xp, y, 1, seed, direction_override=d))
        else:
            basis = random_subspace(Xp.shape[1], k, rand_rng)
            n = len(y)
            oof = np.zeros(n, dtype=float)
            skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
            proj_all = Xp @ basis
            for tr, te in skf.split(Xp, y):
                sc = StandardScaler().fit(proj_all[tr])
                clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=5000,
                                          random_state=seed)
                clf.fit(sc.transform(proj_all[tr]), y[tr])
                oof[te] = clf.decision_function(sc.transform(proj_all[te]))
            rand_aurocs.append(float(roc_auc_score(y, oof)))
    rand_mean = float(np.mean(rand_aurocs))
    return {"discriminative_auroc": disc_auroc, "random_slice_mean_auroc": rand_mean,
            "random_slice_aurocs": rand_aurocs, "margin": float(disc_auroc - rand_mean)}


def _e3_margin_quick(Xp: np.ndarray, y: np.ndarray, seed: int, r_rand: int) -> float:
    """Cheaper E3-k1-margin for the diffuse (r, rho) CALIBRATION SEARCH only
    (fewer random-slice draws than the official R_RAND=20) -- never used for
    a reported/gated value. The final locked-in diffuse condition's official
    E3 margin is always computed by e3_random_slice_margin with the full
    R_RAND=20, at R_SIM=30 reps, exactly like every other condition."""
    disc = restricted_cv_auroc(Xp, y, 1, seed)
    rand_vals = []
    for r in range(r_rand):
        rand_rng = rng_for(seed, "e3quick", f"r{r}")
        d = random_direction(Xp.shape[1], rand_rng)
        rand_vals.append(restricted_cv_auroc(Xp, y, 1, seed, direction_override=d))
    return float(disc - float(np.mean(rand_vals)))


# --- E4: null-subtracted participation ratio of the discriminability
#     spectrum (SECONDARY, gate-optional; v2) --------------------------------
def e4_participation_ratio(Xp: np.ndarray, y: np.ndarray, seed: int,
                            p_perm: int = 100) -> dict:
    """v2 fix (section 15): the v1 criterion ("recovered PR within +/-1 of
    true rank") was hopeless because ~127 of 128 PCA axes carry no true
    signal but each contributes a small nonzero univariate AUROC deviation
    by finite-sample chance, and their squared sum dominates the true-signal
    axis/axes' contribution to the participation-ratio formula (confirmed:
    v1 recovered PR 37.9-53.2 for true rank 1/2/4/8). Fix: estimate each
    axis's noise floor by LABEL PERMUTATION (P=p_perm reshuffles of y on the
    SAME held-out half, recomputing the per-axis discriminability spectrum
    each time), then subtract the permutation-mean floor from the observed
    spectrum before forming PR. This is a null-subtracted / shrunk spectrum,
    not a raw one -- the many noise axes' expected contribution is removed
    rather than left to dominate. Held-out convention unchanged from v1: a
    single stratified 50% split (paired with E1's own split seed for
    hygiene), scored via the vectorized rank-based AUROC (no logistic fits,
    cheap even at P=100).

    Reports both the null-subtracted PR (the v2 gate-relevant quantity) and
    the raw (unadjusted) PR for comparability with v1's NOTEBOOK numbers."""
    _, ib = _stratified_half_split(y, seed)
    y_te = y[ib]
    if min((y_te == 1).sum(), (y_te == 0).sum()) < 2:
        return {"pr": float("nan"), "pr_raw_unadjusted": float("nan"),
                "s_i_adjusted": [], "perm_mean_floor": []}
    Xp_te = Xp[ib]
    ranks_te = _column_ranks(Xp_te)
    aucs_obs = _auroc_from_ranks(ranks_te, y_te)
    s_obs = np.abs(aucs_obs - 0.5) * 2.0

    perm_rng = np.random.default_rng(sub_seed(seed, "e4_perm"))
    perm_s = np.empty((p_perm, Xp.shape[1]), dtype=float)
    for p in range(p_perm):
        y_perm = perm_rng.permutation(y_te)
        aucs_p = _auroc_from_ranks(ranks_te, y_perm)
        perm_s[p] = np.abs(aucs_p - 0.5) * 2.0
    perm_mean = perm_s.mean(axis=0)

    s_adj = np.clip(s_obs - perm_mean, 0.0, None)
    sum_s, sum_s2 = float(s_adj.sum()), float((s_adj ** 2).sum())
    pr = float((sum_s ** 2) / sum_s2) if sum_s2 > 1e-12 else float("nan")

    sum_raw, sum_raw2 = float(s_obs.sum()), float((s_obs ** 2).sum())
    pr_raw = float((sum_raw ** 2) / sum_raw2) if sum_raw2 > 1e-12 else float("nan")

    return {"pr": pr, "pr_raw_unadjusted": pr_raw,
            "s_i_adjusted": s_adj.tolist(), "perm_mean_floor": perm_mean.tolist()}


# --- v2 correlated-redundant flat-Rashomon generator (section 14) ----------
def synthetic_redundant_features(n_pos: int, n_neg: int, pca_dim: int, rank, rho: float,
                                  target_auroc: float, seed: int,
                                  calib_iters: int = 40) -> tuple[np.ndarray, np.ndarray]:
    """Isotropic Gaussian background in D=pca_dim (this generator's output IS
    the working PCA-128-space basis directly -- packet section 14's literal
    framing, and v1's own convention; no separate ambient/truncation step).

    Choose an axis-aligned r-axis block (r randomly-chosen raw axes out of
    pca_dim, carried over from v1's E4 axis-alignment rationale: a
    randomly-ROTATED block would make E4's per-raw-axis participation-ratio
    statistic blind to rank regardless of the covariance fix, exactly as
    found for v1's mean-shift generator). Give the positive class a mean
    shift spread evenly over the block. Impose WITHIN-BLOCK COVARIANCE
    (1-rho)*I_r + rho*11^T (equicorrelated / compound symmetry) on those same
    r axes for BOTH classes (background covariance, not label-dependent) via
    the standard equicorrelated construction: block_i = sqrt(rho)*z +
    sqrt(1-rho)*eps_i, with z, eps_i ~ N(0,1) iid across rows -- this gives
    Cov(block_i, block_j) = rho for i != j, Var(block_i) = 1, i.e. r
    correlated, redundant readouts of the SAME underlying block rather than
    r independent slivers of one vector (diagnosis 13.3: this is what a
    Rashomon-flat set actually is -- many near-optimal linear combinations
    of the r axes, not a high-rank mean shift).

    r=1 or rho<=0 has no internal block correlation to impose (a 1x1 block
    is trivially uncorrelated with itself); the background stays iid on
    those axes and only the mean shift differs by class, matching v1's
    original rank-1 behavior exactly (the crystallized reference case).

    Signal strength is calibrated by bisection on the shift magnitude so the
    synthetic full-PCA-128 OOF AUROC (via cv_auroc, the SAME function used
    on real data) matches target_auroc -- unchanged calibration mechanism
    from v1, just against the new covariance-block construction.

    n_pos/n_neg are independent (not forced equal) so this same function
    generates BOTH the full-n (imbalanced, matching each scale's real
    class counts -- E1's v2 primary regime) and matched-n (balanced N*/N*
    -- E1's secondary regime, and E2/E3/E4's primary regime) datasets."""
    rng = np.random.default_rng(seed)
    n = n_pos + n_neg
    y = np.array([1] * n_pos + [0] * n_neg)
    r = int(rank)
    axes = rng.choice(pca_dim, size=r, replace=False)
    bg = rng.standard_normal((n, pca_dim))
    if r > 1 and rho and rho > 0:
        z = rng.standard_normal(n)
        eps = rng.standard_normal((n, r))
        bg[:, axes] = np.sqrt(rho) * z[:, None] + np.sqrt(1.0 - rho) * eps
    shift_shape = np.zeros(pca_dim)
    shift_shape[axes] = 1.0 / np.sqrt(r)

    def make_xy(strength: float) -> tuple[np.ndarray, np.ndarray]:
        X = bg.copy()
        X[y == 1] += strength * shift_shape
        return X, y

    # Headroom note (found during v2 build, not a tuning pass): at high rho
    # the equicorrelated block's Mahalanobis distance for a fixed raw shift
    # magnitude is mu^T Sigma^-1 mu = strength^2 * r / (1 + (r-1)*rho) -- as
    # rho -> 1, r correlated copies carry no more Mahalanobis information
    # than ONE copy (diminishing returns, exactly the redundancy property
    # this generator is meant to encode), so a fixed strength ceiling that
    # was adequate for the uncorrelated case can be far too low to reach the
    # SAME target AUROC at high (r, rho). Expand the ceiling geometrically
    # (bounded) before bisecting, rather than silently returning an
    # undershoot -- this keeps the calibration's actual contract ("match
    # target_auroc") intact regardless of (r, rho), it does not change what
    # is being calibrated to.
    lo, hi = 0.0, 8.0
    for _ in range(20):
        X_hi, _ = make_xy(hi)
        if cv_auroc(X_hi, y) >= target_auroc:
            break
        hi *= 2.0
    for _ in range(calib_iters):
        mid = 0.5 * (lo + hi)
        X_mid, _ = make_xy(mid)
        auc_mid = cv_auroc(X_mid, y)
        if auc_mid < target_auroc:
            lo = mid
        else:
            hi = mid
    return make_xy(0.5 * (lo + hi))


def diffuse_grid_points() -> list[tuple]:
    """All (r, rho) pairs in the diffuse-calibration grid, as an explicit
    task list for the caller to dispatch through parallel_map (parallelize-
    by-default: each grid point is an independent unit of work, keyed only
    by its own (scale, r, rho) identifiers, never by iteration order)."""
    return [(r, rho) for r in DIFFUSE_R_GRID for rho in DIFFUSE_RHO_GRID]


def diffuse_grid_point(scale: str, r: int, rho: float, target_auroc: float,
                        n_pos_full: int, n_neg_full: int, n_star: int, base_seed: int,
                        quick_reps: int = 2, quick_r_rand: int = 5,
                        quick_calib_iters: int = 25, quick_r_sh: int = 3) -> dict:
    """One (r, rho) candidate's quick fingerprint estimate for the diffuse
    calibration search (lead ruling 21.1): priority 1 is E1's FULL-N
    split-half reliability vs CD's 0.174; priority 2 (tiebreak only) is the
    matched-n E3-k1 random-slice margin vs SO's ~0.04, within reported
    slack. Uses a SMALL number of quick reps and a cheaper E3 random-slice
    count (this is a calibration search, not a reported value) at a
    slightly coarser AUROC-calibration tolerance; the final locked-in
    (r, rho) is then run at the full R_SIM=30 / R_RAND=20 / calib_iters=40
    official precision by the caller, exactly like every other condition.

    This anchors what "diffuse" MEANS in the simulation to an independently
    published empirical fingerprint from CD/SO -- distinct in kind from
    retuning a gate threshold to make an estimator pass; the grid and the
    fingerprint targets are fixed before any search result is read. The
    caller (scale_ladder_planted_sim.py) dispatches every grid point through
    lib.parallel_map and selects the argmin afterwards; this function itself
    does no parallel dispatch, matching the lib/orchestration split used
    throughout this module.

    `quick_r_sh` (v3 fix (i), section 22.6.4) is a CHEAPER r_sh than the
    official R_SH=15 used for the locked-in candidate's real reps -- this
    search's own numbers are never gated or reported (only used to pick
    (r, rho)), matching the existing convention (quick_reps/quick_r_rand/
    quick_calib_iters are all already cheaper than official precision, per
    the v2 filled-gap #4 rationale: only the SEARCH is coarse, the final
    locked-in point is always re-run at full official precision)."""
    e1_vals, e3_vals = [], []
    for rep in range(quick_reps):
        rep_seed = sub_seed(base_seed, scale, "diffuse_calib", f"r{r}", f"rho{rho}", f"rep{rep}")
        gen_seed_full = sub_seed(rep_seed, "gen_full")
        X_full, y_full = synthetic_redundant_features(
            n_pos_full, n_neg_full, PCA_DIM, r, rho, target_auroc, gen_seed_full,
            calib_iters=quick_calib_iters,
        )
        e1 = e1_split_half_reliability_avg(X_full, y_full, sub_seed(rep_seed, "e1"), r_sh=quick_r_sh)
        e1_vals.append(e1)
        sub_idx = stratified_subsample_indices(y_full, n_star, sub_seed(rep_seed, "sub"))
        Xm, ym = X_full[sub_idx], y_full[sub_idx]
        e3 = _e3_margin_quick(Xm, ym, sub_seed(rep_seed, "e3"), quick_r_rand)
        e3_vals.append(e3)
    e1_mean = float(np.nanmean(e1_vals)) if len(e1_vals) else float("nan")
    e3_mean = float(np.nanmean(e3_vals)) if len(e3_vals) else float("nan")
    score_e1 = abs(e1_mean - DIFFUSE_FINGERPRINT_TARGET["e1_full_n"])
    score_e3 = abs(e3_mean - DIFFUSE_FINGERPRINT_TARGET["e3_k1_margin"])
    return {"r": r, "rho": rho, "e1_full_n_mean": e1_mean, "e3_k1_margin_mean": e3_mean,
            "score_e1": score_e1, "score_e3": score_e3}


def pick_best_diffuse_candidate(candidates: list[dict]) -> dict:
    best = None
    for cand in candidates:
        if best is None or cand["score_e1"] < best["score_e1"] - 1e-9 or (
                abs(cand["score_e1"] - best["score_e1"]) <= 1e-9 and cand["score_e3"] < best["score_e3"]):
            best = cand
    return best
