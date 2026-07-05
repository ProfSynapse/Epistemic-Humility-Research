#!/usr/bin/env python3
"""Backlog item 22a: what predicts CONTROVERSIAL flips under the certainty prime?

Anomaly (session-0036 pliability fleet, Amendment AH surface): baseline refusal is
one clean curve in caution_dist_z (AUROC 0.956). Under the certainty (release) prime,
which rows flip refuse->answer also tracks boundary distance (pooled inverse AUROC
0.146 == effective 0.854) for every flavor EXCEPT controversial: within-controversial
z-AUROC is 0.338 (near chance) while controversial has the HIGHEST flip rate (25%).
Interaction LR p=0.026. So controversial flips for reasons the caution axis misses.
This script hunts for what DOES predict controversial flips.

Flip definition (identical to pliability_analysis.py):
  eligible = baseline (A0) refused
  flip (uptake) = baseline refused AND certainty-prime (Acertain) answered
  modeled WITHIN each flavor, on eligible rows only.

Predictors tested within controversial (each: repeated stratified CV AUROC +- spread,
with a label-permutation null):
  a. frozen knowledge-probe unknown-score (L20/24/28)   [precomputed score_L24 too]
  b. projection onto per-flavor residual directions (controversial residual = target;
     shared trunk + other flavors' residuals = specificity controls)
  c. direct within-flavor activation probe: PCA-128 (label-agnostic, per layer) + saga
     logistic, proper held-out repeated CV, layer sweep L8/16/20/24/28/34
  d. cheap surface features: question length (chars/words), '?' count, has-'or',
     TF-IDF + logistic on question text
Specificity: rerun the winning predictor(s) on the OTHER flavors' flips.

CPU only. Load one activation layer at a time. Seed fixed. No gates, Tier-1 notebook.
"""
import json
import os
import re
import numpy as np
from collections import Counter
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline
import joblib

