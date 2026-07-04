"""Confab-vs-refuse signature hunt (arm B, hallucination-mechanics fleet).

Research question: On unanswerable questions the model sometimes confabulates
and sometimes refuses. Session 0036 + item 22a established the decision is
largely ONE shared doubt/caution axis passed through flavor-specific thresholds.
THE HUNT: at matched caution boundary distance and matched flavor, is there ANY
pre-generation signal that predicts which unknowns get confabulated vs refused?

Two clean outcomes:
  (a) nothing beats the matched null  -> threshold event (strong null claim)
  (b) something survives              -> a commitment signal (GPU follow-up)

Tier-1 lab notebook. CPU only. Load one layer at a time. Seed 20260704.

Population: A0 rows, gold_class == 'unanswerable', not degenerate/ungradeable.
Label: confab_on_unanswerable (True=confab, False=refused); complementary here.
Pre-gen activations: mi_category_geometry_20260704/cache. Join by row_key AS-IS
  (the manifest carries both 'ah::' and 'ahx::' forms; direct join = 1338/1338).

METHOD NOTES (leakage discipline):
  * All learned transforms (PCA, confound residualisation, standardisation,
    TF-IDF, SVD) are FIT ON THE TRAIN FOLD ONLY and applied to the test fold.
  * The classes are near-separated on caution (confab mean z~0.03, refuse ~1.47),
    so the overlap band is thin; the matched design retains only that band.
  * Because within-flavor caliper matching balances flavor by construction, the
    matched null is intercept-only (chance). We ALSO report a full-population
    confound-residualised probe (z + flavor regressed out inside folds) as a
    complementary, higher-n view of the same residual-signal question.
  * Deep layers can encode the imminent answer/refuse DECISION (outcome state),
    not a pre-commitment predictor. We report the full layer profile and flag
    the monotone-with-depth pattern explicitly rather than cherry-picking L34.
"""
import warnings
warnings.filterwarnings("ignore")
import os
# cap BLAS threads: many small in-fold fits thrash otherwise (load>>ncores).
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
import json
import re
import math
import numpy as np
from collections import Counter, defaultdict
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import roc_auc_score
import joblib

SEED = 20260704
BASE = os.path.dirname(os.path.abspath(__file__))
AN = os.path.abspath(os.path.join(BASE, ".."))
GEOM = os.path.join(AN, "mi_category_geometry_20260704")
CACHE = os.path.join(GEOM, "cache")
PROBES = os.path.join(AN, "ah_stage0", "probes")
A0 = os.path.join(AN, "ah_main", "gen_A0", "rows.jsonl")

LAYERS_SWEEP = [8, 16, 20, 24, 28, 34]
PCA_DIM = 128
N_REPEAT = 10
N_SPLITS = 5
N_PERM = 100
CALIPER = 0.20

findings = {"seed": SEED, "config": {
    "pca_dim": PCA_DIM, "cv": f"{N_REPEAT}x{N_SPLITS}",
    "n_perm": N_PERM, "caliper_z": CALIPER,
    "join": "direct row_key (manifest has both ah:: and ahx:: forms)"}}


# ---------- population ----------
rows = [json.loads(l) for l in open(A0)]
pop = [r for r in rows if r["gold_class"] == "unanswerable"
       and not r["degenerate"] and not r["ungradeable"]]
for r in pop:
    r["_y"] = 1 if r["confab_on_unanswerable"] else 0

CATS = sorted(set(r["category_canon"] for r in pop))
pop_tab = {}
for c in CATS:
    sub = [r for r in pop if r["category_canon"] == c]
    pop_tab[c] = {"n": len(sub),
                  "confab": int(sum(r["_y"] for r in sub)),
                  "refused": int(sum(1 - r["_y"] for r in sub))}
findings["population"] = {
    "n_total_A0": len(rows),
    "n_unanswerable_clean": len(pop),
    "n_confab": int(sum(r["_y"] for r in pop)),
    "n_refused": int(sum(1 - r["_y"] for r in pop)),
    "per_flavor": pop_tab,
}

# ---------- cache join (DIRECT) ----------
man = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
man_idx = {m["row_key"]: i for i, m in enumerate(man)}
work = [r for r in pop if r["row_key"] in man_idx]
findings["cache_join"] = {"n_pop": len(pop), "n_joined": len(work),
                          "coverage": round(len(work) / len(pop), 4)}
