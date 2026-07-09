"""Category-conditional doubt geometry of the known/unknown contrast.

Raw Qwen3-4B instruct base, pre-generation anchor activations.
Question: is doubt/answerability ONE shared direction across unanswerability
categories, or does each flavor have its own direction?

Tier-1 lab-notebook. CPU only. Load one layer at a time. Seed 20260704.
"""
import json
import os
from pathlib import Path
import numpy as np
from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import joblib

SEED = 20260704
rng = np.random.default_rng(SEED)

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[5]
LEGACY_ANALYSIS = REPO / "experiment" / "phase1" / "probe" / "analysis"
CACHE = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704" / "cache")
AH = str(LEGACY_ANALYSIS / "ah_stage0" / "probes")
OUT = BASE

LAYERS = [20, 24, 28]
CATS = ["ambiguous", "controversial", "counterfactual",
        "false_assumption", "future_unknown", "unsolved_problem"]

# ---------- load manifest ----------
rows = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
N = len(rows)
label = np.array([1 if r["label"] == "unknown" else 0 for r in rows])  # 1 = unknown
cat = np.array([r["category_canon"] for r in rows])
src = np.array([r["source"] for r in rows])

known_idx = np.where(label == 0)[0]
cat_idx = {c: np.where((label == 1) & (cat == c))[0] for c in CATS}

findings = {"seed": SEED, "n_rows": N,
            "n_known": int(len(known_idx)),
            "cat_sizes": {c: int(len(cat_idx[c])) for c in CATS},
            "layers": {}}

# ---------- guard: category x source crosstab ----------
cs = defaultdict(Counter)
for r in rows:
    if r["category_canon"]:
        cs[r["category_canon"]][r["source"]] += 1
src_confound = {}
for c in CATS:
    tot = sum(cs[c].values())
    top_src, top_n = cs[c].most_common(1)[0]
    src_confound[c] = {"by_source": dict(cs[c]),
                       "dominant_source": top_src,
                       "dominant_frac": round(top_n / tot, 3)}
# knowns come from a DISJOINT source set from categorized unknowns -> global flag
known_srcs = sorted(set(src[known_idx]))
unknown_cat_srcs = sorted(set(src[label == 1][cat[label == 1] != ""]))
findings["source_guard"] = {
    "per_category": src_confound,
    "known_sources": known_srcs,
    "categorized_unknown_sources": unknown_cat_srcs,
    "source_disjoint_known_vs_unknown": len(set(known_srcs) & set(unknown_cat_srcs)) == 0,
}


def shrink_whiten_matrix(Xc_list, lam=0.1):
    """Pooled within-class shrinkage-whitening transform W (x -> W @ x).
    Xc_list: list of centered class matrices. Returns W such that cov becomes ~I."""
    d = Xc_list[0].shape[1]
    S = np.zeros((d, d))
    ntot = 0
    for Xc in Xc_list:
        S += Xc.T @ Xc
        ntot += Xc.shape[0]
    S /= max(ntot - len(Xc_list), 1)
    # shrinkage toward scaled identity
    mu = np.trace(S) / d
    S = (1 - lam) * S + lam * mu * np.eye(d)
    # whitening via eigh
    w, V = np.linalg.eigh(S)
    w = np.clip(w, 1e-8, None)
    W = V @ np.diag(1.0 / np.sqrt(w)) @ V.T
    return W