SEED = 20260704
rng = np.random.default_rng(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.abspath(os.path.join(HERE, "..", "ah_main"))
CACHE = os.path.abspath(os.path.join(HERE, "..", "mi_category_geometry_20260704", "cache"))
PROBES = os.path.abspath(os.path.join(HERE, "..", "ah_stage0", "probes"))

CATS = ["ambiguous", "controversial", "unsolved_problem",
        "false_assumption", "future_unknown", "counterfactual"]
PROBE_LAYERS = [20, 24, 28]
SWEEP_LAYERS = [8, 16, 20, 24, 28, 34]
N_PCA = 128
CV_SPLITS = 5
CV_REPEATS = 20        # small n -> average many splits
N_PERM = 200           # permutation-null replicates

# ---------------------------------------------------------------- data load
def load(arm):
    return [json.loads(l) for l in open(os.path.join(GEN, f"gen_{arm}", "rows.jsonl"))]

a0_rows = load("A0")
ac_rows = load("Acertain")
a0 = {r["row_key"]: r for r in a0_rows}

# cache manifest -> row_key to cache-row-index
man = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
key2cache = {r["row_key"]: i for i, r in enumerate(man)}

# Build the eligible/flip table per flavor from the RELEASE arm (Acertain).
# elig = baseline refused ; flip = baseline refused AND prime answered.
records = {c: [] for c in CATS}
join_miss = Counter()
for pr in ac_rows:
    b = a0[pr["row_key"]]
    if not b["refused"]:
        continue  # not eligible
    c = pr["category_canon"]
    if c not in CATS:
        continue
    ci = key2cache.get(pr["row_key"], None)
    if ci is None:
        join_miss[c] += 1
    records[c].append({
        "row_key": pr["row_key"],
        "flip": 1 if pr["answered"] else 0,
        "caution_dist_z": b["caution_dist_z"],
        "score_L24": b["score_L24"],
        "question": b["question"],
        "cache_idx": ci,
    })

flip_counts = {c: {"n_elig": len(records[c]),
                   "n_flip": int(sum(r["flip"] for r in records[c])),
                   "flip_rate": round(float(np.mean([r["flip"] for r in records[c]])), 4)
                                 if records[c] else None,
                   "n_cache_missing": int(join_miss[c])}
               for c in CATS}


def auroc_dir(y, x):
    """Direction-agnostic AUROC (report max(auc, 1-auc)) plus signed auc."""
    y = np.asarray(y); x = np.asarray(x)
    if len(set(y.tolist())) < 2:
        return None, None
    a = float(roc_auc_score(y, x))
    return round(max(a, 1 - a), 4), round(a, 4)


# ---------------------------------------------------------------- (1) anomaly repro
anomaly = {}
for c in CATS:
    y = np.array([r["flip"] for r in records[c]])
    z = np.array([r["caution_dist_z"] for r in records[c]])
    da, signed = auroc_dir(y, z)
    anomaly[c] = {"n": len(y), "n_flip": int(y.sum()),
                  "auroc_z_dir": da, "auroc_z_signed": signed}


# ---------------------------------------------------------------- CV helper
def cv_auroc_scalar(x, y, n_repeats=CV_REPEATS):
    """Repeated stratified CV AUROC for a single scalar predictor.
    A 1-D scalar has no fit; we just rank on held-out folds using the raw scalar,
    orienting the sign on the TRAIN fold to avoid leakage. Returns mean, std, and
    a pooled direction-agnostic AUROC for reference."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=int)
    rskf = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=n_repeats,
                                   random_state=SEED)
    aucs = []
    for tr, te in rskf.split(x.reshape(-1, 1), y):
        if len(set(y[tr].tolist())) < 2 or len(set(y[te].tolist())) < 2:
            continue
        # orient using train fold only
        a_tr = roc_auc_score(y[tr], x[tr])
        sign = 1.0 if a_tr >= 0.5 else -1.0
        aucs.append(roc_auc_score(y[te], sign * x[te]))
    if not aucs:
        return None
    return {"cv_auroc_mean": round(float(np.mean(aucs)), 4),
            "cv_auroc_std": round(float(np.std(aucs)), 4),
            "n_folds": len(aucs)}


def cv_auroc_matrix(X, y, n_comp=N_PCA, n_repeats=CV_REPEATS, C=1.0):
    """Repeated stratified CV AUROC for a matrix predictor via PCA(fit on train) +
    saga logistic. Returns mean/std over held-out folds."""
    X = np.asarray(X, dtype=np.float64); y = np.asarray(y, dtype=int)
    rskf = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=n_repeats,
                                   random_state=SEED)
    aucs = []
    for tr, te in rskf.split(X, y):
        if len(set(y[tr].tolist())) < 2 or len(set(y[te].tolist())) < 2:
            continue
        k = min(n_comp, X[tr].shape[0] - 1, X.shape[1])
        pca = PCA(n_components=k, svd_solver="randomized", random_state=SEED)
        Ztr = pca.fit_transform(X[tr])
        Zte = pca.transform(X[te])
        mu = Ztr.mean(0); sd = Ztr.std(0) + 1e-6
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=3000, C=C)
        clf.fit((Ztr - mu) / sd, y[tr])
        p = clf.predict_proba((Zte - mu) / sd)[:, 1]
        aucs.append(roc_auc_score(y[te], p))
    if not aucs:
        return None
    return {"cv_auroc_mean": round(float(np.mean(aucs)), 4),
            "cv_auroc_std": round(float(np.std(aucs)), 4),
            "n_folds": len(aucs)}


def perm_null_scalar(x, y, n_perm=N_PERM):
    """Permutation null for a scalar predictor: shuffle y, recompute pooled dir-AUROC."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=int)
    obs, _ = auroc_dir(y, x)
    null = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        a, _s = auroc_dir(yp, x)
        null.append(a)
    null = np.array(null)
    p = float((np.sum(null >= obs) + 1) / (n_perm + 1))
    return {"obs_dir_auroc": obs,
            "perm_mean": round(float(null.mean()), 4),
            "perm_p95": round(float(np.quantile(null, 0.95)), 4),
            "perm_p": round(p, 4)}


def perm_null_matrix(X, y, n_perm=40):
    """Cheaper permutation null for the matrix probe (CV is expensive).
    Uses fewer repeats per permutation."""
    obs = cv_auroc_matrix(X, y, n_repeats=CV_REPEATS)["cv_auroc_mean"]
    null = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        r = cv_auroc_matrix(X, yp, n_repeats=3)
        if r:
            null.append(r["cv_auroc_mean"])
    null = np.array(null)
    p = float((np.sum(null >= obs) + 1) / (len(null) + 1))
    return {"obs_cv_auroc": obs,
            "perm_mean": round(float(null.mean()), 4),
            "perm_p95": round(float(np.quantile(null, 0.95)), 4),
            "perm_p": round(p, 4), "n_perm": len(null)}


# ================================================================ MAIN
findings = {
    "seed": SEED,
    "flip_definition": ("eligible = A0 refused; flip = A0 refused AND Acertain answered; "
                        "modeled within flavor on eligible rows (identical to "
                        "pliability_analysis.py release/uptake)."),
    "flip_counts": flip_counts,
    "anomaly_reproduction": anomaly,
    "cache_join": {
        "note": "eligible controversial rows with cache activations",
        "controversial_elig": flip_counts["controversial"]["n_elig"],
        "controversial_cache_missing": flip_counts["controversial"]["n_cache_missing"],
    },
}

# ---- focal flavor: controversial ----
C = "controversial"
recs = records[C]
y = np.array([r["flip"] for r in recs])
cache_ok = np.array([r["cache_idx"] is not None for r in recs])
print(f"controversial n={len(y)} flips={int(y.sum())} cache_ok={int(cache_ok.sum())}",
      flush=True)

cand = {}

# (a) frozen knowledge probes (unknown-score = 1 - p_known) + precomputed score_L24
print("=== (a) frozen knowledge probes ===", flush=True)
# precomputed score_L24 straight from gen rows (no cache needed)
sL24 = np.array([r["score_L24"] for r in recs])
cand["score_L24_precomputed"] = {
    "cv": cv_auroc_scalar(sL24, y),
    "perm": perm_null_scalar(sL24, y),
}
# also caution_dist_z as the baseline anomaly predictor, for the ranked table
zc = np.array([r["caution_dist_z"] for r in recs])
cand["caution_dist_z"] = {
    "cv": cv_auroc_scalar(zc, y),
    "perm": perm_null_scalar(zc, y),
}
# frozen probes require cache activations; restrict to cache_ok rows
idx_ok = np.where(cache_ok)[0]
cache_idx_arr = np.array([recs[i]["cache_idx"] for i in idx_ok])
y_ok = y[idx_ok]
for L in PROBE_LAYERS:
    obj = joblib.load(os.path.join(PROBES, f"probe_L{L}.joblib"))
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    Xc = X[cache_idx_arr]
    p_known = obj["clf"].predict_proba(obj["scaler"].transform(Xc))[:, 1]
    p_unknown = 1.0 - p_known
    cand[f"knowprobe_unknown_L{L}"] = {
        "cv": cv_auroc_scalar(p_unknown, y_ok),
        "perm": perm_null_scalar(p_unknown, y_ok),
        "n": int(len(y_ok)),
    }
    del X
    print(f"  L{L} knowprobe done", flush=True)

# (b) projection onto per-flavor residual directions (built from cache, layer-swept
#     but we build directions at each PROBE_LAYER for interpretability + specificity).
#     residual dir(c) = (mean_c - mean_known) projected off pooled_cat doubt trunk.
print("=== (b) residual/trunk projections ===", flush=True)
man_label = np.array([1 if r["label"] == "unknown" else 0 for r in man])
man_cat = np.array([r["category_canon"] for r in man])
known_idx_cache = np.where(man_label == 0)[0]
cat_idx_cache = {c: np.where((man_label == 1) & (man_cat == c))[0] for c in CATS}

resid_proj = {}
for L in PROBE_LAYERS:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    mu_k = X[known_idx_cache].mean(0)
    all_cat = np.concatenate([cat_idx_cache[c] for c in CATS])
    pooled = X[all_cat].mean(0) - mu_k
    u = pooled / (np.linalg.norm(pooled) + 1e-12)               # shared trunk (unit)
    dirs = {}
    resids = {}
    for c in CATS:
        d = X[cat_idx_cache[c]].mean(0) - mu_k
        dirs[c] = d
        r = d - (d @ u) * u
        resids[c] = r / (np.linalg.norm(r) + 1e-12)
    # score controversial eligible rows on each direction; AUROC to controversial flip
    Xc = X[cache_idx_arr]
    layer_rec = {}
    # trunk
    s_trunk = Xc @ u
    layer_rec["trunk"] = {"cv": cv_auroc_scalar(s_trunk, y_ok),
                          "perm": perm_null_scalar(s_trunk, y_ok)}
    for c in CATS:
        s = Xc @ resids[c]
        tag = "controversial_residual" if c == C else f"residual_{c}"
        layer_rec[tag] = {"cv": cv_auroc_scalar(s, y_ok),
                          "perm": perm_null_scalar(s, y_ok)}
    resid_proj[f"L{L}"] = layer_rec
    del X
    print(f"  L{L} residual projections done", flush=True)
cand["_residual_projections_by_layer"] = resid_proj

# (c) direct within-controversial activation probe: PCA-128 + saga, layer sweep
print("=== (c) direct activation probe layer sweep ===", flush=True)
act_probe = {}
for L in SWEEP_LAYERS:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    Xc = X[cache_idx_arr]
    cvr = cv_auroc_matrix(Xc, y_ok)
    act_probe[f"L{L}"] = {"cv": cvr, "n": int(len(y_ok))}
    del X
    print(f"  L{L} act-probe cv={cvr}", flush=True)
# permutation null only for the best sweep layer (expensive)
best_L = max(act_probe, key=lambda k: act_probe[k]["cv"]["cv_auroc_mean"])
print(f"  best act layer {best_L}; running perm null", flush=True)
Xb = np.load(os.path.join(CACHE, f"{best_L}.npy")).astype(np.float64)[cache_idx_arr]
act_probe[best_L]["perm"] = perm_null_matrix(Xb, y_ok, n_perm=40)
del Xb
cand["_direct_activation_probe"] = {"by_layer": act_probe, "best_layer": best_L}

# (d) cheap surface features
print("=== (d) surface/text features ===", flush=True)
qs = [r["question"] for r in recs]
qlen_char = np.array([len(q) for q in qs], dtype=float)
qlen_word = np.array([len(q.split()) for q in qs], dtype=float)
q_marks = np.array([q.count("?") for q in qs], dtype=float)
has_or = np.array([1.0 if re.search(r"\bor\b", q.lower()) else 0.0 for q in qs])
surface = {}
for name, x in [("q_len_chars", qlen_char), ("q_len_words", qlen_word),
                ("q_question_marks", q_marks), ("q_has_or", has_or)]:
    surface[name] = {"cv": cv_auroc_scalar(x, y), "perm": perm_null_scalar(x, y)}
# TF-IDF + logistic, proper CV
def cv_tfidf(qs, y, n_repeats=CV_REPEATS):
    y = np.asarray(y)
    rskf = RepeatedStratifiedKFold(n_splits=CV_SPLITS, n_repeats=n_repeats,
                                   random_state=SEED)
    qs = np.array(qs, dtype=object)
    aucs = []
    for tr, te in rskf.split(qs, y):
        if len(set(y[tr].tolist())) < 2 or len(set(y[te].tolist())) < 2:
            continue
        pipe = make_pipeline(
            TfidfVectorizer(min_df=2, ngram_range=(1, 2), sublinear_tf=True),
            LogisticRegression(solver="saga", tol=1e-3, max_iter=3000, C=1.0))
        pipe.fit(qs[tr].tolist(), y[tr])
        p = pipe.predict_proba(qs[te].tolist())[:, 1]
        aucs.append(roc_auc_score(y[te], p))
    return {"cv_auroc_mean": round(float(np.mean(aucs)), 4),
            "cv_auroc_std": round(float(np.std(aucs)), 4), "n_folds": len(aucs)}
tfidf_obs = cv_tfidf(qs, y)
# permutation null (cheap repeats)
tfidf_null = []
for _ in range(30):
    tfidf_null.append(cv_tfidf(qs, rng.permutation(y), n_repeats=2)["cv_auroc_mean"])
tfidf_null = np.array(tfidf_null)
surface["tfidf_logistic"] = {
    "cv": tfidf_obs,
    "perm": {"perm_mean": round(float(tfidf_null.mean()), 4),
             "perm_p95": round(float(np.quantile(tfidf_null, 0.95)), 4),
             "perm_p": round(float((np.sum(tfidf_null >= tfidf_obs["cv_auroc_mean"]) + 1)
                                   / (len(tfidf_null) + 1)), 4)}}
cand["_surface_features"] = surface

findings["controversial_predictors"] = cand

# ---------------------------------------------------------------- (3) specificity
# Rerun the leading predictors on the OTHER flavors' flips. The knowledge probe and
# the score_L24 need cache; residual projections use each flavor's OWN residual and
# the controversial residual (does the controversial residual predict OTHER flavors?).
print("=== specificity across flavors ===", flush=True)
spec = {}
# precompute controversial residual dir at each probe layer for cross-flavor scoring
for c in CATS:
    r_c = records[c]
    yc = np.array([r["flip"] for r in r_c])
    ok = np.array([r["cache_idx"] is not None for r in r_c])
    cidx = np.array([r["cache_idx"] for r in r_c if r["cache_idx"] is not None])
    yok = yc[ok]
    spec[c] = {"n": len(yc), "n_flip": int(yc.sum()),
               "score_L24": cv_auroc_scalar(np.array([r["score_L24"] for r in r_c]), yc),
               "caution_dist_z": cv_auroc_scalar(
                   np.array([r["caution_dist_z"] for r in r_c]), yc),
               "by_layer": {}}
    for L in PROBE_LAYERS:
        X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
        mu_k = X[known_idx_cache].mean(0)
        all_cat = np.concatenate([cat_idx_cache[cc] for cc in CATS])
        u = (X[all_cat].mean(0) - mu_k)
        u = u / (np.linalg.norm(u) + 1e-12)
        d_contr = X[cat_idx_cache["controversial"]].mean(0) - mu_k
        r_contr = d_contr - (d_contr @ u) * u
        r_contr = r_contr / (np.linalg.norm(r_contr) + 1e-12)
        obj = joblib.load(os.path.join(PROBES, f"probe_L{L}.joblib"))
        Xc = X[cidx]
        p_unknown = 1.0 - obj["clf"].predict_proba(obj["scaler"].transform(Xc))[:, 1]
        s_contr_res = Xc @ r_contr
        spec[c]["by_layer"][f"L{L}"] = {
            "knowprobe_unknown": cv_auroc_scalar(p_unknown, yok),
            "controversial_residual_proj": cv_auroc_scalar(s_contr_res, yok),
        }
        del X
    print(f"  {c} specificity done", flush=True)
findings["specificity"] = spec

with open(os.path.join(HERE, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings.json", flush=True)
