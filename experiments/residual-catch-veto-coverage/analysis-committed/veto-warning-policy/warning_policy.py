"""Post-generation warning-policy operating characteristics (CPU-only).

Design: after the model answers, an external readout (the post-gen veto/dial
score) either triggers a warning label or routes to abstain/regenerate. This
script produces the OFFLINE operating characteristics on cached data:

  1. WARNING precision/recall/false-alarm across a veto-score threshold sweep.
  2. CALIBRATION: Platt vs isotonic, out-of-fold, ECE/Brier + reliability curve.
  3. ROUTER: two-signal PIPELINE (gate then veto), confusion structure.
  4. Permutation null on the chosen operating point.

Veto score convention: HIGHER veto score = MORE likely hallucination (we flip the
dial so the positive/警报 direction is hallucination). We WARN when veto >= thr.

Checkpoints:
  raw base  = Qwen3-4B instruct (Amendment W answered rows: 677 hallucination /
              556 answerable_attempt). Dial = S-correctness probe fit OOS.
  grpo-v2   = clean-SFT->GRPO-v2 (Amendment U answered rows: 121 hallucination /
              276 answerable_attempt). Dial = fresh correctness probe, CV OOF.

All probe scores used for grading are OUT-OF-FOLD or genuine cross-dataset OOS.
Reuses vt_lib loaders from the veto-transport analysis.
"""
import os, sys, json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score, brier_score_loss
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.isotonic import IsotonicRegression

# reuse the transport loaders
REPO = Path(__file__).resolve().parents[4]
sys.path.insert(
    0,
    str(REPO / "experiments" / "commitment-point" / "analysis-committed" / "veto-transport"),
)
import vt_lib as L

OUT = os.path.dirname(os.path.abspath(__file__))
SEED = 20260704
rng = np.random.default_rng(SEED)

# ---- stated floors (aim-small, declared BEFORE computing) ----
PRECISION_FLOOR = 0.80          # warning precision target
PRECISION_CI_LB_FLOOR = 0.70    # bootstrap CI lower bound must clear this
N_BOOT = 1000
N_PERM = 200

findings = {
    "meta": {
        "seed": SEED,
        "precision_floor": PRECISION_FLOOR,
        "precision_ci_lb_floor": PRECISION_CI_LB_FLOOR,
        "n_boot": N_BOOT,
        "n_perm": N_PERM,
        "veto_convention": "higher score = more likely hallucination; WARN when veto>=thr",
    }
}


def log(*a):
    print(*a, flush=True)