assert len(work) == len(pop), f"join dropped rows: {len(work)}/{len(pop)}"
y = np.array([r["_y"] for r in work])
cat = np.array([r["category_canon"] for r in work])
z = np.array([r["caution_dist_z"] for r in work], dtype=np.float64)
cidx = np.array([man_idx[r["row_key"]] for r in work])
questions = [r["question"] for r in work]

# caution separation diagnostic
findings["caution_separation"] = {
    "z_confab_mean": round(float(z[y == 1].mean()), 4),
    "z_confab_sd": round(float(z[y == 1].std()), 4),
    "z_refused_mean": round(float(z[y == 0].mean()), 4),
    "z_refused_sd": round(float(z[y == 0].std()), 4),
    "note": "near-separation on caution is why the unmatched null is ~0.96.",
}


def summ(a):
    a = np.asarray(a, dtype=float)
    return {"mean": round(float(np.mean(a)), 4), "std": round(float(np.std(a)), 4),
            "n": int(len(a))}


# =====================================================================
# leak-free repeated CV over a feature-builder callable.
# build(Xtr_raw, ytr, Xte_raw) -> (feat_tr, feat_te) fit on TRAIN only.
# raw feature block here is a tuple of arrays we pass through per split.
# =====================================================================
def repeated_cv(build, raw, yy, n_repeat=N_REPEAT, n_splits=N_SPLITS,
                clf_factory=None, seed=SEED):
    if clf_factory is None:
        clf_factory = lambda: LogisticRegression(max_iter=3000, C=1.0)
    idx = np.arange(len(yy))
    aurocs = []
    for rep in range(n_repeat):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True,
                              random_state=seed + rep)
        oof = np.full(len(yy), np.nan)
        for tr, te in skf.split(idx, yy):
            ftr, fte = build(tr, te)
            clf = clf_factory()
            clf.fit(ftr, yy[tr])
            oof[te] = clf.predict_proba(fte)[:, 1]
        aurocs.append(roc_auc_score(yy, oof))
    return np.array(aurocs)


def perm_test(build, yy, clf_factory=None, n_perm=N_PERM, n_repeat=3, seed=SEED):
    """Permute labels; recompute mean CV AUROC. All fitting stays inside folds.
    obs uses the same n_repeat as the perm draws so the comparison is like-for-like."""
    obs = float(repeated_cv(build, None, yy, n_repeat=n_repeat,
                            clf_factory=clf_factory).mean())
    prng = np.random.default_rng(seed + 999)
    perms = []
    for _ in range(n_perm):
        yp = prng.permutation(yy)
        perms.append(float(repeated_cv(build, None, yp, n_repeat=n_repeat,
                                       clf_factory=clf_factory).mean()))
    perms = np.array(perms)
    p = float((np.sum(perms >= obs) + 1) / (n_perm + 1))
    return {"obs": round(obs, 4), "perm_mean": round(float(perms.mean()), 4),
            "perm_p95": round(float(np.quantile(perms, 0.95)), 4),
            "perm_p": round(p, 4)}


# feature builders operate on module-level arrays via closures over indices.
def onehot_flavor(catv, ref_cats):
    return np.hstack([(catv == c).astype(float).reshape(-1, 1) for c in ref_cats])


# =====================================================================
# 1. NULL MODELS (unmatched, full population): z, z+flavor -> confab
# =====================================================================
ref_cats = sorted(set(cat))[1:]

def build_zonly(tr, te):
    sc = StandardScaler().fit(z[tr].reshape(-1, 1))
    return sc.transform(z[tr].reshape(-1, 1)), sc.transform(z[te].reshape(-1, 1))

def build_zflav(tr, te):
    ztr = z[tr].reshape(-1, 1); zte = z[te].reshape(-1, 1)
    sc = StandardScaler().fit(ztr)
    Ftr = np.hstack([sc.transform(ztr), onehot_flavor(cat[tr], ref_cats)])
    Fte = np.hstack([sc.transform(zte), onehot_flavor(cat[te], ref_cats)])
    return Ftr, Fte

null_z = repeated_cv(build_zonly, None, y)
null_zf = repeated_cv(build_zflav, None, y)
findings["null_model_fullpop"] = {"z_only": summ(null_z), "z_plus_flavor": summ(null_zf)}
print("NULL(full) z", summ(null_z), "z+flav", summ(null_zf), flush=True)


