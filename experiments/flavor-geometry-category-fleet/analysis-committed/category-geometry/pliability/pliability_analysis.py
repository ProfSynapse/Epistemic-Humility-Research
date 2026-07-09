#!/usr/bin/env python3
"""Pliability one-curve vs per-category analysis on the Amendment AH surface.

Question: is prime pliability (whether a prompt prime flips refuse/answer behavior)
a single curve in baseline boundary distance (caution_dist_z), or category-specific?

Prior finding (session 0035, different surface): compliance both directions collapsed
onto ONE curve of baseline boundary distance (AUROC 0.823). Here we have per-row
unanswerability-category labels and test whether that one-curve picture holds.

CPU only. Tier-1 lab-notebook: characterize + report, no gates.
"""
import json
import os
from pathlib import Path
import numpy as np
from collections import Counter, defaultdict
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = Path(__file__).resolve().parents[5]
LEGACY_ANALYSIS = REPO / "experiment" / "phase1" / "probe" / "analysis"
BASE = str(LEGACY_ANALYSIS / "ah_main")
ARMS = ["A0", "Acertain", "Adoubt"]
CATS = ["ambiguous", "controversial", "unsolved_problem",
        "false_assumption", "future_unknown", "counterfactual"]
MIN_CELL = 30  # cells below this are flagged unstable and not interpreted

def load(arm):
    p = os.path.join(BASE, f"gen_{arm}", "rows.jsonl")
    return [json.loads(l) for l in open(p)]

def auroc(y, x):
    """AUROC of continuous x predicting binary y; None if a class is empty."""
    y = np.asarray(y); x = np.asarray(x)
    if len(set(y.tolist())) < 2:
        return None
    return float(roc_auc_score(y, x))

def logit_fit(X, y):
    """Fit logistic regression, return fitted log-likelihood and n params."""
    X = np.asarray(X, dtype=float); y = np.asarray(y, dtype=int)
    if len(set(y.tolist())) < 2:
        return None
    clf = LogisticRegression(max_iter=2000, C=1e6, solver="lbfgs")
    clf.fit(X, y)
    p = clf.predict_proba(X)[:, 1]
    eps = 1e-12
    ll = float(np.sum(y * np.log(p + eps) + (1 - y) * np.log(1 - p + eps)))
    k = X.shape[1] + 1  # + intercept
    return {"ll": ll, "k": k, "n": len(y)}

def lr_test(restricted, full):
    """Likelihood-ratio test: full vs restricted (nested)."""
    if restricted is None or full is None:
        return None
    d = 2.0 * (full["ll"] - restricted["ll"])
    df = full["k"] - restricted["k"]
    if df <= 0:
        return None
    pval = float(stats.chi2.sf(d, df))
    return {"lr_stat": float(d), "df": int(df), "pval": pval}

def design_matrices(rows, y_field=None, y_vals=None):
    """Build z-only, z+category (main effects), z+category+interaction matrices.

    Categories restricted to those with >=1 row present among the labeled cats.
    Uncategorized ('(none)') rows are dropped from the category models but kept
    in the z-only pooled model note (handled by caller).
    Returns dict of design matrices keyed by model name, aligned label vector y,
    and the per-category index arrays.
    """
    z = np.array([r["caution_dist_z"] for r in rows], dtype=float)
    cat = [r["category_canon"] for r in rows]
    y = np.array(y_vals, dtype=int)
    present = [c for c in CATS if cat.count(c) > 0]
    # dummy code categories (drop-first -> reference is first present cat)
    ref = present[0] if present else None
    dummies = np.zeros((len(rows), max(len(present) - 1, 0)))
    for j, c in enumerate(present[1:]):
        dummies[:, j] = np.array([1.0 if cc == c else 0.0 for cc in cat])
    X_z = z.reshape(-1, 1)
    if len(present) >= 2:
        X_zc = np.hstack([X_z, dummies])
        inter = dummies * z.reshape(-1, 1)
        X_zci = np.hstack([X_z, dummies, inter])
    else:
        X_zc = None
        X_zci = None
    return {"X_z": X_z, "X_zc": X_zc, "X_zci": X_zci, "y": y,
            "present": present, "ref": ref}

def per_category_stats(rows, y_vals):
    out = {}
    cat = [r["category_canon"] for r in rows]
    z = np.array([r["caution_dist_z"] for r in rows])
    y = np.array(y_vals)
    for c in CATS + ["(none)"]:
        idx = [i for i, cc in enumerate(cat) if cc == c]
        n = len(idx)
        if n == 0:
            continue
        yc = y[idx]; zc = z[idx]
        rate = float(yc.mean())
        a = auroc(yc, zc) if n >= MIN_CELL else None
        out[c] = {"n": n, "rate": rate, "auroc_z": a,
                  "unstable": n < MIN_CELL}
    return out

