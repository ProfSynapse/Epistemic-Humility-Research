"""Core veto-transport analysis: tests 1,2,3,5.

Emits partial findings to findings_core.json.
"""
import os, json, sys
import numpy as np
from scipy.stats import pearsonr, spearmanr
from sklearn.metrics import roc_auc_score
import vt_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
np.random.seed(0)


def log(*a):
    print(*a, flush=True)


findings = {}

# ---------------------------------------------------------------
# Load cached probes
gate = L.load_probe("gate__qwen3-4b-instruct__pre_L18")   # answerability, raw base
dial = L.load_probe("dial__qwen3-4b-instruct__post_L20")  # correctness, raw base
findings["probes"] = {"gate": "pre_L18 answerability", "dial": "post_L20 correctness"}

# ---------------------------------------------------------------
# TEST 1: same-row transport correlation (S surface: pre AND post per row)
log("=== TEST 1: same-row transport on S ===")
rowsS = L.load_rows(L.S_DIR)
yS = np.array([1 if r["correct"] else 0 for r in rowsS])  # 1=correct

# Load gate/dial home layers at both positions
cache = {}
XS_pre_L18, m1 = L.load_layer_matrix(L.S_DIR, rowsS, "pre", 18, cache)
XS_post_L18, m2 = L.load_layer_matrix(L.S_DIR, rowsS, "post", 18, cache)
XS_pre_L20, _ = L.load_layer_matrix(L.S_DIR, rowsS, "pre", 20, cache)
XS_post_L20, _ = L.load_layer_matrix(L.S_DIR, rowsS, "post", 20, cache)
cache.clear()
assert m1.all() and m2.all()

# gate (answerability/doubt) projection at pre vs post, same layer L18
gate_pre = L.apply_probe(gate, XS_pre_L18)
gate_post = L.apply_probe(gate, XS_post_L18)
# dial (correctness) projection at pre vs post, same layer L20
dial_pre = L.apply_probe(dial, XS_pre_L20)
dial_post = L.apply_probe(dial, XS_post_L20)

t1 = {}
r, p = pearsonr(gate_pre, gate_post)
rs, _ = spearmanr(gate_pre, gate_post)
t1["gate_axis_pre_vs_post_L18"] = {"pearson": float(r), "spearman": float(rs)}
r, p = pearsonr(dial_pre, dial_post)
rs, _ = spearmanr(dial_pre, dial_post)
t1["dial_axis_pre_vs_post_L20"] = {"pearson": float(r), "spearman": float(rs)}
# raw-state cosine per row (how much does the whole state move pre->post)
sc_L18 = [L.cos(XS_pre_L18[i], XS_post_L18[i]) for i in range(len(rowsS))]
sc_L20 = [L.cos(XS_pre_L20[i], XS_post_L20[i]) for i in range(len(rowsS))]
t1["raw_state_cos_pre_post_L18"] = {"mean": float(np.mean(sc_L18)), "std": float(np.std(sc_L18))}
t1["raw_state_cos_pre_post_L20"] = {"mean": float(np.mean(sc_L20)), "std": float(np.std(sc_L20))}
findings["test1_same_row_transport"] = t1
log(json.dumps(t1, indent=2))

# ---------------------------------------------------------------
# TEST 2: cross-position probe transfer
log("=== TEST 2: cross-position transfer ===")
t2 = {}

# (a) Native dial veto on S correctness at post (sanity: should ~0.834) and pre (~0.754)
t2["dial_native_post_L20_AUROC_correct"] = float(roc_auc_score(yS, dial_post))
t2["dial_native_pre_L20_AUROC_correct"] = float(roc_auc_score(yS, dial_pre))
# gate applied to S correctness (is answerability axis predictive of correctness?)
t2["gate_on_S_pre_L18_AUROC_correct"] = float(roc_auc_score(yS, gate_pre))
t2["gate_on_S_post_L18_AUROC_correct"] = float(roc_auc_score(yS, gate_post))