# =====================================================================
# 2. MATCHED DESIGN: within-flavor 1:1 caliper match on z (no replacement).
# =====================================================================
rng = np.random.default_rng(SEED)
matched_rows = []
match_report = {}
for c in CATS:
    ci = np.where(cat == c)[0]
    conf = ci[y[ci] == 1]; refu = ci[y[ci] == 0]
    if len(conf) == 0 or len(refu) == 0:
        match_report[c] = {"n_confab": int(len(conf)), "n_refused": int(len(refu)),
                           "n_matched_pairs": 0}
        continue
    used = set(); pairs = []; refu_z = z[refu]
    order_conf = conf[np.argsort([len(refu)] * len(conf))]  # stable
    for ii in conf:
        d = np.abs(refu_z - z[ii]); order = np.argsort(d); picked = None
        for o in order:
            if d[o] > CALIPER:
                break
            if refu[o] not in used:
                picked = refu[o]; used.add(refu[o]); break
        if picked is not None:
            pairs.append((ii, picked))
    cm = [p[0] for p in pairs]; rm = [p[1] for p in pairs]
    match_report[c] = {
        "n_confab": int(len(conf)), "n_refused": int(len(refu)),
        "n_matched_pairs": len(pairs),
        "z_confab_mean_prematch": round(float(z[conf].mean()), 4),
        "z_refused_mean_prematch": round(float(z[refu].mean()), 4),
        "z_absdiff_postmatch_mean": round(float(np.abs(z[cm] - z[rm]).mean()), 4) if pairs else None,
    }
    matched_rows.extend(cm); matched_rows.extend(rm)

matched_rows = np.array(sorted(matched_rows))
# local index space for the matched set
M = len(matched_rows)
ym = y[matched_rows]; catm = cat[matched_rows]
zm = z[matched_rows]; cidxm = cidx[matched_rows]
q_m = [questions[i] for i in matched_rows]
findings["matched_design"] = {
    "caliper_z": CALIPER, "per_flavor": match_report,
    "n_matched_total": int(M), "n_matched_confab": int(ym.sum()),
    "n_matched_refused": int((1 - ym).sum()),
    "note": "1:1 within-flavor no-replacement; thin overlap band retains few rows.",
}

# balance: z should no longer predict label in matched set
def build_zonly_m(tr, te):
    sc = StandardScaler().fit(zm[tr].reshape(-1, 1))
    return sc.transform(zm[tr].reshape(-1, 1)), sc.transform(zm[te].reshape(-1, 1))
z_m_auroc = repeated_cv(build_zonly_m, None, ym)
findings["matched_design"]["z_predicts_label_postmatch_auroc"] = summ(z_m_auroc)
findings["matched_design"]["matched_null_is_chance"] = (
    "flavor balanced by construction + z balanced by matching -> intercept-only "
    "null = 0.5; any predictor must beat 0.5 AND the permutation null.")
print("MATCHED M", M, "z-postmatch", summ(z_m_auroc), flush=True)


# =====================================================================
# leak-free residualise: fit LinearRegression(features ~ z+flavor) on TRAIN,
# subtract predicted from BOTH train & test. Then standardise on train.
# =====================================================================
def make_confound(zv, catv, ref):
    return np.hstack([zv.reshape(-1, 1), onehot_flavor(catv, ref)])

MREF = sorted(set(catm))[1:]

def residualise_split(F, tr, te, zv, catv, ref):
    Ctr = make_confound(zv[tr], catv[tr], ref)
    Cte = make_confound(zv[te], catv[te], ref)
    lr = LinearRegression().fit(Ctr, F[tr])
    Rtr = F[tr] - lr.predict(Ctr)
    Rte = F[te] - lr.predict(Cte)
    sc = StandardScaler().fit(Rtr)
    return sc.transform(Rtr), sc.transform(Rte)


# =====================================================================
# 2a. DIRECT ACTIVATION PROBE (matched, leak-free): per layer
#     build: PCA(fit train) -> residualise(fit train) -> saga logistic
# =====================================================================
# dense residualised PCA features -> lbfgs converges fast and matches saga here.
saga = lambda: LogisticRegression(max_iter=3000, C=0.5, solver="lbfgs")

def act_build_factory(Xm):
    def build(tr, te):
        pca = PCA(n_components=min(PCA_DIM, len(tr) - 1), random_state=SEED)
        Ptr = pca.fit_transform(Xm[tr]); Pte = pca.transform(Xm[te])
        P = np.empty((M, Ptr.shape[1])); P[tr] = Ptr; P[te] = Pte
        return residualise_split(P, tr, te, zm, catm, MREF)
    return build