# ================================================================
# Helpers
# ================================================================
def oof_cv_scores(X, y, seed=SEED, n_splits=5):
    """PCA-128 + saga LR, stratified CV. Return OOF decision scores (higher=class1)."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.zeros(len(y))
    for tr, te in skf.split(X, y):
        fp = L.fit_full_probe(X[tr], y[tr], seed=seed)
        oof[te] = L.score_full_probe(fp, X[te])
    return oof


def boot_metric_ci(fn, *arrays, n=N_BOOT, stratify_pos=None):
    """Bootstrap CI of a scalar metric fn(*arrays_boot). Resamples rows with replacement."""
    m = len(arrays[0])
    vals = []
    idx = np.arange(m)
    for _ in range(n):
        b = rng.choice(idx, m, replace=True)
        try:
            v = fn(*[a[b] for a in arrays])
        except Exception:
            v = np.nan
        if v is not None and not (isinstance(v, float) and np.isnan(v)):
            vals.append(v)
    vals = np.asarray(vals, float)
    if len(vals) == 0:
        return (np.nan, np.nan, np.nan)
    return (float(np.nanmean(vals)),
            float(np.nanpercentile(vals, 2.5)),
            float(np.nanpercentile(vals, 97.5)))


def warn_precision(y_hall, warn_mask):
    """precision = P(hallucination | warned). y_hall: 1=hallucination."""
    w = warn_mask
    if w.sum() == 0:
        return np.nan
    return float(y_hall[w].sum() / w.sum())


def warn_recall(y_hall, warn_mask):
    """recall = P(warned | hallucination)."""
    pos = y_hall == 1
    if pos.sum() == 0:
        return np.nan
    return float((warn_mask & pos).sum() / pos.sum())


def false_alarm_rate(y_hall, warn_mask):
    """FAR = P(warned | correct/good answer) = warnings on non-hallucination answers."""
    neg = y_hall == 0
    if neg.sum() == 0:
        return np.nan
    return float((warn_mask & neg).sum() / neg.sum())


def ece(p, y, n_bins=10):
    """Expected calibration error (equal-width bins)."""
    bins = np.linspace(0, 1, n_bins + 1)
    e = 0.0
    N = len(y)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        m = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        if m.sum() == 0:
            continue
        e += (m.sum() / N) * abs(p[m].mean() - y[m].mean())
    return float(e)


def reliability_points(p, y, n_bins=10):
    bins = np.linspace(0, 1, n_bins + 1)
    pts = []
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        m = (p >= lo) & (p < hi) if i < n_bins - 1 else (p >= lo) & (p <= hi)
        if m.sum() == 0:
            continue
        pts.append({"bin_lo": float(lo), "bin_hi": float(hi),
                    "n": int(m.sum()), "mean_pred": float(p[m].mean()),
                    "frac_hall": float(y[m].mean())})
    return pts


def calibrate_oof(score, y_hall, seed=SEED, n_splits=5):
    """Out-of-fold Platt and isotonic maps from veto score -> P(hallucination).
    Returns dict of oof calibrated probs for each method + ECE/Brier."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    s = score.reshape(-1, 1)
    p_platt = np.zeros(len(y_hall))
    p_iso = np.zeros(len(y_hall))
    for tr, te in skf.split(s, y_hall):
        lr = LogisticRegression(solver="lbfgs", max_iter=1000)
        lr.fit(s[tr], y_hall[tr])
        p_platt[te] = lr.predict_proba(s[te])[:, 1]
        iso = IsotonicRegression(out_of_bounds="clip")
        iso.fit(s[tr].ravel(), y_hall[tr])
        p_iso[te] = iso.predict(s[te].ravel())
    res = {
        "platt": {"ece": ece(p_platt, y_hall), "brier": float(brier_score_loss(y_hall, p_platt)),
                  "reliability": reliability_points(p_platt, y_hall)},
        "isotonic": {"ece": ece(p_iso, y_hall), "brier": float(brier_score_loss(y_hall, p_iso)),
                     "reliability": reliability_points(p_iso, y_hall)},
    }
    return res, p_platt, p_iso


# ================================================================
# Build per-checkpoint veto scores on ANSWERED rows
# ================================================================
def build_raw_base():
    """raw base = W answered rows. Veto = S-correctness dial, fit OOS on S, applied to W.
    y_hall: 1 = hallucination. veto score oriented so higher = hallucination."""
    rowsS = L.load_rows(L.S_DIR)
    yS = np.array([1 if r["correct"] else 0 for r in rowsS])  # 1=correct
    cache = {}
    Spost20, _ = L.load_layer_matrix(L.S_DIR, rowsS, "post", 20, cache)
    cache.clear()
    # fit correctness dial on ALL S rows (higher = correct)
    fp = L.fit_full_probe(Spost20, yS, seed=SEED)

    rowsW = L.load_rows(L.W_DIR)
    # W answered rows only (all W rows are answered)
    y_hall = np.array([1 if r.get("outcome") == "hallucination" else 0 for r in rowsW])
    cacheW = {}
    Wpost20, mW = L.load_layer_matrix(L.W_DIR, rowsW, "post", 20, cacheW)
    cacheW.clear()
    assert mW.all(), "W tensor coverage incomplete"
    corr_score = L.score_full_probe(fp, Wpost20)  # higher = correct
    veto = -corr_score  # higher = hallucination
    datasets = np.array([r["dataset"] for r in rowsW])
    return {"veto": veto, "y_hall": y_hall, "dataset": datasets,
            "rows": rowsW, "n": len(rowsW),
            "sanity_auroc": float(roc_auc_score(1 - y_hall, corr_score))}
    # sanity_auroc: detect trustworthy(=1) with corr_score => matches published 0.784