# (b) The veto: W has known-answered vs unknown-hallucination (raw base).
#     Build raw-base veto analogue: score W rows with the S dial (post L20),
#     and with the PRE-gen gate (pre L18) TRANSPORTED to post.
rowsW = L.load_rows(L.W_DIR)
# outcome: 'hallucination' (unknown, answered wrong) vs known-answered
yW = np.array([0 if r.get("outcome") == "hallucination" else 1 for r in rowsW])  # 1=known(trustworthy),0=hallucination
log("W label balance known/halluc:", int(yW.sum()), int((1 - yW).sum()))

cacheW = {}
XW_pre_L18, _ = L.load_layer_matrix(L.W_DIR, rowsW, "pre", 18, cacheW)
XW_post_L18, _ = L.load_layer_matrix(L.W_DIR, rowsW, "post", 18, cacheW)
XW_pre_L20, _ = L.load_layer_matrix(L.W_DIR, rowsW, "pre", 20, cacheW)
XW_post_L20, _ = L.load_layer_matrix(L.W_DIR, rowsW, "post", 20, cacheW)
cacheW.clear()

# dial (correctness axis, post L20) as the veto on raw base
sW_dial_post = L.apply_probe(dial, XW_post_L20)
sW_dial_pre = L.apply_probe(dial, XW_pre_L20)
# gate (answerability axis, pre L18) at pre and TRANSPORTED to post
sW_gate_pre = L.apply_probe(gate, XW_pre_L18)
sW_gate_post = L.apply_probe(gate, XW_post_L18)

def auc(y, s):
    # ensure "trustworthy" is positive; report AUROC for detecting hallucination
    return float(roc_auc_score(y, s))

t2["veto_rawbase_dial_post_L20"] = auc(yW, sW_dial_post)
t2["veto_rawbase_dial_pre_L20"] = auc(yW, sW_dial_pre)
t2["veto_rawbase_gate_pre_L18"] = auc(yW, sW_gate_pre)
t2["veto_rawbase_gate_post_L18_TRANSPORTED"] = auc(yW, sW_gate_post)
findings["test2_cross_position"] = t2
log(json.dumps(t2, indent=2))

# ---------------------------------------------------------------
# TEST 3: axis geometry (cosines raw + whitened)
log("=== TEST 3: axis geometry ===")
t3 = {}
gate_coef = gate["logreg_coef"]
dial_coef = dial["logreg_coef"]
# standardized-space coef back to raw space: coef_raw = coef / scale
gate_raw = gate_coef / gate["scaler_scale"]
dial_raw = dial_coef / dial["scaler_scale"]

t3["cos_gatecoef_dialcoef_standardized"] = L.cos(gate_coef, dial_coef)
t3["cos_gatecoef_dialcoef_rawspace"] = L.cos(gate_raw, dial_raw)

# behavioral doubt axis vectors: load a few relevant ones
GOLD_KTO_AXIS_DIR = "mechinterp_gold_kto_calibrated_expression_axis_directions"
LEGACY_GOLD_KTO_AXIS_DIR = "phase" + "3_gold_kto_calibrated_expression_axis_directions"


def load_axis_vec(subdir, folder):
    base = os.path.join(L.AXES, subdir, folder, "directions")
    legacy = os.path.join(L.AXES, LEGACY_GOLD_KTO_AXIS_DIR, folder, "directions")
    dpath = base if os.path.isdir(base) or subdir != GOLD_KTO_AXIS_DIR else legacy
    fs = [f for f in os.listdir(dpath) if f.endswith(".safetensors")]
    from safetensors.numpy import load_file
    t = load_file(os.path.join(dpath, fs[0]))
    k = list(t.keys())[0]
    return t[k].astype(np.float64), k

