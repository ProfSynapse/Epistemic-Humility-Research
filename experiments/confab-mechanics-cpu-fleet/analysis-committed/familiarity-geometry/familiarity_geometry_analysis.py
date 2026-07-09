"""Internal familiarity direction: geometry + information (Amendment AK prep).

Arm B (mi_confab_signature_20260704) found that at matched caution boundary
distance and matched flavor, pre-generation activations predict confab-vs-refuse
on unanswerable questions at AUROC 0.834 (the "commitment direction", peaks
L24-28, cos 0.32 to the doubt trunk). TEXT-side familiarity proxies (corpus
frequencies) predict the same contrast at 0.682.

THIS SCRIPT: what is the INTERNAL familiarity direction geometrically, and does
the commitment direction reduce to it?

  1. Fit an internal familiarity direction: Ridge-regress the continuous
     text-familiarity score onto activations (PCA-128 -> ridge -> lift back to
     full 2560-dim). L20/24/28.
  2. Geometry: whitened cosines between the familiarity direction and
       (a) the doubt trunk (geometry-cache unknown-minus-known),
       (b) the caution axis (knowledge-probe coefficient direction),
       (c) the arm-B commitment direction (matched confab-minus-refuse mean).
  3. Information: (a) internal-familiarity projection AUROC on matched set vs the
     0.682 text proxies and the 0.834 commitment probe; (b) residualize the
     matched activations on the internal-familiarity direction and re-run the
     commitment probe -> how much of 0.834 survives; (c) permutation nulls
     (n=100) for the headline numbers, best layer only.
  4. Verdict: is the commitment direction (i) mostly familiarity, (ii) partially,
     or (iii) largely independent.

CPU only. One layer at a time. Seed 20260704. Direct row_key join (no ah::/ahx::
prefix normalization). Leak-free CV: all learned transforms fit on train fold.
"""
import warnings
warnings.filterwarnings("ignore")
import os
os.environ.setdefault("OMP_NUM_THREADS", "6")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "6")
os.environ.setdefault("MKL_NUM_THREADS", "6")
import json
import re
import math
from pathlib import Path
import numpy as np
from collections import Counter
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.decomposition import PCA
from sklearn.metrics import roc_auc_score
import joblib

SEED = 20260704
BASE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[4]
LEGACY_ANALYSIS = REPO / "experiment" / "phase1" / "probe" / "analysis"
GEOM = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704")
CACHE = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704" / "cache")
PROBES = str(LEGACY_ANALYSIS / "ah_stage0" / "probes")
A0 = str(LEGACY_ANALYSIS / "ah_main" / "gen_A0" / "rows.jsonl")
ARM_B_FINDINGS = (
    REPO / "experiments" / "confab-mechanics-cpu-fleet" / "analysis-committed"
    / "confab-signature" / "findings.json"
)

LAYERS = [20, 24, 28]
PCA_DIM = 128
N_REPEAT = 10
N_SPLITS = 5
N_PERM = 100
CALIPER = 0.20

GEOM_CATS = ["ambiguous", "controversial", "counterfactual",
             "false_assumption", "future_unknown", "unsolved_problem"]

findings = {"seed": SEED, "config": {
    "pca_dim": PCA_DIM, "cv": f"{N_REPEAT}x{N_SPLITS}", "n_perm": N_PERM,
    "caliper_z": CALIPER, "layers": LAYERS,
    "join": "direct row_key (no ah::/ahx:: normalization)",
    "familiarity_target": "mean_log_freq (continuous corpus log-frequency)"}}


# ---------- population (arm-B verbatim) ----------
rows = [json.loads(l) for l in open(A0)]
pop = [r for r in rows if r["gold_class"] == "unanswerable"
       and not r["degenerate"] and not r["ungradeable"]]
for r in pop:
    r["_y"] = 1 if r["confab_on_unanswerable"] else 0
