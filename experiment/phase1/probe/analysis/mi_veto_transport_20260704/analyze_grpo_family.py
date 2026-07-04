"""grpo-v2 family (Amendment T + U) mirror of the S/W transport analysis.

T = per-answer correctness (988 correct / 500 wrong), pre+post.
U = veto pool: answerable_attempt (276) vs hallucination (121), pre+post.

Tests, within grpo-v2 family only:
 1. Same-row transport on T: correctness-axis projection pre vs post correlation.
 2. Correctness readable pre vs post (honest CV) + cross-position transfer.
 3. Decomposition on T: post-gen correctness residualized against transported doubt.
 4. OOS veto on U: T-fit correctness dial applied to U (answerable vs hallucination).
"""
import os, json
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
import vt_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(0)
T_DIR = L.T_DIR
U_DIR = L.U_DIR


def residualize(X, s):
    s = (s - s.mean()) / s.std()
    s = s.reshape(-1, 1)
    beta = (X.T @ s).ravel() / (s.T @ s).ravel()[0]
    return X - s @ beta.reshape(1, -1)


def cv_transfer(Xfit, Xeval, y, seed=0, n_splits=5):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    for tr, te in skf.split(Xfit, y):
        fp = L.fit_full_probe(Xfit[tr], y[tr], seed=seed)
        oof[te] = L.score_full_probe(fp, Xeval[te])
    return float(roc_auc_score(y, oof)), oof


def boot_ci(y, s, n=2000):
    aucs = []
    idx = np.arange(len(y))
    for _ in range(n):
        b = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[b])) < 2:
            continue
        aucs.append(roc_auc_score(y[b], s[b]))
    return [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]


findings = {"family": "clean-sft-grpo-v2", "note": "cross-family vs S/W (raw base) is descriptive only"}

# ---- T: load correctness rows with files ----
rowsT_all = L.load_rows(T_DIR)
rowsT = [r for r in rowsT_all if r.get("correct") is not None
         and os.path.exists(L.tensor_path(T_DIR, r["row_key"], "pre"))
         and os.path.exists(L.tensor_path(T_DIR, r["row_key"], "post"))]
yT = np.array([1 if r["correct"] else 0 for r in rowsT])
print("T rows", len(rowsT), "correct", int(yT.sum()), flush=True)

cache = {}
Tpre20, _ = L.load_layer_matrix(T_DIR, rowsT, "pre", 20, cache)
Tpost20, _ = L.load_layer_matrix(T_DIR, rowsT, "post", 20, cache)
Tpre18, _ = L.load_layer_matrix(T_DIR, rowsT, "pre", 18, cache)
Tpost18, _ = L.load_layer_matrix(T_DIR, rowsT, "post", 18, cache)
cache.clear()

# 1. same-row transport: use S-fit cached dial (raw base) as a fixed axis?  No -
#    grpo-v2 direction drifts (cold transfer 0.679). Instead fit a T correctness
#    axis on ALL T (in-sample projection is fine for a CORRELATION of positions).
fp_T = L.fit_full_probe(Tpost20, yT, seed=5)
proj_pre = L.score_full_probe(fp_T, Tpre20)
proj_post = L.score_full_probe(fp_T, Tpost20)
r1 = {}
r, _ = pearsonr(proj_pre, proj_post); rs, _ = spearmanr(proj_pre, proj_post)
r1["Tcorrectness_axis_pre_vs_post_L20"] = {"pearson": float(r), "spearman": float(rs)}
sc = [L.cos(Tpre20[i], Tpost20[i]) for i in range(len(rowsT))]
r1["raw_state_cos_pre_post_L20"] = {"mean": float(np.mean(sc)), "std": float(np.std(sc))}
findings["test1_same_row_T"] = r1
print(json.dumps(r1, indent=2), flush=True)

# 2. correctness pre vs post (honest CV) + transport
auc_post, oof_post = cv_transfer(Tpost20, Tpost20, yT, seed=6)
auc_pre, oof_pre = cv_transfer(Tpre20, Tpre20, yT, seed=6)
auc_prefit_at_post, _ = cv_transfer(Tpre20, Tpost20, yT, seed=6)
auc_postfit_at_pre, _ = cv_transfer(Tpost20, Tpre20, yT, seed=6)
findings["test2_correctness_T"] = {
    "cv_post_L20": auc_post, "cv_post_ci95": boot_ci(yT, oof_post),
    "cv_pre_L20": auc_pre, "cv_pre_ci95": boot_ci(yT, oof_pre),
    "post_beats_pre_delta": auc_post - auc_pre,
    "prefit_applied_at_post": auc_prefit_at_post,
    "postfit_applied_at_pre": auc_postfit_at_pre,
}
print(json.dumps(findings["test2_correctness_T"], indent=2), flush=True)

# 3. decomposition: residualize post L20 against transported doubt (gate axis).
#    Use W-family gate? cross-family. Instead use the T pre-gen correctness proj
#    as the "carried" scalar and see if post survives beyond it.
Tpost20_resid = residualize(Tpost20, proj_pre)
auc_resid, _ = cv_transfer(Tpost20_resid, Tpost20_resid, yT, seed=6)
findings["test3_decomp_T"] = {
    "fresh_post_L20": auc_post,
    "fresh_post_L20_resid_carried_correctness": auc_resid,
    "fresh_pre_L20_baseline": auc_pre,
}
print(json.dumps(findings["test3_decomp_T"], indent=2), flush=True)

# 4. OOS veto on U: fit correctness dial on ALL T, apply to U (answerable vs halluc)
rowsU_all = L.load_rows(U_DIR)
rowsU = [r for r in rowsU_all if r.get("outcome") in ("answerable_attempt", "hallucination")
         and os.path.exists(L.tensor_path(U_DIR, r["row_key"], "post"))]
yU = np.array([1 if r["outcome"] == "answerable_attempt" else 0 for r in rowsU])  # 1=trust,0=halluc
Upost20, _ = L.load_layer_matrix(U_DIR, rowsU, "post", 20, {})
sU = L.score_full_probe(fp_T, Upost20)
findings["test4_veto_U_OOS"] = {
    "n_answerable": int(yU.sum()), "n_hallucination": int((1 - yU).sum()),
    "Tdial_post_L20_on_U_veto_AUROC": float(roc_auc_score(yU, sU)),
    "Tdial_post_L20_on_U_veto_ci95": boot_ci(yU, sU),
    "published_U_veto_reference": 0.980,
}
print(json.dumps(findings["test4_veto_U_OOS"], indent=2), flush=True)

with open(os.path.join(OUT, "findings_grpo_family.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings_grpo_family.json", flush=True)