# Pass 1: fast CV-only across all layers (no permutation) to find best layer.
act_probe = {}
act_builds = {}
best_layer, best_mean = None, -1
for L in LAYERS_SWEEP:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float32)
    Xm = X[cidxm].astype(np.float64); del X
    build = act_build_factory(Xm)
    act_builds[L] = build
    cv = repeated_cv(build, None, ym, clf_factory=saga)
    act_probe[f"L{L}"] = {"cv": summ(cv)}
    print(f"ACT L{L} cv={summ(cv)}", flush=True)
    if cv.mean() > best_mean:
        best_mean, best_layer = cv.mean(), L
# Pass 2: permutation only on the best layer (the expensive step, run once).
pt = perm_test(act_builds[best_layer], ym, clf_factory=saga)
act_probe[f"L{best_layer}"]["perm"] = pt
print(f"ACT-PERM L{best_layer} p={pt['perm_p']} obs={pt['obs']} pm={pt['perm_mean']}",
      flush=True)
findings["activation_probe_matched"] = {
    "by_layer": act_probe, "best_layer": f"L{best_layer}",
    "perm_note": "permutation test run on best layer only (cost); other layers "
                 "report CV mean/SD.",
}


# =====================================================================
# 2a-complement: FULL-POPULATION residualised activation probe (higher n).
# Same leak-free build on all `work` rows, residualising z+flavor inside folds.
# =====================================================================
FREF = sorted(set(cat))[1:]
Na = len(y)

def full_build_factory(Xa):
    def build(tr, te):
        pca = PCA(n_components=PCA_DIM, random_state=SEED)
        Ptr = pca.fit_transform(Xa[tr]); Pte = pca.transform(Xa[te])
        P = np.empty((Na, Ptr.shape[1])); P[tr] = Ptr; P[te] = Pte
        return residualise_split(P, tr, te, z, cat, FREF)
    return build

act_full = {}
full_builds = {}
best_full_L, best_full_mean = None, -1
for L in [20, 24, 28, 34]:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float32)
    Xa = X[cidx].astype(np.float64); del X
    build = full_build_factory(Xa)
    full_builds[L] = build
    cv = repeated_cv(build, None, y, clf_factory=saga)
    act_full[f"L{L}"] = {"cv": summ(cv)}
    print(f"ACTFULL L{L} cv={summ(cv)}", flush=True)
    if cv.mean() > best_full_mean:
        best_full_mean, best_full_L = cv.mean(), L
pt = perm_test(full_builds[best_full_L], y, clf_factory=saga, n_perm=50)
act_full[f"L{best_full_L}"]["perm"] = pt
print(f"ACTFULL-PERM L{best_full_L} p={pt['perm_p']}", flush=True)
findings["activation_probe_fullpop_residualised"] = {
    "by_layer": act_full, "best_layer": f"L{best_full_L}",
    "perm_note": "permutation on best full-pop layer only."}


# =====================================================================
# 2b. KNOWLEDGE PROBES (frozen L20/24/28) as predictors (matched, leak-free).
# The probe is frozen (no refit); we residualise its score vs z+flavor in-fold.
# =====================================================================
know = {}
know_scores = {}
for L in [20, 24, 28]:
    o = joblib.load(os.path.join(PROBES, f"probe_L{L}.joblib"))
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float32)
    Xm = X[cidxm].astype(np.float64); del X
    s = o["clf"].decision_function(o["scaler"].transform(Xm))  # log-odds known
    know_scores[L] = s

    def build(tr, te, s=s):
        F = s.reshape(-1, 1)
        return residualise_split(F, tr, te, zm, catm, MREF)

    cv = repeated_cv(build, None, ym)
    pt = perm_test(build, ym)
    raw = roc_auc_score(ym, s)
    know[f"L{L}"] = {"known_score_raw_auroc_abs": round(max(raw, 1 - raw), 4),
                     "residualised_cv": summ(cv), "perm": pt}
    print(f"KNOW L{L} raw|auc|={max(raw,1-raw):.3f} cv={summ(cv)} p={pt['perm_p']}",
          flush=True)
findings["knowledge_probe_matched"] = know