CATS = sorted(set(r["category_canon"] for r in pop))

# ---------- cache join (DIRECT, arm-B verbatim) ----------
man = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
man_idx = {m["row_key"]: i for i, m in enumerate(man)}
work = [r for r in pop if r["row_key"] in man_idx]
assert len(work) == len(pop), f"join dropped rows: {len(work)}/{len(pop)}"
y = np.array([r["_y"] for r in work])
cat = np.array([r["category_canon"] for r in work])
z = np.array([r["caution_dist_z"] for r in work], dtype=np.float64)
cidx = np.array([man_idx[r["row_key"]] for r in work])
questions = [r["question"] for r in work]

man_label = np.array([1 if m["label"] == "unknown" else 0 for m in man])
man_cat = np.array([m["category_canon"] for m in man])


# ---------- familiarity proxies (arm-B verbatim feature defs) ----------
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
# continuous familiarity target = mean_log_freq (strongest continuous proxy in
# arm B: residualised 0.566). Higher = more familiar (frequent) tokens.
FAM_TARGET_IDX = 1


# ---------- matched design (arm-B verbatim, same seed -> same 328 rows) ----------
rng = np.random.default_rng(SEED)
matched_rows = []
for c in CATS:
    ci = np.where(cat == c)[0]
    conf = ci[y[ci] == 1]; refu = ci[y[ci] == 0]
    if len(conf) == 0 or len(refu) == 0:
        continue
    used = set(); pairs = []; refu_z = z[refu]
    for ii in conf:
        d = np.abs(refu_z - z[ii]); order = np.argsort(d); picked = None
        for o in order:
            if d[o] > CALIPER:
                break
            if refu[o] not in used:
                picked = refu[o]; used.add(refu[o]); break
        if picked is not None:
            pairs.append((ii, picked))
    matched_rows.extend([p[0] for p in pairs])
    matched_rows.extend([p[1] for p in pairs])
matched_rows = np.array(sorted(matched_rows))
M = len(matched_rows)
ym = y[matched_rows]; catm = cat[matched_rows]
zm = z[matched_rows]; cidxm = cidx[matched_rows]
q_m = [questions[i] for i in matched_rows]
MREF = sorted(set(catm))[1:]
famv_m = np.array([fam_feats(q)[FAM_TARGET_IDX] for q in q_m], dtype=np.float64)
FAMm_all = np.array([fam_feats(q) for q in q_m], dtype=np.float64)
findings["matched_design"] = {"n_matched_total": int(M),
                              "n_confab": int(ym.sum()),
                              "n_refused": int((1 - ym).sum())}
print(f"MATCHED M={M} confab={int(ym.sum())} refused={int((1-ym).sum())}", flush=True)


def summ(a):
    a = np.asarray(a, dtype=float)
    return {"mean": round(float(np.mean(a)), 4), "std": round(float(np.std(a)), 4),
            "n": int(len(a))}


def onehot_flavor(catv, ref_cats):
    return np.hstack([(catv == c).astype(float).reshape(-1, 1) for c in ref_cats])


def make_confound(zv, catv, ref):
    return np.hstack([zv.reshape(-1, 1), onehot_flavor(catv, ref)])


def residualise_split(F, tr, te, zv, catv, ref):
    Ctr = make_confound(zv[tr], catv[tr], ref)
    Cte = make_confound(zv[te], catv[te], ref)
    lr = LinearRegression().fit(Ctr, F[tr])
    Rtr = F[tr] - lr.predict(Ctr)
    Rte = F[te] - lr.predict(Cte)
    sc = StandardScaler().fit(Rtr)
    return sc.transform(Rtr), sc.transform(Rte)