def build_grpo():
    """grpo-v2 = U answered rows (397). Veto = fresh correctness dial (correct vs
    hallucination) fit via CV OOF on T? T has correct/wrong on popqa/triviaqa; U is
    selfaware. Follow transport report: fit dial on T post L20 (correctness), apply
    OOS to U (answerable_attempt vs hallucination).
    We ALSO provide a within-U CV veto (answerable_attempt=trust vs hallucination)
    so the operating characteristics are not purely cross-dataset."""
    # --- T dial (correctness) fit on all T answered rows ---
    rowsT = L.load_rows(L.T_DIR)
    # T answered rows have correct in {True,False}; refused rows correct=None
    ansT = [i for i, r in enumerate(rowsT) if r.get("answered") and r.get("correct") is not None]
    rowsT_ans = [rowsT[i] for i in ansT]
    yT = np.array([1 if r["correct"] else 0 for r in rowsT_ans])
    cacheT = {}
    Tpost20_all, mT = L.load_layer_matrix(L.T_DIR, rowsT_ans, "post", 20, cacheT)
    cacheT.clear()
    # some answered rows may lack tensors; align
    rowsT_ans = [r for r, mm in zip(rowsT_ans, mT) if mm]
    yT = yT[mT]
    fpT = L.fit_full_probe(Tpost20_all, yT, seed=SEED)

    # --- U answered rows ---
    rowsU = L.load_rows(L.U_DIR)
    ansU = [i for i, r in enumerate(rowsU) if r.get("answered")]
    rowsU_ans = [rowsU[i] for i in ansU]
    y_hall = np.array([1 if r.get("outcome") == "hallucination" else 0 for r in rowsU_ans])
    cacheU = {}
    Upost20, mU = L.load_layer_matrix(L.U_DIR, rowsU_ans, "post", 20, cacheU)
    cacheU.clear()
    rowsU_ans = [r for r, mm in zip(rowsU_ans, mU) if mm]
    y_hall = y_hall[mU]
    corr_score_x = L.score_full_probe(fpT, Upost20)  # cross-dataset OOS, higher=correct
    veto_x = -corr_score_x

    # within-U CV veto (correct/trust=answerable_attempt vs hallucination)
    yU_trust = 1 - y_hall  # 1 = answerable_attempt (trust)
    corr_oof = oof_cv_scores(Upost20, yU_trust, seed=SEED)  # higher = trust
    veto_cv = -corr_oof

    datasets = np.array([r["dataset"] for r in rowsU_ans])
    return {"veto_xdataset": veto_x, "veto_cv": veto_cv, "y_hall": y_hall,
            "dataset": datasets, "rows": rowsU_ans, "n": len(rowsU_ans),
            "sanity_auroc_xdataset": float(roc_auc_score(1 - y_hall, corr_score_x)),
            "sanity_auroc_cv": float(roc_auc_score(yU_trust, corr_oof))}