def cosine(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


for L in LAYERS:
    print(f"=== layer L{L} ===", flush=True)
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    Xk = X[known_idx]
    mu_k = Xk.mean(0)

    # size-matched known subsample (match to smallest category for robustness dir)
    min_cat = min(len(cat_idx[c]) for c in CATS)
    sub_k = rng.choice(known_idx, size=min_cat, replace=False)
    mu_k_sub = X[sub_k].mean(0)

    Lrec = {}

    # ---------- (1) per-category directions ----------
    dirs, dirs_sub = {}, {}
    for c in CATS:
        Xc = X[cat_idx[c]]
        dirs[c] = Xc.mean(0) - mu_k
        dirs_sub[c] = Xc.mean(0) - mu_k_sub
    pooled_dir = X[label == 1].mean(0) - mu_k  # all-category doubt direction (uses categorized+uncat unknowns)
    # pooled over CATEGORIZED unknowns only (cleaner for residual test)
    all_cat_idx = np.concatenate([cat_idx[c] for c in CATS])
    pooled_cat_dir = X[all_cat_idx].mean(0) - mu_k

    # whitening from pooled within-class covariance (known + each category centered)
    centered = [Xk - mu_k] + [X[cat_idx[c]] - X[cat_idx[c]].mean(0) for c in CATS]
    W = shrink_whiten_matrix(centered, lam=0.1)

    def cos_matrix(dvec):
        M = np.zeros((len(CATS), len(CATS)))
        for i, ci in enumerate(CATS):
            for j, cj in enumerate(CATS):
                M[i, j] = cosine(dvec[ci], dvec[cj])
        return M

    raw_cos = cos_matrix(dirs)
    dirs_w = {c: W @ dirs[c] for c in CATS}
    whit_cos = cos_matrix(dirs_w)
    # off-diagonal summaries
    off = ~np.eye(len(CATS), dtype=bool)
    Lrec["cosine_raw"] = raw_cos.round(4).tolist()
    Lrec["cosine_whitened"] = whit_cos.round(4).tolist()
    Lrec["cosine_raw_offdiag_mean"] = round(float(raw_cos[off].mean()), 4)
    Lrec["cosine_whitened_offdiag_mean"] = round(float(whit_cos[off].mean()), 4)
    Lrec["cosine_whitened_offdiag_min"] = round(float(whit_cos[off].min()), 4)
    Lrec["cosine_whitened_offdiag_max"] = round(float(whit_cos[off].max()), 4)
    # size-matched-known robustness (whitened offdiag mean)
    dirs_sub_w = {c: W @ dirs_sub[c] for c in CATS}
    Lrec["cosine_whitened_offdiag_mean_sizematched_known"] = round(
        float(cos_matrix(dirs_sub_w)[off].mean()), 4)

    # ---------- (2) transfer AUROC matrix ----------
    # readout: logistic on standardized features (fit scaler on train-only).
    # in-category: 5-fold CV. off-diagonal: fit on i (unknowns of i vs full knowns),
    # eval on j (unknowns of j vs held-out knowns disjoint from any known used in fit).
    # To keep knowns disjoint across the (i,j) eval we split knowns once into two halves.
    k_perm = rng.permutation(known_idx)
    k_fit_pool = k_perm[: len(k_perm) // 2]
    k_eval_pool = k_perm[len(k_perm) // 2:]

    def fit_readout(pos_idx, neg_idx):
        Xtr = X[np.concatenate([pos_idx, neg_idx])]
        ytr = np.concatenate([np.ones(len(pos_idx)), np.zeros(len(neg_idx))])
        m = Xtr.mean(0)
        s = Xtr.std(0) + 1e-6
        clf = LogisticRegression(max_iter=2000, C=1.0)
        clf.fit((Xtr - m) / s, ytr)
        return clf, m, s

    def eval_readout(clf, m, s, pos_idx, neg_idx):
        Xe = X[np.concatenate([pos_idx, neg_idx])]
        ye = np.concatenate([np.ones(len(pos_idx)), np.zeros(len(neg_idx))])
        p = clf.predict_proba((Xe - m) / s)[:, 1]
        return roc_auc_score(ye, p)

    T = np.zeros((len(CATS), len(CATS)))
    for i, ci in enumerate(CATS):
        # fit uses category i unknowns + k_fit_pool knowns
        clf, m, s = fit_readout(cat_idx[ci], k_fit_pool)
        for j, cj in enumerate(CATS):
            if i == j:
                # proper 5-fold CV within category i (unknowns) vs a matched knowns sample
                pos = cat_idx[ci]
                neg = rng.choice(known_idx, size=len(pos), replace=False)
                idx_all = np.concatenate([pos, neg])
                y_all = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))])
                skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
                aucs = []
                for tr, te in skf.split(idx_all, y_all):
                    ptr, ntr = idx_all[tr][y_all[tr] == 1], idx_all[tr][y_all[tr] == 0]
                    pte, nte = idx_all[te][y_all[te] == 1], idx_all[te][y_all[te] == 0]
                    c2, m2, s2 = fit_readout(ptr, ntr)
                    aucs.append(eval_readout(c2, m2, s2, pte, nte))
                T[i, j] = np.mean(aucs)
            else:
                T[i, j] = eval_readout(clf, m, s, cat_idx[cj], k_eval_pool)
    Lrec["transfer_auroc"] = T.round(4).tolist()
    Lrec["transfer_diag_mean"] = round(float(np.diag(T).mean()), 4)
    Lrec["transfer_offdiag_mean"] = round(float(T[off].mean()), 4)
    Lrec["transfer_offdiag_min"] = round(float(T[off].min()), 4)
    Lrec["transfer_gap_diag_minus_offdiag"] = round(
        float(np.diag(T).mean() - T[off].mean()), 4)

    # ---------- (3) shared-axis residual (reducibility test) ----------
    u = pooled_cat_dir / (np.linalg.norm(pooled_cat_dir) + 1e-12)
    resid = {}
    for c in CATS:
        d = dirs[c]
        proj = (d @ u) * u
        r = d - proj
        resid_frac = float(np.linalg.norm(r) / (np.linalg.norm(d) + 1e-12))
        # does the residual still discriminate this cat's unknowns vs held-out knowns?
        # score = X @ r_hat ; AUROC on category unknowns vs matched knowns, 5-fold-ish holdout
        r_hat = r / (np.linalg.norm(r) + 1e-12)
        pos = cat_idx[c]
        neg = rng.choice(known_idx, size=len(pos), replace=False)
        sc = X[np.concatenate([pos, neg])] @ r_hat
        y = np.concatenate([np.ones(len(pos)), np.zeros(len(neg))])
        auc_r = roc_auc_score(y, sc)
        # also the full-direction AUROC for reference
        sc_full = X[np.concatenate([pos, neg])] @ (d / np.linalg.norm(d))
        auc_full = roc_auc_score(y, sc_full)
        resid[c] = {"residual_norm_frac": round(resid_frac, 4),
                    "residual_auroc": round(float(max(auc_r, 1 - auc_r)), 4),
                    "full_dir_auroc": round(float(max(auc_full, 1 - auc_full)), 4)}
    Lrec["shared_axis_residual"] = resid

    Lrec["min_category_size"] = int(min_cat)
    findings["layers"][f"L{L}"] = Lrec
    del X, Xk
    print(f"  L{L} done: whit-offdiag-mean={Lrec['cosine_whitened_offdiag_mean']} "
          f"transfer diag={Lrec['transfer_diag_mean']} off={Lrec['transfer_offdiag_mean']}",
          flush=True)

# ---------- (4) frozen-probe equity ----------
# probe class 1 == 'known'; unknown-score = 1 - p1
probe_equity = {}
for L in LAYERS:
    obj = joblib.load(os.path.join(AH, f"probe_L{L}.joblib"))
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    p_known = obj["clf"].predict_proba(obj["scaler"].transform(X))[:, 1]
    p_unknown = 1 - p_known
    rec = {}
    # per-category AUROC: category unknowns vs ALL knowns
    for c in CATS:
        pos = cat_idx[c]
        idx = np.concatenate([pos, known_idx])
        y = np.concatenate([np.ones(len(pos)), np.zeros(len(known_idx))])
        rec[c] = {
            "auroc_unknown_vs_known": round(float(roc_auc_score(y, p_unknown[idx])), 4),
            "mean_unknown_score": round(float(p_unknown[pos].mean()), 4),
            "median_unknown_score": round(float(np.median(p_unknown[pos])), 4),
            "n": int(len(pos)),
        }
    rec["_mean_known_score_unknownaxis"] = round(float(p_unknown[known_idx].mean()), 4)
    probe_equity[f"L{L}"] = rec
    del X
findings["frozen_probe_equity"] = probe_equity

with open(os.path.join(OUT, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings.json", flush=True)
