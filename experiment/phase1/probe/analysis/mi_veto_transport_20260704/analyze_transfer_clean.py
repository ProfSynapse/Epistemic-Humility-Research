"""Non-circular transport tests (fixes in-sample leakage of cached probes).

Cached dial/gate probes were fit on their own S/W data, so applying them back
to the same rows is in-sample (~1.0). Here we:

  A) TRANSPORT DIRECTION (core question): fit a fresh correctness/answerability
     probe at ONE position with CV; the SAME fold's probe is evaluated at the
     OTHER position on the held-out rows. This gives an honest cross-position
     transfer AUROC (no leakage).

  B) VETO REPRODUCTION on raw base (W = known vs hallucination), out-of-sample:
     - Fit correctness dial on S (all rows) -> apply to W post L20 (genuine OOS,
       different dataset). This is the raw-base analogue of Amendment U's veto.
     - Fit answerability gate on S? no; use W's own construct via 5-fold CV so the
       held-out hallucination rows are scored by a probe never trained on them,
       at pre L18 and transported to post L18.

  C) Bootstrap CIs on the headline transfer deltas.
"""
import os, json
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
import vt_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(0)


def cv_transfer(Xfit, Xeval, y, seed=0, n_splits=5):
    """Fit on Xfit train fold, eval on Xeval test fold (held-out rows). Returns oof AUROC."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    for tr, te in skf.split(Xfit, y):
        fp = L.fit_full_probe(Xfit[tr], y[tr], seed=seed)
        oof[te] = L.score_full_probe(fp, Xeval[te])
    return float(roc_auc_score(y, oof)), oof


def boot_auc_ci(y, s, n=2000):
    aucs = []
    idx = np.arange(len(y))
    for _ in range(n):
        b = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(y[b])) < 2:
            continue
        aucs.append(roc_auc_score(y[b], s[b]))
    return float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))


findings = {}

# ---- S: correctness, transport between pre/post L20 (honest CV) ----
print("=== S correctness transport (CV) ===", flush=True)
rowsS = L.load_rows(L.S_DIR)
yS = np.array([1 if r["correct"] else 0 for r in rowsS])
cache = {}
Spre20, _ = L.load_layer_matrix(L.S_DIR, rowsS, "pre", 20, cache)
Spost20, _ = L.load_layer_matrix(L.S_DIR, rowsS, "post", 20, cache)
Spre18, _ = L.load_layer_matrix(L.S_DIR, rowsS, "pre", 18, cache)
Spost18, _ = L.load_layer_matrix(L.S_DIR, rowsS, "post", 18, cache)
cache.clear()

s_res = {}
# in-position (honest CV) both
auc_pp, oof_pp = cv_transfer(Spost20, Spost20, yS, seed=1)   # post-fit, post-eval == cv_post
auc_qq, oof_qq = cv_transfer(Spre20, Spre20, yS, seed=1)     # pre-fit, pre-eval == cv_pre
# transport: post-fit applied at pre; pre-fit applied at post
auc_postfit_at_pre, o1 = cv_transfer(Spost20, Spre20, yS, seed=1)
auc_prefit_at_post, o2 = cv_transfer(Spre20, Spost20, yS, seed=1)
s_res["L20"] = {
    "cv_post_correct": auc_pp,
    "cv_pre_correct": auc_qq,
    "postfit_applied_at_pre": auc_postfit_at_pre,
    "prefit_applied_at_post": auc_prefit_at_post,
    "post_beats_pre_delta": auc_pp - auc_qq,
}
ci = boot_auc_ci(yS, oof_pp)
s_res["L20"]["cv_post_ci95"] = list(ci)
ci = boot_auc_ci(yS, oof_qq)
s_res["L20"]["cv_pre_ci95"] = list(ci)
findings["S_correctness_transport"] = s_res
print(json.dumps(s_res, indent=2), flush=True)

# ---- W: veto, out-of-sample ----
print("=== W veto (OOS) ===", flush=True)
rowsW = L.load_rows(L.W_DIR)
# correctness-style label for veto: known-answered (trust=1) vs hallucination (0)
yW_veto = np.array([1 if r.get("outcome") != "hallucination" else 0 for r in rowsW])
yW_ans = np.array([1 if r["label"] == "known" else 0 for r in rowsW])  # answerability
cacheW = {}
Wpre18, _ = L.load_layer_matrix(L.W_DIR, rowsW, "pre", 18, cacheW)
Wpost18, _ = L.load_layer_matrix(L.W_DIR, rowsW, "post", 18, cacheW)
Wpre20, _ = L.load_layer_matrix(L.W_DIR, rowsW, "post", 20, cacheW)  # note: post L20 for dial-style
Wpost20 = Wpre20
cacheW.clear()

w_res = {}
# 1) S-fit correctness dial (all S rows) applied OOS to W post L20 -> raw-base veto
fp_dial = L.fit_full_probe(Spost20, yS, seed=2)
sW = L.score_full_probe(fp_dial, Wpost20)
w_res["Sdial_post_L20_on_W_veto_AUROC"] = float(roc_auc_score(yW_veto, sW))
w_res["Sdial_post_L20_on_W_veto_ci95"] = list(boot_auc_ci(yW_veto, sW))

# 2) W answerability gate via CV at pre L18, and TRANSPORTED to post L18,
#    evaluated on the veto label (known vs hallucination). Because hallucination
#    rows are the unknown-answered subset, answerability≈veto here; report both.
auc_gate_pre, oofg = cv_transfer(Wpre18, Wpre18, yW_ans, seed=3)
auc_gate_post_transport, _ = cv_transfer(Wpre18, Wpost18, yW_ans, seed=3)
w_res["gate_pre_L18_answerability_CV"] = auc_gate_pre
w_res["gate_pre_fit_transported_to_post_L18"] = auc_gate_post_transport
w_res["gate_transport_retention_frac"] = (
    (auc_gate_post_transport - 0.5) / (auc_gate_pre - 0.5) if auc_gate_pre > 0.5 else None
)
findings["W_veto_OOS"] = w_res
print(json.dumps(w_res, indent=2), flush=True)

# ---- Interpretation scalar: fraction of veto that is transported doubt ----
# On W: compare (a) transported answerability at post vs (b) S-dial correctness at post.
# If transported answerability alone reproduces most of the dial veto, veto=carried.
findings["veto_reproduction_summary"] = {
    "raw_base_dial_veto": w_res["Sdial_post_L20_on_W_veto_AUROC"],
    "transported_answerability_at_post": auc_gate_post_transport,
    "note": "answerability construct on W is near-degenerate with the veto label; treat as upper-bound anchor",
}

with open(os.path.join(OUT, "findings_transfer_clean.json"), "w") as f:
    json.dump(findings, f, indent=2)
print("WROTE findings_transfer_clean.json", flush=True)