def repeated_cv(build, yy, n_repeat=N_REPEAT, n_splits=N_SPLITS, clf_factory=None):
    if clf_factory is None:
        clf_factory = lambda: LogisticRegression(max_iter=3000, C=1.0)
    idx = np.arange(len(yy)); aurocs = []
    for rep in range(n_repeat):
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True,
                              random_state=SEED + rep)
        oof = np.full(len(yy), np.nan)
        for tr, te in skf.split(idx, yy):
            ftr, fte = build(tr, te)
            clf = clf_factory(); clf.fit(ftr, yy[tr])
            oof[te] = clf.predict_proba(fte)[:, 1]
        aurocs.append(roc_auc_score(yy, oof))
    return np.array(aurocs)


def perm_test(build, yy, clf_factory=None, n_perm=N_PERM, n_repeat=3):
    obs = float(repeated_cv(build, yy, n_repeat=n_repeat, clf_factory=clf_factory).mean())
    prng = np.random.default_rng(SEED + 999); perms = []
    for _ in range(n_perm):
        yp = prng.permutation(yy)
        perms.append(float(repeated_cv(build, yp, n_repeat=n_repeat,
                                       clf_factory=clf_factory).mean()))
    perms = np.array(perms)
    p = float((np.sum(perms >= obs) + 1) / (n_perm + 1))
    return {"obs": round(obs, 4), "perm_mean": round(float(perms.mean()), 4),
            "perm_p95": round(float(np.quantile(perms, 0.95)), 4), "perm_p": round(p, 4)}


saga = lambda: LogisticRegression(max_iter=3000, C=0.5, solver="lbfgs")


# =====================================================================
# Per-layer: fit internal familiarity direction, geometry, information.
# =====================================================================
def fit_fam_direction_fullspace(Xfull_std, fam_target, pca):
    """Ridge (PCA-128) of continuous familiarity onto activations; lift the
    component-space coefficients back to the standardized full 2560-dim space.
    Returns a unit direction in standardized activation space."""
    P = pca.transform(Xfull_std)
    ridge = Ridge(alpha=10.0).fit(P, fam_target)
    # w_full_std = V^T @ w_pca  (PCA components_ maps std-space -> comp-space)
    w_full = pca.components_.T @ ridge.coef_
    n = np.linalg.norm(w_full)
    return w_full / (n + 1e-12), ridge


def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


layer_out = {}
best_layer, best_survive_auroc = None, None
per_layer_cache = {}

