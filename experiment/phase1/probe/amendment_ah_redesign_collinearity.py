#!/usr/bin/env python3
"""Amendment AH redesign check — collinearity + cell projections (CPU).

Pre-signing follow-up (team-lead task, 2026-07-03). NO GPU, NO commits.

The redesigned identification holds prime DIRECTION constant and varies READOUT
state within a gold class:
  - Release contrast (gold-unanswerable): probe-certain (D-over, congruent with a
    certainty prime) vs probe-uncertain (concordant unknown, incongruent).
  - Muzzle contrast (gold-answerable): probe-uncertain (congruent with a doubt
    prime) vs probe-certain (concordant known, incongruent).
Statistical risk = collinearity: readout state (doubt axis) correlates with
boundary distance (caution axis), the pliability covariate that must be
controlled.

This script:
  1. Reconstructs the FROZEN AG caution axis (refused-vs-answered, L24) exactly
     per amendment_ag_state_analysis.py: StandardScaler + LogisticRegression
     (max_iter=2000, C=1.0) fit on the AF-600 L24 states with caution labels
     from the AE census (refused=1/answered=0), sign-oriented so refused
     projects higher. Applies it to all 5,000 mined pre-gen states -> per-row
     signed caution distance. (Sanity: reproduces AG's L24 caution CV AUROC
     0.9374 and base SD 12.395 on AF-600.)
  2. Correlation (Pearson + Spearman) between L24 doubt score and caution
     distance, overall and within the four cells.
  3. Congruent-vs-incongruent caution-distance overlap per contrast (means, SDs,
     overlap coefficient, separability AUC).
  4. Cell-size projections at the consensus(L20/L24/L28) rule, bands 0 and 0.5z.
  5. Proposes (does NOT lock) a caliper-matched ~1200-row pool maximizing
     caution-distance overlap between congruent/incongruent cells within each
     contrast; writes pool_proposal.jsonl + composition.

Reads doubt scores from ah_stage0/score/scored_rows.jsonl (frozen L20/L24/L28 +
fold scores) so it is byte-consistent with the mining pass. Caution axis is
applied to the mined pregen tensors directly.

Output: analysis/ah_stage0/redesign_check/ (canonical, gitignored).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from safetensors import safe_open
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
from scipy.stats import pearsonr, spearmanr

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
ROOT = CANONICAL / "experiment/phase1/probe/analysis/ah_stage0"
AF_BASE = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen"
AE_CENSUS = CANONICAL / "experiment/phase1/probe/analysis/ae_base_behavior_rows/rows.jsonl"
PREGEN = ROOT / "pregen"
OUT = ROOT / "redesign_check"

TARGET_LAYER = "L24"
LAYERS = ["L20", "L24", "L28"]
CV_RANDOM_STATE = 0
N_FOLDS = 5
POOL_TARGET = 1200
POOL_SEED = 20260703


def load_jsonl(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def load_af_caution():
    """Fit the AG caution axis on AF-600 L24; return (pipeline, sign, base_sd, cv_auroc)."""
    af_rows = load_jsonl(AF_BASE / "rows.jsonl")
    ae = {r["row_key"]: r for r in load_jsonl(AE_CENSUS)}
    X, y = [], []
    for r in af_rows:
        with safe_open(str(AF_BASE / f"{r['safe_key']}__pre.safetensors"), "pt") as st:
            X.append(st.get_tensor(TARGET_LAYER).float().numpy().astype(np.float64))
        y.append(1 if ae[r["row_key"]].get("refused", False) else 0)
    X = np.vstack(X); y = np.asarray(y)
    # CV AUROC sanity (reproduce AG 0.9374)
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=CV_RANDOM_STATE)
    clf_cv = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    proba = cross_val_predict(clf_cv, X, y, cv=skf, method="predict_proba")[:, 1]
    cv_auroc = float(roc_auc_score(y, proba))
    # Full fit + sign orientation (refused projects higher)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)).fit(X, y)
    proj = clf.decision_function(X)
    sign = 1.0
    if proj[y == 1].mean() < proj[y == 0].mean():
        sign = -1.0
    proj *= sign
    base_sd = float(proj.std())
    return clf, sign, base_sd, cv_auroc


def overlap_coefficient(a, b, bins=60):
    """Histogram overlap coefficient (area of min of two normalized densities)."""
    lo = min(a.min(), b.min()); hi = max(a.max(), b.max())
    edges = np.linspace(lo, hi, bins + 1)
    ha, _ = np.histogram(a, bins=edges, density=True)
    hb, _ = np.histogram(b, bins=edges, density=True)
    w = np.diff(edges)
    return float(np.sum(np.minimum(ha, hb) * w))


def separability_auc(congruent, incongruent):
    """AUC discriminating congruent(1) from incongruent(0) by caution distance.
    ~0.5 => distributions overlap well (good for covariate control)."""
    y = np.concatenate([np.ones(len(congruent)), np.zeros(len(incongruent))])
    s = np.concatenate([congruent, incongruent])
    if len(np.unique(y)) < 2 or len(s) == 0:
        return None
    return float(roc_auc_score(y, s))


def corr_block(doubt, caution):
    if len(doubt) < 3:
        return {"n": int(len(doubt)), "pearson": None, "spearman": None}
    pr = pearsonr(doubt, caution); sr = spearmanr(doubt, caution)
    return {"n": int(len(doubt)),
            "pearson_r": round(float(pr[0]), 4), "pearson_p": float(pr[1]),
            "spearman_r": round(float(sr[0]), 4), "spearman_p": float(sr[1])}


def run(args):
    OUT.mkdir(parents=True, exist_ok=True)

    # 1. Caution axis
    print("[ah/redesign] reconstructing AG caution axis on AF-600 ...", flush=True)
    clf, sign, base_sd, cv_auroc = load_af_caution()
    print(f"[ah/redesign] caution CV AUROC={cv_auroc:.4f} (AG=0.9374), "
          f"base_sd={base_sd:.3f} (AG=12.395), sign={sign}", flush=True)

    # Load mined rows + doubt scores (byte-consistent with mining pass)
    scored = load_jsonl(ROOT / "score" / "scored_rows.jsonl")
    scored_by_key = {r["safe_key"]: r for r in scored}
    pregen_rows = load_jsonl(PREGEN / "rows.jsonl")

    # Apply caution axis to mined L24 states
    doubt = np.zeros(len(pregen_rows))
    caution = np.zeros(len(pregen_rows))
    gold_known = np.zeros(len(pregen_rows), dtype=int)
    s_L20 = np.zeros(len(pregen_rows)); s_L28 = np.zeros(len(pregen_rows))
    keys = []
    for i, r in enumerate(pregen_rows):
        with safe_open(str(PREGEN / f"{r['safe_key']}__pre.safetensors"), "pt") as st:
            v = st.get_tensor(TARGET_LAYER).float().numpy().astype(np.float64)
        caution[i] = sign * clf.decision_function(v[None, :])[0]
        sc = scored_by_key[r["safe_key"]]
        doubt[i] = sc["score_L24"]; s_L20[i] = sc["score_L20"]; s_L28[i] = sc["score_L28"]
        gold_known[i] = 1 if r["label"] == "known" else 0
        keys.append(r["safe_key"])
    caution_z = caution / base_sd
    keys = np.array(keys)

    # z of doubt on mined pool (for consensus bands)
    grid = json.loads((ROOT / "score" / "divergence_grid.json").read_text())
    z = grid["score_sd"]  # {'L20','L24','L28','fold'}

    def consensus_certain(band):
        return ((s_L20 > band * z["L20"]) & (doubt > band * z["L24"]) & (s_L28 > band * z["L28"]))

    def consensus_uncertain(band):
        return ((s_L20 < -band * z["L20"]) & (doubt < -band * z["L24"]) & (s_L28 < -band * z["L28"]))

    # ---- Cells (task 2a) ----
    # D-over-consensus@0z: consensus-certain & gold-unanswerable
    m_dover_cons = consensus_certain(0.0) & (gold_known == 0)
    # concordant-unknown: probe-uncertain (L24<0) & gold-unanswerable  (incongruent side of release contrast)
    m_conc_unknown = (doubt < 0) & (gold_known == 0)
    # probe-uncertain-any-gold
    m_uncertain_any = (doubt < 0)
    # concordant-known: probe-certain (L24>0) & gold-answerable (incongruent side of muzzle contrast)
    m_conc_known = (doubt > 0) & (gold_known == 1)

    cells = {
        "D_over_consensus_0z": m_dover_cons,
        "concordant_unknown": m_conc_unknown,
        "probe_uncertain_any_gold": m_uncertain_any,
        "concordant_known": m_conc_known,
    }

    # 2a. Correlation overall + per cell
    corr = {"overall": corr_block(doubt, caution)}
    for name, m in cells.items():
        corr[name] = corr_block(doubt[m], caution[m])

    # 2b. Congruent-vs-incongruent distance overlap per contrast.
    # Release contrast (gold-unanswerable): congruent = D-over-consensus@0z,
    #   incongruent = concordant-unknown that is NOT D-over (probe-uncertain unknown).
    rel_cong = caution[m_dover_cons]
    m_rel_incong = (doubt < 0) & (gold_known == 0)
    rel_incong = caution[m_rel_incong]
    # Muzzle contrast (gold-answerable): congruent = probe-uncertain (consensus) answerable,
    #   incongruent = concordant-known (probe-certain answerable).
    m_muz_cong = consensus_uncertain(0.0) & (gold_known == 1)
    muz_cong = caution[m_muz_cong]
    m_muz_incong = (doubt > 0) & (gold_known == 1)
    muz_incong = caution[m_muz_incong]

    def overlap_block(cong, incong):
        if len(cong) == 0 or len(incong) == 0:
            return {"n_congruent": int(len(cong)), "n_incongruent": int(len(incong)),
                    "note": "empty cell"}
        return {
            "n_congruent": int(len(cong)), "n_incongruent": int(len(incong)),
            "mean_congruent": round(float(cong.mean()), 3),
            "mean_incongruent": round(float(incong.mean()), 3),
            "sd_congruent": round(float(cong.std()), 3),
            "sd_incongruent": round(float(incong.std()), 3),
            "overlap_coefficient": round(overlap_coefficient(cong, incong), 4),
            "separability_auc_cong_vs_incong": (
                round(separability_auc(cong, incong), 4)
                if separability_auc(cong, incong) is not None else None),
        }

    overlap = {
        "release_contrast_gold_unanswerable": {
            "congruent": "D_over_consensus_0z", "incongruent": "probe_uncertain_unknown",
            **overlap_block(rel_cong, rel_incong),
        },
        "muzzle_contrast_gold_answerable": {
            "congruent": "consensus_uncertain_answerable",
            "incongruent": "concordant_known (probe_certain_answerable)",
            **overlap_block(muz_cong, muz_incong),
        },
    }

    # 3. Cell-size projections at consensus rule, bands 0 and 0.5z.
    proj = {}
    for band in [0.0, 0.5]:
        cert = consensus_certain(band); unc = consensus_uncertain(band)
        proj[f"{band}z"] = {
            "probe_certain_gold_unanswerable": int((cert & (gold_known == 0)).sum()),
            "probe_uncertain_gold_unanswerable": int((unc & (gold_known == 0)).sum()),
            "probe_certain_gold_answerable": int((cert & (gold_known == 1)).sum()),
            "probe_uncertain_gold_answerable": int((unc & (gold_known == 1)).sum()),
        }

    # 4. Caliper-matched pool proposal (~1200 rows) maximizing caution-distance
    #    overlap between congruent/incongruent within each contrast.
    rng = np.random.default_rng(POOL_SEED)

    def caliper_match(cong_idx, incong_idx, caliper):
        """Greedy 1:1 nearest-neighbor match on caution distance within caliper."""
        cong_idx = list(cong_idx); incong_idx = list(incong_idx)
        rng.shuffle(cong_idx)
        used = set(); pairs = []
        inc_arr = np.array(incong_idx)
        inc_c = caution[inc_arr]
        for ci in cong_idx:
            d = np.abs(inc_c - caution[ci])
            order = np.argsort(d)
            for j in order:
                if d[j] > caliper:
                    break
                cand = inc_arr[j]
                if cand not in used:
                    used.add(cand); pairs.append((ci, int(cand))); break
        return pairs

    caliper = 0.25 * base_sd  # quarter-SD caliper on caution distance
    rel_pairs = caliper_match(np.where(m_dover_cons)[0], np.where(m_rel_incong)[0], caliper)
    muz_pairs = caliper_match(np.where(m_muz_cong)[0], np.where(m_muz_incong)[0], caliper)

    # Assemble pool rows (both members of each pair), tagged by contrast + congruence.
    pool_rows = []
    seen = set()
    def add(idx, contrast, congruent):
        sk = keys[idx]
        if sk in seen:
            return
        seen.add(sk)
        r = pregen_rows[idx]
        pool_rows.append({
            "safe_key": sk, "row_key": r["row_key"], "question": r["question"],
            "label": r["label"], "source": r["source"],
            "score_L24": round(float(doubt[idx]), 3),
            "caution_dist": round(float(caution[idx]), 3),
            "caution_dist_z": round(float(caution_z[idx]), 3),
            "contrast": contrast, "congruent": bool(congruent),
        })
    for ci, ii in rel_pairs:
        add(ci, "release", True); add(ii, "release", False)
    for ci, ii in muz_pairs:
        add(ci, "muzzle", True); add(ii, "muzzle", False)

    # If under target, we simply report what caliper-matching yields (do not pad
    # with unmatched rows — matching quality is the point). If over, keep all
    # matched pairs (matched set is the proposal); report the count.
    with (OUT / "pool_proposal.jsonl").open("w", encoding="utf-8") as fh:
        for row in pool_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    from collections import Counter
    comp = Counter((r["contrast"], r["congruent"], r["label"]) for r in pool_rows)
    pool_comp = {f"{k[0]}|{'congruent' if k[1] else 'incongruent'}|{k[2]}": v
                 for k, v in sorted(comp.items())}
    # post-match overlap check
    def matched_overlap(contrast):
        c = np.array([r["caution_dist"] for r in pool_rows
                      if r["contrast"] == contrast and r["congruent"]])
        i = np.array([r["caution_dist"] for r in pool_rows
                      if r["contrast"] == contrast and not r["congruent"]])
        if len(c) == 0 or len(i) == 0:
            return None
        return {"n_cong": int(len(c)), "n_incong": int(len(i)),
                "mean_cong": round(float(c.mean()), 3),
                "mean_incong": round(float(i.mean()), 3),
                "overlap_coefficient": round(overlap_coefficient(c, i), 4),
                "separability_auc": (round(separability_auc(c, i), 4)
                                     if separability_auc(c, i) is not None else None)}

    report = {
        "amendment": "AH", "stage": "redesign_collinearity_check",
        "caution_axis": {
            "layer": TARGET_LAYER, "cv_auroc_on_AF600": round(cv_auroc, 4),
            "ag_reported_cv_auroc": 0.9374, "base_sd": round(base_sd, 3),
            "ag_reported_base_sd": 12.395, "sign": sign,
            "recipe": "AG amendment_ag_state_analysis: refused=1/answered=0, "
                      "StandardScaler+LogisticRegression(max_iter=2000,C=1.0), L24, "
                      "in-sample on AF600 (mined pool disjoint => out-of-sample)",
        },
        "mined_pool_n": len(pregen_rows),
        "doubt_score_sd_on_pool": z,
        "cell_sizes": {name: int(m.sum()) for name, m in cells.items()},
        "task2a_doubt_caution_correlation": corr,
        "task2b_congruent_incongruent_distance_overlap": overlap,
        "task3_cell_projections_consensus_rule": proj,
        "task4_pool_proposal": {
            "target": POOL_TARGET, "caliper_units": "0.25*caution_base_sd",
            "caliper_value": round(caliper, 3),
            "n_rows_proposed": len(pool_rows),
            "n_release_pairs": len(rel_pairs), "n_muzzle_pairs": len(muz_pairs),
            "composition": pool_comp,
            "post_match_overlap": {
                "release": matched_overlap("release"),
                "muzzle": matched_overlap("muzzle"),
            },
            "pool_file": str(OUT / "pool_proposal.jsonl"),
            "note": "PROPOSAL, not locked. Caliper-matched on caution distance to "
                    "maximize congruent/incongruent overlap. Under-target size "
                    "reflects match availability; do not pad with unmatched rows.",
        },
    }
    (OUT / "collinearity_report.json").write_text(json.dumps(report, indent=2),
                                                  encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
    print(f"[ah/redesign] DONE -> {OUT}", flush=True)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