def main():
    raw = {arm: load(arm) for arm in ARMS}
    a0 = {r["row_key"]: r for r in raw["A0"]}

    findings = {}

    # ---- overlap structure ----
    ac_keys = set(r["row_key"] for r in raw["Acertain"])
    ad_keys = set(r["row_key"] for r in raw["Adoubt"])
    a0_keys = set(a0)
    findings["overlap"] = {
        "n_A0": len(a0_keys), "n_Acertain": len(ac_keys), "n_Adoubt": len(ad_keys),
        "Acertain_subset_of_A0": ac_keys <= a0_keys,
        "Adoubt_subset_of_A0": ad_keys <= a0_keys,
        "Acertain_Adoubt_disjoint": len(ac_keys & ad_keys) == 0,
        "Acertain_contrast": dict(Counter(r["contrast"] for r in raw["Acertain"])),
        "Adoubt_contrast": dict(Counter(r["contrast"] for r in raw["Adoubt"])),
        "note": ("Acertain = the 1338 release rows (all gold=unanswerable); "
                 "Adoubt = 174 muzzle + 150 positive_control rows (all gold=answerable). "
                 "Prime arm is collinear with contrast direction and gold_class."),
    }

    # ================================================================
    # 1. BASELINE behavior curve: P(refused) ~ caution_dist_z in A0
    # ================================================================
    base_rows = raw["A0"]
    y_ref = [1 if r["refused"] else 0 for r in base_rows]
    # z-only on full A0 (incl uncategorized)
    z_all = np.array([r["caution_dist_z"] for r in base_rows]).reshape(-1, 1)
    m_z_full = logit_fit(z_all, y_ref)
    au_z_full = auroc(y_ref, z_all.ravel())

    # category models: restrict to labeled cats only (drop '(none)')
    lab_idx = [i for i, r in enumerate(base_rows) if r["category_canon"] in CATS]
    base_lab = [base_rows[i] for i in lab_idx]
    y_ref_lab = [y_ref[i] for i in lab_idx]
    dm = design_matrices(base_lab, y_vals=y_ref_lab)
    m_z = logit_fit(dm["X_z"], dm["y"])
    m_zc = logit_fit(dm["X_zc"], dm["y"]) if dm["X_zc"] is not None else None
    m_zci = logit_fit(dm["X_zci"], dm["y"]) if dm["X_zci"] is not None else None

    findings["baseline_refusal"] = {
        "n_full_A0": len(base_rows),
        "n_labeled": len(base_lab),
        "auroc_z_predicts_refused_full": au_z_full,
        "present_categories": dm["present"],
        "reference_category": dm["ref"],
        "models": {"z": m_z, "z+cat": m_zc, "z+cat+interaction": m_zci},
        "lr_cat_vs_z": lr_test(m_z, m_zc),
        "lr_interaction_vs_maineffect": lr_test(m_zc, m_zci),
        "per_category": per_category_stats(base_lab, y_ref_lab),
        "confab_rate_by_category": {},
    }
    # confab rates by category in A0 (only unanswerable rows can confab; report all)
    for c in CATS + ["(none)"]:
        cr = [r for r in base_rows if r["category_canon"] == c]
        if not cr:
            continue
        findings["baseline_refusal"]["confab_rate_by_category"][c] = {
            "n": len(cr),
            "confab_rate": float(np.mean([1 if r["confab_on_unanswerable"] else 0 for r in cr])),
            "n_unanswerable": sum(1 for r in cr if r["gold_class"] == "unanswerable"),
        }

    # ================================================================
    # 2. PRIME UPTAKE per arm
    #    release (Acertain): uptake = A0 refused AND prime answered (flip to answer)
    #    muzzle/pos_ctrl (Adoubt): uptake = A0 answered AND prime refused (flip to refuse)
    # ================================================================
    findings["uptake"] = {}
    for arm, direction in [("Acertain", "release"), ("Adoubt", "muzzle")]:
        prime_rows = raw[arm]
        recs = []
        for pr in prime_rows:
            b = a0[pr["row_key"]]
            if direction == "release":
                # eligible: baseline refused; uptake = prime answered
                eligible = bool(b["refused"])
                uptake = 1 if (b["refused"] and pr["answered"]) else 0
            else:
                # doubt prime pushes toward refusing; eligible: baseline answered
                eligible = bool(b["answered"])
                uptake = 1 if (b["answered"] and pr["refused"]) else 0
            recs.append({
                "row_key": pr["row_key"],
                "category_canon": pr["category_canon"],
                "caution_dist_z": b["caution_dist_z"],
                "score_L24": b["score_L24"],
                "eligible": eligible,
                "uptake": uptake,
            })
        # Restrict uptake modeling to ELIGIBLE rows (rows that had room to flip).
        elig = [r for r in recs if r["eligible"]]
        y_up = [r["uptake"] for r in elig]
        z_up = np.array([r["caution_dist_z"] for r in elig]).reshape(-1, 1)
        m_z_up_full = logit_fit(z_up, y_up)
        au_z_up_full = auroc(y_up, z_up.ravel()) if len(elig) else None

        # labeled-only for category models
        elig_lab = [r for r in elig if r["category_canon"] in CATS]
        y_up_lab = [r["uptake"] for r in elig_lab]
        entry = {
            "direction": direction,
            "n_prime_rows": len(prime_rows),
            "n_eligible": len(elig),
            "n_eligible_labeled": len(elig_lab),
            "overall_uptake_rate_eligible": float(np.mean(y_up)) if y_up else None,
            "auroc_z_predicts_uptake_eligible_full": au_z_up_full,
        }
        if len(elig_lab) and len(set(y_up_lab)) == 2:
            dmu = design_matrices(elig_lab, y_vals=y_up_lab)
            mu_z = logit_fit(dmu["X_z"], dmu["y"])
            mu_zc = logit_fit(dmu["X_zc"], dmu["y"]) if dmu["X_zc"] is not None else None
            mu_zci = logit_fit(dmu["X_zci"], dmu["y"]) if dmu["X_zci"] is not None else None
            entry["present_categories"] = dmu["present"]
            entry["reference_category"] = dmu["ref"]
            entry["models"] = {"z": mu_z, "z+cat": mu_zc, "z+cat+interaction": mu_zci}
            entry["lr_cat_vs_z"] = lr_test(mu_z, mu_zc)
            entry["lr_interaction_vs_maineffect"] = lr_test(mu_zc, mu_zci)
            entry["per_category"] = per_category_stats(elig_lab, y_up_lab)
        else:
            entry["per_category"] = per_category_stats(elig_lab, y_up_lab) if elig_lab else {}
            entry["note_models"] = "insufficient class variation for category LR ladder"
        findings["uptake"][arm] = entry

    # ================================================================
    # 4. SANITY GUARD: score_L24 as competing predictor
    # ================================================================
    z_a0 = np.array([r["caution_dist_z"] for r in base_rows])
    l24_a0 = np.array([r["score_L24"] for r in base_rows])
    corr = float(np.corrcoef(z_a0, l24_a0)[0, 1])
    au_l24_ref = auroc(y_ref, l24_a0)
    # partial: refused ~ z + L24, is L24 adding over z? (LR)
    m_z_only = logit_fit(z_a0.reshape(-1, 1), y_ref)
    m_z_l24 = logit_fit(np.column_stack([z_a0, l24_a0]), y_ref)
    m_l24_only = logit_fit(l24_a0.reshape(-1, 1), y_ref)
    findings["sanity_L24"] = {
        "corr_z_L24_A0": corr,
        "auroc_L24_predicts_refused_A0": au_l24_ref,
        "auroc_z_predicts_refused_A0": au_z_full,
        "lr_L24_over_z": lr_test(m_z_only, m_z_l24),
        "lr_z_over_L24": lr_test(m_l24_only, m_z_l24),
    }
    # also L24 vs uptake per arm (eligible)
    findings["sanity_L24"]["uptake"] = {}
    for arm, direction in [("Acertain", "release"), ("Adoubt", "muzzle")]:
        prime_rows = raw[arm]
        elig = []
        for pr in prime_rows:
            b = a0[pr["row_key"]]
            if direction == "release":
                if not b["refused"]:
                    continue
                up = 1 if pr["answered"] else 0
            else:
                if not b["answered"]:
                    continue
                up = 1 if pr["refused"] else 0
            elig.append((b["caution_dist_z"], b["score_L24"], up))
        if len(elig) < 2:
            continue
        zc = np.array([e[0] for e in elig]); lc = np.array([e[1] for e in elig])
        yc = [e[2] for e in elig]
        findings["sanity_L24"]["uptake"][arm] = {
            "n_eligible": len(elig),
            "corr_z_L24": float(np.corrcoef(zc, lc)[0, 1]),
            "auroc_z_uptake": auroc(yc, zc),
            "auroc_L24_uptake": auroc(yc, lc),
        }

    with open(os.path.join(HERE, "findings.json"), "w") as f:
        json.dump(findings, f, indent=2)
    print("wrote findings.json")
    # brief console echo
    print("baseline auroc_z (refused):", au_z_full)
    print("baseline LR cat vs z:", findings["baseline_refusal"]["lr_cat_vs_z"])
    print("baseline LR interaction:", findings["baseline_refusal"]["lr_interaction_vs_maineffect"])
    for arm in ["Acertain", "Adoubt"]:
        u = findings["uptake"][arm]
        print(arm, "uptake auroc_z:", u["auroc_z_predicts_uptake_eligible_full"],
              "LR cat:", u.get("lr_cat_vs_z"), "LR inter:", u.get("lr_interaction_vs_maineffect"))
    return findings

if __name__ == "__main__":
    main()