for L in LAYERS:
    X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
    # --- standardizer fit on FULL geometry cache (label-agnostic) ---
    sc_full = StandardScaler().fit(X)
    Xstd = sc_full.transform(X)
    # --- whitening scale = per-dim std (diagonal whitening) ---
    whiten = 1.0 / (sc_full.scale_ + 1e-12)  # multiply raw-space vec by this

    # --- PCA-128 on FULL geometry cache, once per layer (label-agnostic) ---
    pca = PCA(n_components=PCA_DIM, random_state=SEED).fit(Xstd)

    # --- doubt trunk (raw space): unknown(all cats) mean - known mean ---
    mu_k = X[man_label == 0].mean(0)
    allc = np.concatenate([np.where((man_label == 1) & (man_cat == c))[0]
                           for c in GEOM_CATS])
    trunk_raw = X[allc].mean(0) - mu_k

    # --- caution axis (raw space): knowledge-probe coefficient direction.
    # probe operates on standardized inputs; lift coef back to raw space. ---
    caution_raw = None
    ppath = os.path.join(PROBES, f"probe_L{L}.joblib")
    if os.path.exists(ppath):
        po = joblib.load(ppath)
        # decision boundary normal in raw space = coef / probe_scaler.scale_
        caution_raw = (po["clf"].coef_.ravel() / (po["scaler"].scale_ + 1e-12))

    # --- commitment direction (raw space): matched confab mean - refuse mean ---
    Xm_raw = X[cidxm]
    commit_raw = Xm_raw[ym == 1].mean(0) - Xm_raw[ym == 0].mean(0)

    # --- internal familiarity direction (standardized space) ---
    # fit on matched-set activations regressed onto continuous familiarity.
    Xm_std = sc_full.transform(Xm_raw)
    fam_dir_std, _ = fit_fam_direction_fullspace(Xm_std, famv_m, pca)
    # raw-space equivalent for whitened-cosine parity with others:
    fam_dir_raw = fam_dir_std * whiten  # std-space unit -> raw-space vector

    # ---------- whitened cosines ----------
    # whitened vector = raw_vec * whiten (diagonal). Compare in whitened space.
    def wcos(a_raw, b_raw):
        return round(cos(a_raw * whiten, b_raw * whiten), 4)

    cosine_matrix = {
        "familiarity_vs_doubt_trunk": wcos(fam_dir_raw, trunk_raw),
        "familiarity_vs_commitment": wcos(fam_dir_raw, commit_raw),
        "commitment_vs_doubt_trunk": wcos(commit_raw, trunk_raw),
    }
    if caution_raw is not None:
        cosine_matrix["familiarity_vs_caution_axis"] = wcos(fam_dir_raw, caution_raw)
        cosine_matrix["commitment_vs_caution_axis"] = wcos(commit_raw, caution_raw)
        cosine_matrix["caution_axis_vs_doubt_trunk"] = wcos(caution_raw, trunk_raw)

    # ---------- information: internal-familiarity projection AUROC ----------
    # leak-free: refit fam direction inside folds (PCA fixed/label-agnostic ok,
    # but ridge target is text not label so no leakage; still refit for rigor),
    # residualise the 1-D projection vs z+flavor in-fold.
    def build_famproj(tr, te):
        fdir, _ = fit_fam_direction_fullspace(Xm_std[tr], famv_m[tr], pca)
        proj = (Xm_std @ fdir).reshape(-1, 1)
        return residualise_split(proj, tr, te, zm, catm, MREF)
    cv_famproj = repeated_cv(build_famproj, ym)
    raw_famproj_auroc = roc_auc_score(
        ym, (Xm_std @ fam_dir_std))
    raw_famproj_auroc = max(raw_famproj_auroc, 1 - raw_famproj_auroc)

    # ---------- information: commitment probe with fam direction removed ----------
    # residualise activations on the internal familiarity direction (project out),
    # THEN run the PCA-128 -> residualise(z+flavor) -> saga commitment probe.
    def project_out(Xa_std, fdir):
        return Xa_std - np.outer(Xa_std @ fdir, fdir)

    def build_commit_full(tr, te):
        pca_f = PCA(n_components=min(PCA_DIM, len(tr) - 1), random_state=SEED)
        Ptr = pca_f.fit_transform(Xm_std[tr]); Pte = pca_f.transform(Xm_std[te])
        P = np.empty((M, Ptr.shape[1])); P[tr] = Ptr; P[te] = Pte
        return residualise_split(P, tr, te, zm, catm, MREF)

    def build_commit_famout(tr, te):
        fdir, _ = fit_fam_direction_fullspace(Xm_std[tr], famv_m[tr], pca)
        Xres = project_out(Xm_std, fdir)
        pca_f = PCA(n_components=min(PCA_DIM, len(tr) - 1), random_state=SEED)
        Ptr = pca_f.fit_transform(Xres[tr]); Pte = pca_f.transform(Xres[te])
        P = np.empty((M, Ptr.shape[1])); P[tr] = Ptr; P[te] = Pte
        return residualise_split(P, tr, te, zm, catm, MREF)

    cv_commit_full = repeated_cv(build_commit_full, ym, clf_factory=saga)
    cv_commit_famout = repeated_cv(build_commit_famout, ym, clf_factory=saga)

    entry = {
        "cosine_matrix_whitened": cosine_matrix,
        "internal_familiarity_projection": {
            "raw_auroc_abs": round(float(raw_famproj_auroc), 4),
            "residualised_cv": summ(cv_famproj)},
        "commitment_probe_full_cv": summ(cv_commit_full),
        "commitment_probe_familiarity_removed_cv": summ(cv_commit_famout),
        "survival_delta": round(float(cv_commit_famout.mean()
                                      - cv_commit_full.mean()), 4),
    }
    layer_out[f"L{L}"] = entry
    per_layer_cache[L] = dict(build_famproj=build_famproj,
                              build_commit_full=build_commit_full,
                              build_commit_famout=build_commit_famout)
    print(f"L{L} cos={cosine_matrix} "
          f"famproj_res={entry['internal_familiarity_projection']['residualised_cv']['mean']} "
          f"commit_full={entry['commitment_probe_full_cv']['mean']} "
          f"commit_famout={entry['commitment_probe_familiarity_removed_cv']['mean']}",
          flush=True)
    del X, Xstd

    if best_survive_auroc is None or entry["commitment_probe_full_cv"]["mean"] > best_survive_auroc:
        best_survive_auroc = entry["commitment_probe_full_cv"]["mean"]
        best_layer = L