# =====================================================================
# 2c. DIRECTION PROJECTIONS (diagnostic). Directions built ONCE from the full
# geometry cache (fixed vectors, not fit to labels), then projected & the
# projection residualised vs z+flavor in-fold. After matching these should be
# ~chance; a positive => matching leaves flavor/trunk structure (diagnostic).
# =====================================================================
man_label = np.array([1 if m["label"] == "unknown" else 0 for m in man])
man_cat = np.array([m["category_canon"] for m in man])
GEOM_CATS = ["ambiguous", "controversial", "counterfactual",
             "false_assumption", "future_unknown", "unsolved_problem"]
proj = {}
for L in [20]:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    mu_k = X[man_label == 0].mean(0)
    allc = np.concatenate([np.where((man_label == 1) & (man_cat == c))[0]
                           for c in GEOM_CATS])
    trunk = X[allc].mean(0) - mu_k
    dirs = {"trunk": trunk}
    for c in GEOM_CATS:
        d = X[np.where((man_label == 1) & (man_cat == c))[0]].mean(0) - mu_k
        dirs[f"{c}_resid"] = d - (d @ trunk) / (trunk @ trunk) * trunk
    Xm = X[cidxm]; del X
    entry = {}
    for name, vec in dirs.items():
        p = (Xm @ vec).reshape(-1, 1)
        def build(tr, te, p=p):
            return residualise_split(p, tr, te, zm, catm, MREF)
        cv = repeated_cv(build, None, ym, n_repeat=5)
        entry[name] = round(float(cv.mean()), 4)
    proj[f"L{L}"] = entry
    print("PROJ L20", entry, flush=True)
findings["direction_projections_matched"] = proj


# =====================================================================
# 2d. FAMILIARITY PROXIES (entity-recognition hypothesis). wordfreq absent ->
# corpus-internal freqs from all A0 questions (fixed, label-agnostic). Feature
# columns residualised vs z+flavor in-fold.
# =====================================================================
tok_re = re.compile(r"[A-Za-z']+")
corpus = Counter()
for r in rows:
    for w in tok_re.findall(r["question"].lower()):
        corpus[w] += 1
tot = sum(corpus.values())

def fam_feats(q):
    toks = tok_re.findall(q.lower()); n = len(toks)
    if n == 0:
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    rare = sum(1 for w in toks if corpus[w] <= 2) / n
    mean_logf = float(np.mean([math.log(corpus[w] / tot + 1e-9) for w in toks]))
    proper = sum(1 for w in q.split()[1:] if re.match(r"^[A-Z][a-z]+", w))
    return [rare, mean_logf, float(proper), float(n), float(len(q))]

FAM_names = ["rare_word_frac", "mean_log_freq", "proper_noun_count",
             "n_tokens", "n_chars"]
FAMm = np.array([fam_feats(q) for q in q_m], dtype=np.float64)
fam = {}
for j, nm in enumerate(FAM_names):
    col = FAMm[:, [j]]
    raw = roc_auc_score(ym, col.ravel()) if len(set(col.ravel())) > 1 else 0.5
    def build(tr, te, col=col):
        return residualise_split(col, tr, te, zm, catm, MREF)
    cv = repeated_cv(build, None, ym)
    fam[nm] = {"raw_auroc_abs": round(max(raw, 1 - raw), 4), "residualised_cv": summ(cv)}

def build_famjoint(tr, te):
    return residualise_split(FAMm, tr, te, zm, catm, MREF)
cvj = repeated_cv(build_famjoint, None, ym)
ptj = perm_test(build_famjoint, ym)
fam["_joint_all5"] = {"cv": summ(cvj), "perm": ptj}
findings["familiarity_proxies_matched"] = fam
print("FAM joint", summ(cvj), "p", ptj["perm_p"], flush=True)


# =====================================================================
# 2e. TF-IDF text baseline (matched, leak-free): fit vectoriser+SVD on train.
# =====================================================================
def build_tfidf(tr, te):
    vec = TfidfVectorizer(max_features=2000, ngram_range=(1, 2),
                          sublinear_tf=True, min_df=2)
    Xtr = vec.fit_transform([q_m[i] for i in tr])
    Xte = vec.transform([q_m[i] for i in te])
    k = min(100, Xtr.shape[1] - 1, len(tr) - 1)
    svd = TruncatedSVD(n_components=max(k, 2), random_state=SEED)
    Ztr = svd.fit_transform(Xtr); Zte = svd.transform(Xte)
    sc = StandardScaler().fit(Ztr)
    return sc.transform(Ztr), sc.transform(Zte)