axis_specs = {
    "unknown_wrong_vs_refused_l25": (GOLD_KTO_AXIS_DIR, "gold_kto_h_lora_unknown_wrong_vs_refused_l25_normed"),
    "unknown_wrong_vs_refused_l27": (GOLD_KTO_AXIS_DIR, "gold_kto_h_lora_unknown_wrong_vs_refused_l27_normed"),
    "known_wrong_vs_correct_l34": (GOLD_KTO_AXIS_DIR, "gold_kto_h_lora_known_wrong_vs_correct_l34_normed"),
    "unknown_refused_vs_known_correct_l36": (GOLD_KTO_AXIS_DIR, "gold_kto_h_lora_unknown_refused_vs_known_correct_l36_normed"),
    "known_refused_vs_correct_l32": (GOLD_KTO_AXIS_DIR, "gold_kto_h_lora_known_refused_vs_correct_l32_normed"),
}
axis_vecs = {}
for name, (sub, fol) in axis_specs.items():
    try:
        v, k = load_axis_vec(sub, fol)
        axis_vecs[name] = v
        t3.setdefault("axis_layers", {})[name] = k
    except Exception as e:
        log("axis load fail", name, e)

t3["cos_raw"] = {}
for name, v in axis_vecs.items():
    t3["cos_raw"][f"gate_vs_{name}"] = L.cos(gate_raw, v)
    t3["cos_raw"][f"dial_vs_{name}"] = L.cos(dial_raw, v)

# whitened cosines (pooled within-class cov from S post L20 correct/wrong)
Wmat = L.whiten_cov([XS_post_L20[yS == 1], XS_post_L20[yS == 0]], shrink=0.1)
def wcos(a, b):
    return L.cos(Wmat @ np.asarray(a, float).ravel(), Wmat @ np.asarray(b, float).ravel())
t3["cos_whitened_postL20cov"] = {"gate_vs_dial_raw": wcos(gate_raw, dial_raw)}
for name, v in axis_vecs.items():
    t3["cos_whitened_postL20cov"][f"gate_vs_{name}"] = wcos(gate_raw, v)
    t3["cos_whitened_postL20cov"][f"dial_vs_{name}"] = wcos(dial_raw, v)
findings["test3_geometry"] = t3
log(json.dumps(t3, indent=2))

# ---------------------------------------------------------------
# TEST 5: decomposition — is post-gen correctness readable BEYOND transported doubt?
log("=== TEST 5: decomposition ===")
t5 = {}
# baseline: fresh correctness probe at post L20 (CV)
auc_post, sd_post, _ = L.cv_auroc(XS_post_L20, yS, layer_seed=0)
auc_pre, sd_pre, _ = L.cv_auroc(XS_pre_L20, yS, layer_seed=0)
t5["fresh_correct_post_L20_AUROC"] = [auc_post, sd_post]
t5["fresh_correct_pre_L20_AUROC"] = [auc_pre, sd_pre]

# residualize post L20 state against the transported gate/doubt projection,
# then re-probe correctness. If it collapses toward pre (~0.754), the post
# advantage IS the transported/updated doubt.
# Use gate direction (pre L18 answerability) evaluated at post L20 state as the
# "transported doubt" scalar; regress each feature on it and take residual.
g_at_post = L.apply_probe(gate, XS_post_L18)  # transported doubt scalar
g_at_post = (g_at_post - g_at_post.mean()) / g_at_post.std()
# residualize post-L20 matrix wrt g_at_post (per-column OLS)
def residualize(X, s):
    s = s.reshape(-1, 1)
    beta = (X.T @ s).ravel() / (s.T @ s).ravel()[0]  # (d,)
    return X - s @ beta.reshape(1, -1)
XS_post_L20_resid = residualize(XS_post_L20, g_at_post)
auc_resid, sd_resid, _ = L.cv_auroc(XS_post_L20_resid, yS, layer_seed=0)
t5["fresh_correct_post_L20_resid_doubt_AUROC"] = [auc_resid, sd_resid]

# also residualize against dial-pre (transported correctness readout itself)
d_pre_scalar = (dial_pre - dial_pre.mean()) / dial_pre.std()
XS_post_L20_resid_dpre = residualize(XS_post_L20, d_pre_scalar)
auc_resid2, sd_resid2, _ = L.cv_auroc(XS_post_L20_resid_dpre, yS, layer_seed=0)
t5["fresh_correct_post_L20_resid_dialpre_AUROC"] = [auc_resid2, sd_resid2]
findings["test5_decomposition"] = t5
log(json.dumps(t5, indent=2))

with open(os.path.join(OUT, "findings_core.json"), "w") as f:
    json.dump(findings, f, indent=2)
log("WROTE findings_core.json")