findings["by_layer"] = layer_out
findings["best_layer"] = f"L{best_layer}"

# ---------- permutation nulls on best layer only ----------
pc = per_layer_cache[best_layer]
perm_famproj = perm_test(pc["build_famproj"], ym, n_perm=N_PERM)
perm_commit_full = perm_test(pc["build_commit_full"], ym, clf_factory=saga, n_perm=N_PERM)
perm_commit_famout = perm_test(pc["build_commit_famout"], ym, clf_factory=saga, n_perm=N_PERM)
findings["permutation_best_layer"] = {
    "layer": f"L{best_layer}",
    "familiarity_projection": perm_famproj,
    "commitment_probe_full": perm_commit_full,
    "commitment_probe_familiarity_removed": perm_commit_famout,
}
print("PERM famproj", perm_famproj, flush=True)
print("PERM commit_full", perm_commit_full, flush=True)
print("PERM commit_famout", perm_commit_famout, flush=True)

# ---------- reference numbers from arm B ----------
armB = json.load(open(ARM_B_FINDINGS))
findings["armB_reference"] = {
    "commitment_probe_L28": armB["activation_probe_matched"]["by_layer"]["L28"]["cv"]["mean"],
    "text_familiarity_proxies_joint": armB["familiarity_proxies_matched"]["_joint_all5"]["cv"]["mean"],
    "matched_scalar_floor_note": "matched null ~0.50; single-scalar residualised "
                                 "proxies floor ~0.53-0.59.",
}

# ---------- verdict ----------
bl = layer_out[f"L{best_layer}"]
wc_fam_commit = bl["cosine_matrix_whitened"]["familiarity_vs_commitment"]
full = bl["commitment_probe_full_cv"]["mean"]
famout = bl["commitment_probe_familiarity_removed_cv"]["mean"]
famproj = bl["internal_familiarity_projection"]["residualised_cv"]["mean"]
floor = 0.53
survive_frac = (famout - floor) / (full - floor) if full > floor else 0.0

if abs(wc_fam_commit) > 0.7 and famout <= floor + 0.03:
    verdict = "(i) mostly familiarity"
elif abs(wc_fam_commit) > 0.35 or famout < full - 0.05:
    verdict = "(ii) partially familiarity"
else:
    verdict = "(iii) largely independent"

findings["verdict"] = {
    "code": verdict,
    "best_layer": f"L{best_layer}",
    "whitened_cos_familiarity_vs_commitment": wc_fam_commit,
    "commitment_full_auroc": full,
    "commitment_familiarity_removed_auroc": famout,
    "internal_familiarity_projection_auroc": famproj,
    "survival_fraction_above_floor": round(float(survive_frac), 3),
    "floor_assumed": floor,
}
print("VERDICT", findings["verdict"], flush=True)

with open(os.path.join(BASE, "findings.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings.json", flush=True)