cv_tf = repeated_cv(build_tfidf, None, ym, clf_factory=saga)
pt_tf = perm_test(build_tfidf, ym, clf_factory=saga)
findings["tfidf_text_baseline_matched"] = {"cv": summ(cv_tf), "perm": pt_tf}
print("TFIDF", summ(cv_tf), "p", pt_tf["perm_p"], flush=True)


# =====================================================================
# 3. INCREMENTAL VALUE (matched): paired CV, base = intercept-only chance is
# trivial; instead compare the best activation layer probe to the text baseline
# and to familiarity, on identical folds. Report paired deltas.
# =====================================================================
Lb = best_layer
Xb = np.load(os.path.join(CACHE, f"L{Lb}.npy")).astype(np.float32)[cidxm].astype(np.float64)

def build_act_best(tr, te):
    pca = PCA(n_components=min(PCA_DIM, len(tr) - 1), random_state=SEED)
    Ptr = pca.fit_transform(Xb[tr]); Pte = pca.transform(Xb[te])
    P = np.empty((M, Ptr.shape[1])); P[tr] = Ptr; P[te] = Pte
    return residualise_split(P, tr, te, zm, catm, MREF)

def paired(bA, bB, yy, fA=saga, fB=saga, n_repeat=N_REPEAT):
    aA, aB = [], []
    for rep in range(n_repeat):
        skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + rep)
        oA = np.full(len(yy), np.nan); oB = np.full(len(yy), np.nan)
        for tr, te in skf.split(np.arange(len(yy)), yy):
            ftr, fte = bA(tr, te); c = fA(); c.fit(ftr, yy[tr]); oA[te] = c.predict_proba(fte)[:, 1]
            gtr, gte = bB(tr, te); c = fB(); c.fit(gtr, yy[tr]); oB[te] = c.predict_proba(gte)[:, 1]
        aA.append(roc_auc_score(yy, oA)); aB.append(roc_auc_score(yy, oB))
    aA, aB = np.array(aA), np.array(aB); d = aA - aB
    return {"A": summ(aA), "B": summ(aB), "delta_mean": round(float(d.mean()), 4),
            "delta_std": round(float(d.std()), 4),
            "delta_frac_A_gt_B": round(float((d > 0).mean()), 3)}

findings["incremental_value_matched"] = {
    "activation_vs_tfidf": paired(build_act_best, build_tfidf, ym),
    "activation_vs_familiarity": paired(build_act_best, build_famjoint, ym, fB=lambda: LogisticRegression(max_iter=3000)),
    "note": "A = best activation layer; positive delta => activation carries "
            "signal beyond text content / familiarity.",
}
print("INCR", findings["incremental_value_matched"]["activation_vs_tfidf"]["delta_mean"],
      findings["incremental_value_matched"]["activation_vs_familiarity"]["delta_mean"], flush=True)


# =====================================================================
# 4. CHARACTERISATION: cosine of matched confab direction (mean confab - mean
# refuse, best layer) to trunk; layer profile already reported; item-22a flip
# cross-check pointer.
# =====================================================================
charac = {}
try:
    X = np.load(os.path.join(CACHE, f"L{Lb}.npy")).astype(np.float64)
    mu_k = X[man_label == 0].mean(0)
    allc = np.concatenate([np.where((man_label == 1) & (man_cat == c))[0] for c in GEOM_CATS])
    trunk_b = X[allc].mean(0) - mu_k
    Xm_b = X[cidxm]; del X
    confab_dir = Xm_b[ym == 1].mean(0) - Xm_b[ym == 0].mean(0)
    cos = lambda a, b: round(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)), 4)
    charac = {"layer": f"L{Lb}", "cos_confabdir_trunk": cos(confab_dir, trunk_b)}
    fl = json.load(open(os.path.join(AN, "mi_controversial_flips_20260704", "findings.json")))
    charac["item22a_flip_probe_best_layer"] = fl["controversial_predictors"][
        "_direct_activation_probe"]["best_layer"]
    charac["item22a_note"] = ("flip = refuse-then-answer under certainty prime "
                              "(controversial only); adjacent commitment axis, "
                              "different label from confab-vs-refuse.")
except Exception as e:
    charac["error"] = repr(e)
findings["characterization"] = charac
print("CHARAC", charac, flush=True)

with open(os.path.join(BASE, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings.json", flush=True)
