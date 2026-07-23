#!/usr/bin/env python3
"""Characterize the L20 controversial-flip direction.

Fits the full-sample L20 PCA-128+saga controversial-flip probe (no CV; direction
characterization only), lifts it back to the 2560-d activation space, and asks:
  - cosine to the shared doubt trunk (pooled_cat mean - known mean)
  - cosine to the controversial residual direction
  - cosine to the caution axis, proxied by the direction that best predicts A0
    baseline refusal among controversial-eligible rows (LDA-style mean diff)
  - does the flip direction ALSO predict baseline refusal, or only prime uptake?
CPU only, one layer.
"""
import json, os, numpy as np
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

SEED = 20260704
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[4]
LEGACY_ANALYSIS = REPO / "archive" / "experiment" / "phase1" / "probe" / "analysis"
GEN = str(LEGACY_ANALYSIS / "ah_main")
CACHE = str(LEGACY_ANALYSIS / "mi_category_geometry_20260704" / "cache")
CATS = ["ambiguous", "controversial", "counterfactual",
        "false_assumption", "future_unknown", "unsolved_problem"]
L = 20

def load(arm):
    return [json.loads(l) for l in open(os.path.join(GEN, f"gen_{arm}", "rows.jsonl"))]
a0 = {r["row_key"]: r for r in load("A0")}
ac = load("Acertain")
man = [json.loads(l) for l in open(os.path.join(CACHE, "manifest.jsonl"))]
key2ci = {r["row_key"]: i for i, r in enumerate(man)}
man_label = np.array([1 if r["label"] == "unknown" else 0 for r in man])
man_cat = np.array([r["category_canon"] for r in man])
known_idx = np.where(man_label == 0)[0]
cat_idx = {c: np.where((man_label == 1) & (man_cat == c))[0] for c in CATS}

# controversial eligible rows
recs = []
for pr in ac:
    b = a0[pr["row_key"]]
    if not b["refused"] or pr["category_canon"] != "controversial":
        continue
    ci = key2ci.get(pr["row_key"])
    if ci is None:
        continue
    recs.append({"ci": ci, "flip": 1 if pr["answered"] else 0})
cidx = np.array([r["ci"] for r in recs]); yflip = np.array([r["flip"] for r in recs])

X = np.load(os.path.join(CACHE, f"L{L}.npy")).astype(np.float64)
mu_k = X[known_idx].mean(0)
all_cat = np.concatenate([cat_idx[c] for c in CATS])
trunk = X[all_cat].mean(0) - mu_k
u = trunk / np.linalg.norm(trunk)
d_contr = X[cat_idx["controversial"]].mean(0) - mu_k
contr_res = d_contr - (d_contr @ u) * u
contr_res /= np.linalg.norm(contr_res)

# full-sample flip probe direction in PCA space, lifted to activation space
Xc = X[cidx]
pca = PCA(n_components=128, svd_solver="randomized", random_state=SEED)
Z = pca.fit_transform(Xc)
mu = Z.mean(0); sd = Z.std(0) + 1e-6
clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=3000)
clf.fit((Z - mu) / sd, yflip)
w_pca = clf.coef_.ravel() / sd
w_act = pca.components_.T @ w_pca           # lift back to 2560-d
w_act /= np.linalg.norm(w_act)

def cos(a, b):
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

# baseline-refusal direction among controversial ALL rows (mean diff refused vs answered)
# gather all controversial A0 rows with cache
b_ci, b_ref = [], []
for rk, r in a0.items():
    if r["category_canon"] != "controversial":
        continue
    ci = key2ci.get(rk)
    if ci is None:
        continue
    b_ci.append(ci); b_ref.append(1 if r["refused"] else 0)
b_ci = np.array(b_ci); b_ref = np.array(b_ref)
Xb = X[b_ci]
ref_dir = Xb[b_ref == 1].mean(0) - Xb[b_ref == 0].mean(0)
ref_dir /= np.linalg.norm(ref_dir)

out = {
    "layer": L,
    "n_controversial_elig": int(len(yflip)),
    "cos_flipdir_trunk": round(cos(w_act, u), 4),
    "cos_flipdir_controversial_residual": round(cos(w_act, contr_res), 4),
    "cos_flipdir_baseline_refusal_dir": round(cos(w_act, ref_dir), 4),
    "cos_trunk_baseline_refusal_dir": round(cos(u, ref_dir), 4),
    # does the flip direction ALSO read baseline refusal (all controversial rows)?
    "flipdir_predicts_baseline_refusal_auroc": round(float(
        max(roc_auc_score(b_ref, Xb @ w_act), 1 - roc_auc_score(b_ref, Xb @ w_act))), 4),
    "trunk_predicts_baseline_refusal_auroc": round(float(
        max(roc_auc_score(b_ref, Xb @ u), 1 - roc_auc_score(b_ref, Xb @ u))), 4),
    "n_controversial_A0_cache": int(len(b_ref)),
    "baseline_refusal_rate_controversial": round(float(b_ref.mean()), 4),
}
with open(os.path.join(HERE, "direction_characterization.json"), "w") as f:
    json.dump(out, f, indent=2)
print(json.dumps(out, indent=2))
