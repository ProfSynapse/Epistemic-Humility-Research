"""Shared library for veto-transport analysis (TODO item 31).

CPU-only. Loads cached per-row hidden states (pre/post generation),
applies cached probes (dot-product), fits fresh PCA-128 + saga probes,
computes axis geometry. No model / GPU.
"""
import os
import json
from pathlib import Path
import numpy as np
from safetensors.numpy import load_file

REPO = os.environ.get(
    "EHR_REPO",
    str(Path(__file__).resolve().parents[4]),
)
PROBE = os.path.join(REPO, "experiment/phase1/probe")

S_DIR = os.path.join(PROBE, "qwen3-4b-instruct/amendment_s/stage2")
W_DIR = os.path.join(PROBE, "qwen3-4b-instruct/amendment_w/stage2")
T_DIR = os.path.join(PROBE, "qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2")
U_DIR = os.path.join(PROBE, "qwen3-4b-clean-sft-grpo-v2/amendment_u/stage2")
TSA = os.path.join(REPO, "experiments/common/artifacts/two_signal_calibration")
AXES = os.path.join(PROBE, "qwen3-4b-instruct/behavior_axis_directions")


def load_rows(d):
    return [json.loads(l) for l in open(os.path.join(d, "rows.jsonl"))]


def tensor_path(d, row_key, pos):
    return os.path.join(d, row_key.replace("::", "__") + "__" + pos + ".safetensors")


def load_layer_matrix(d, rows, pos, layer, cache=None):
    """Return (N, 2560) matrix of the given position/layer for all rows, in row order.
    Skips rows whose file is missing (returns mask too)."""
    key = f"L{layer}"
    X = []
    mask = []
    for r in rows:
        p = tensor_path(d, r["row_key"], pos)
        if not os.path.exists(p):
            mask.append(False)
            continue
        if cache is not None and p in cache:
            t = cache[p]
        else:
            t = load_file(p)
            if cache is not None:
                cache[p] = t
        X.append(t[key].astype(np.float64))
        mask.append(True)
    return np.asarray(X), np.asarray(mask)


def load_all_layers(d, rows, pos, layers):
    """Load a dict layer->matrix in one pass over files (memory: N*len(layers)*2560*8).
    Returns (dict, mask)."""
    keys = [f"L{l}" for l in layers]
    out = {l: [] for l in layers}
    mask = []
    for r in rows:
        p = tensor_path(d, r["row_key"], pos)
        if not os.path.exists(p):
            mask.append(False)
            continue
        t = load_file(p)
        for l, k in zip(layers, keys):
            out[l].append(t[k].astype(np.float64))
        mask.append(True)
    return {l: np.asarray(v) for l, v in out.items()}, np.asarray(mask)


def load_probe(name):
    """name e.g. 'dial__qwen3-4b-instruct__post_L20' or 'gate__qwen3-4b-instruct__pre_L18'."""
    d = np.load(os.path.join(TSA, name + ".npz"), allow_pickle=True)
    return {k: d[k] for k in d.files}


def apply_probe(probe, X):
    """Apply cached probe (standardize then dot). Returns raw decision score (logit-ish)."""
    z = (X - probe["scaler_mean"]) / probe["scaler_scale"]
    return z @ probe["logreg_coef"]


def project_on_coef(X, coef):
    """Simple projection onto a raw coefficient vector (no standardization)."""
    return X @ coef


# ---- fresh probe (PCA-128 + saga) ----
def fit_pca(X, n_components=128, seed=0):
    """Randomized PCA, label-agnostic. Returns (mean, components (k,d))."""
    from sklearn.decomposition import PCA
    mu = X.mean(0)
    p = PCA(n_components=min(n_components, X.shape[0] - 1, X.shape[1]),
            svd_solver="randomized", random_state=seed)
    p.fit(X - mu)
    return mu, p.components_


def cv_auroc(X, y, layer_seed=0, n_splits=5, C=1.0):
    """PCA-128 (fit on train fold only) + saga LR, stratified CV, return mean AUROC + oof scores."""
    from sklearn.model_selection import StratifiedKFold
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.decomposition import PCA
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=layer_seed)
    oof = np.zeros(len(y))
    aucs = []
    for tr, te in skf.split(X, y):
        mu = X[tr].mean(0)
        p = PCA(n_components=min(128, len(tr) - 1, X.shape[1]),
                svd_solver="randomized", random_state=layer_seed)
        Ztr = p.fit_transform(X[tr] - mu)
        Zte = p.transform(X[te] - mu)
        lr = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000, C=C)
        lr.fit(Ztr, y[tr])
        s = lr.decision_function(Zte)
        oof[te] = s
        aucs.append(roc_auc_score(y[te], s))
    return float(np.mean(aucs)), float(np.std(aucs)), oof


def fit_full_probe(X, y, seed=0, C=1.0):
    """Fit PCA-128 + saga on ALL data, return a callable full-dim coef in original space.
    Returns dict with 'mean','components','lr_coef','apply' where score(Xnew)=... .
    We fold PCA into a single 2560-dim direction: coef_full = components.T @ lr.coef_ ."""
    from sklearn.linear_model import LogisticRegression
    mu, comps = fit_pca(X, seed=seed)
    Z = (X - mu) @ comps.T
    lr = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000, C=C)
    lr.fit(Z, y)
    coef_full = comps.T @ lr.coef_.ravel()   # (2560,)
    intercept = float(lr.intercept_[0]) - float(mu @ coef_full)
    return {"mean": mu, "coef_full": coef_full, "intercept": intercept}


def score_full_probe(fp, X):
    return X @ fp["coef_full"] + fp["intercept"]


def whiten_cov(X_list, shrink=0.1):
    """Pooled within-class covariance whitening matrix W = Sigma^{-1/2} with shrinkage.
    X_list: list of class matrices. Returns W (d,d)."""
    d = X_list[0].shape[1]
    S = np.zeros((d, d))
    n = 0
    for Xc in X_list:
        Xc = Xc - Xc.mean(0)
        S += Xc.T @ Xc
        n += Xc.shape[0]
    S /= max(n - len(X_list), 1)
    S = (1 - shrink) * S + shrink * np.eye(d) * np.trace(S) / d
    # symmetric inverse sqrt
    vals, vecs = np.linalg.eigh(S)
    vals = np.clip(vals, 1e-8, None)
    W = vecs @ np.diag(vals ** -0.5) @ vecs.T
    return W


def cos(a, b):
    a = np.asarray(a, float).ravel()
    b = np.asarray(b, float).ravel()
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))