# ================================================================
# Threshold sweep + candidate operating points
# ================================================================
def sweep_and_candidates(veto, y_hall, tag):
    log(f"--- sweep {tag} ---")
    base_rate = float(y_hall.mean())
    qs = np.linspace(0.01, 0.99, 99)
    thrs = np.quantile(veto, qs)
    thrs = np.unique(thrs)
    sweep = []
    for thr in thrs:
        wm = veto >= thr
        if wm.sum() == 0:
            continue
        sweep.append({
            "thr": float(thr),
            "warn_frac": float(wm.mean()),
            "precision": warn_precision(y_hall, wm),
            "recall": warn_recall(y_hall, wm),
            "false_alarm": false_alarm_rate(y_hall, wm),
            "n_warned": int(wm.sum()),
        })
    # candidate selection: thresholds where precision>=floor AND bootstrap CI lb>=ci_floor,
    # pick a spread by recall (aim-small: highest recall that still clears the floors,
    # plus a higher-precision conservative point, plus a mid point).
    qualified = []
    for row in sweep:
        wm = veto >= row["thr"]
        pm, plo, phi = boot_metric_ci(warn_precision, y_hall, wm.astype(int))
        # note: boot resamples rows; recompute mask via veto>=thr is fixed threshold
        # re-do properly: bootstrap over (veto,y) pairs at fixed thr
        row2 = dict(row)
        row2["precision_ci"] = None
        qualified.append((row, plo, phi, pm))

    # proper bootstrap at fixed threshold over (veto,y_hall)
    def prec_at_thr(v, y, thr):
        wm = v >= thr
        return warn_precision(y, wm) if wm.sum() > 0 else np.nan

    cand_pool = []
    for row in sweep:
        thr = row["thr"]
        pm, plo, phi = boot_metric_ci(
            lambda v, y: prec_at_thr(v, y, thr), veto, y_hall)
        if row["precision"] is not None and row["precision"] >= PRECISION_FLOOR and plo >= PRECISION_CI_LB_FLOOR:
            rm, rlo, rhi = boot_metric_ci(
                lambda v, y: warn_recall(y, v >= thr), veto, y_hall)
            fm, flo, fhi = boot_metric_ci(
                lambda v, y: false_alarm_rate(y, v >= thr), veto, y_hall)
            cand_pool.append({
                "thr": thr, "warn_frac": row["warn_frac"], "n_warned": row["n_warned"],
                "precision": row["precision"], "precision_ci": [plo, phi],
                "recall": row["recall"], "recall_ci": [rlo, rhi],
                "false_alarm": row["false_alarm"], "false_alarm_ci": [flo, fhi],
            })
    # choose up to 3 candidates spanning recall (most permissive that qualifies,
    # a mid, and the most precise)
    chosen = []
    if cand_pool:
        by_recall = sorted(cand_pool, key=lambda c: c["recall"])
        # highest-recall qualified point (aim-small: max catch subject to precision floor)
        chosen.append(("max_recall_at_floor", by_recall[-1]))
        # most precise qualified point
        by_prec = sorted(cand_pool, key=lambda c: c["precision"])
        chosen.append(("max_precision", by_prec[-1]))
        # mid point
        mid = by_recall[len(by_recall) // 2]
        chosen.append(("mid", mid))
    return {"base_rate": base_rate, "sweep": sweep,
            "candidates": [{"kind": k, **v} for k, v in chosen],
            "n_qualified": len(cand_pool)}


# ================================================================
# Permutation null at a chosen operating point
# ================================================================
def perm_null(veto, y_hall, dataset, thr, n=N_PERM):
    """Permute veto scores WITHIN dataset strata; warning precision should collapse
    to the base rate among warned (i.e., ~ overall base rate)."""
    obs_wm = veto >= thr
    obs_prec = warn_precision(y_hall, obs_wm)
    strata = np.unique(dataset)
    null_prec = []
    for _ in range(n):
        vperm = veto.copy()
        for s in strata:
            m = dataset == s
            vperm[m] = rng.permutation(veto[m])
        wm = vperm >= thr
        p = warn_precision(y_hall, wm)
        if p is not None and not np.isnan(p):
            null_prec.append(p)
    null_prec = np.asarray(null_prec)
    base_rate = float(y_hall.mean())
    pval = float((null_prec >= obs_prec).mean()) if len(null_prec) else np.nan
    return {"thr": float(thr), "obs_precision": obs_prec,
            "null_precision_mean": float(null_prec.mean()),
            "null_precision_p95": float(np.percentile(null_prec, 95)),
            "base_rate": base_rate, "p_value": pval}


# ================================================================
# Router confusion (two-signal PIPELINE)
# ================================================================
def router_confusion_grpo():
    """The router uses the pre-gen gate (answerability) + post-gen veto.
    Buckets:
      - gate=answerable & (answered) : model produced an answer -> subject to veto warn
      - gate=unanswerable & veto fires : warn/abstain bucket
      - gate=unanswerable & answered & veto low : ESCAPED hallucination (worst cell)
    We realize this on U (grpo-v2) where refusal/answer behavior is real:
      gate label = row['label'] in {known(answerable), unknown(unanswerable)}
      action = answered vs refused (real model behavior)
      veto (cv) on answered rows.
    Report the confusion: for each (gate, action) cell, counts and, among answered,
    how the veto at the chosen thr splits hallucination vs trust."""
    rowsU = L.load_rows(L.U_DIR)
    out = {}
    # counts of gate x action
    from collections import Counter
    cnt = Counter()
    for r in rowsU:
        gate = "answerable" if r["label"] == "known" else "unanswerable"
        action = "answered" if r.get("answered") else "refused"
        cnt[(gate, action)] += 1
    out["gate_x_action_counts"] = {f"{g}|{a}": c for (g, a), c in sorted(cnt.items())}
    return out


# ================================================================
# MAIN
# ================================================================
def main():
    log("=== BUILD raw base (W) veto ===")
    rb = build_raw_base()
    log("raw base n=", rb["n"], "sanity trustworthy-AUROC=", round(rb["sanity_auroc"], 4),
        "(published ~0.784)")
    findings["raw_base"] = {"n": rb["n"], "base_rate_hall": float(rb["y_hall"].mean()),
                            "sanity_trustworthy_auroc": rb["sanity_auroc"]}

    log("=== BUILD grpo-v2 (U) veto ===")
    gp = build_grpo()
    log("grpo n=", gp["n"], "sanity xdataset AUROC=", round(gp["sanity_auroc_xdataset"], 4),
        "sanity CV AUROC=", round(gp["sanity_auroc_cv"], 4), "(published dial ~0.969/0.980)")
    findings["grpo_v2"] = {"n": gp["n"], "base_rate_hall": float(gp["y_hall"].mean()),
                           "sanity_xdataset_auroc": gp["sanity_auroc_xdataset"],
                           "sanity_cv_auroc": gp["sanity_auroc_cv"]}

    # ---- Sweeps + candidates ----
    log("=== SWEEP raw base ===")
    findings["raw_base"]["sweep_result"] = sweep_and_candidates(rb["veto"], rb["y_hall"], "raw_base")
    log("=== SWEEP grpo-v2 (CV veto) ===")
    findings["grpo_v2"]["sweep_result_cv"] = sweep_and_candidates(gp["veto_cv"], gp["y_hall"], "grpo_cv")
    log("=== SWEEP grpo-v2 (xdataset veto) ===")
    findings["grpo_v2"]["sweep_result_xdataset"] = sweep_and_candidates(gp["veto_xdataset"], gp["y_hall"], "grpo_x")

    # ---- Calibration (out-of-fold) ----
    log("=== CALIBRATION raw base ===")
    cal_rb, _, _ = calibrate_oof(rb["veto"], rb["y_hall"])
    findings["raw_base"]["calibration"] = cal_rb
    log("raw base ECE platt=", round(cal_rb["platt"]["ece"], 4),
        "iso=", round(cal_rb["isotonic"]["ece"], 4))
    log("=== CALIBRATION grpo-v2 (CV veto) ===")
    cal_gp, p_platt_gp, _ = calibrate_oof(gp["veto_cv"], gp["y_hall"])
    findings["grpo_v2"]["calibration_cv"] = cal_gp
    log("grpo ECE platt=", round(cal_gp["platt"]["ece"], 4),
        "iso=", round(cal_gp["isotonic"]["ece"], 4))

    # attach calibrated probability to each candidate operating point (isotonic OOF)
    def attach_calibrated_p(veto, y_hall, cand_list):
        # fit isotonic OOF once and read the mean calibrated P among warned rows
        _, p_platt, p_iso = calibrate_oof(veto, y_hall)
        for c in cand_list:
            wm = veto >= c["thr"]
            c["calibrated_P_hall_warned_isotonic"] = float(p_iso[wm].mean()) if wm.sum() else None
            c["calibrated_P_hall_warned_platt"] = float(p_platt[wm].mean()) if wm.sum() else None
    attach_calibrated_p(rb["veto"], rb["y_hall"], findings["raw_base"]["sweep_result"]["candidates"])
    attach_calibrated_p(gp["veto_cv"], gp["y_hall"], findings["grpo_v2"]["sweep_result_cv"]["candidates"])

    # ---- Permutation null on chosen operating point (max_recall_at_floor if present) ----
    def chosen_thr(sweep_result):
        cands = sweep_result["candidates"]
        for c in cands:
            if c["kind"] == "max_recall_at_floor":
                return c["thr"]
        return cands[0]["thr"] if cands else None

    log("=== PERMUTATION NULL ===")
    thr_rb = chosen_thr(findings["raw_base"]["sweep_result"])
    if thr_rb is not None:
        findings["raw_base"]["perm_null"] = perm_null(rb["veto"], rb["y_hall"], rb["dataset"], thr_rb)
        log("raw base perm:", findings["raw_base"]["perm_null"])
    else:
        findings["raw_base"]["perm_null"] = {"note": "no qualified operating point"}
    thr_gp = chosen_thr(findings["grpo_v2"]["sweep_result_cv"])
    if thr_gp is not None:
        findings["grpo_v2"]["perm_null"] = perm_null(gp["veto_cv"], gp["y_hall"], gp["dataset"], thr_gp)
        log("grpo perm:", findings["grpo_v2"]["perm_null"])
    else:
        findings["grpo_v2"]["perm_null"] = {"note": "no qualified operating point"}

    # ---- Router confusion ----
    log("=== ROUTER ===")
    findings["router"] = router_confusion_grpo()

    # ---- AH residual-catch feasibility ----
    findings["ah_residual_catch"] = {
        "post_gen_tensors_present": False,
        "verdict": "GPU-BLOCKED",
        "note": ("ah_main/gen_A0 contains only rows.jsonl with PRE-gen scalars "
                 "(score_L24, caution_dist_z); zero .safetensors/.npz/.npy at any "
                 "position across the entire ah_main tree. No post-gen activations "
                 "to score the residual confabs. Cannot compute post-gen veto catch "
                 "on the radial-ceiling gate misses without re-extraction on GPU."),
    }

    with open(os.path.join(OUT, "findings.json"), "w") as f:
        json.dump(findings, f, indent=2)
    log("WROTE findings.json")


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "8")
    main()
