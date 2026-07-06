#!/usr/bin/env python3
"""AL prep: is the "commitment" direction generic or confabulation-specific?

The direction was fit and named on unanswerable rows only (confab-vs-refuse at
matched caution, AK prep 0.834), where "commitment to answer" and "propensity
to confabulate" are the same contrast. The two readings come apart on
ANSWERABLE rows: a generic answer-commitment axis should also predict
answer-vs-refuse there; a confabulation-specific axis should not.

Test (TRUE A0 surface, all pre-gen L24, caution-residualized features):
  D_confab  mean-diff confab-vs-refused fit WITHIN unanswerables
  D_answer  mean-diff answered-vs-refused fit WITHIN answerables
  1. cosine(D_confab, D_answer) on caution-residualized PCA space
  2. transfer: D_confab scored on answerables (answered-vs-refused) and
     D_answer scored on unanswerables (confab-vs-refused); each direction is
     fit on the OTHER population so transfer AUROCs are leak-free by
     construction. In-population AUROCs are 5-fold OOF.
  3. everything reported raw AND with the projection itself re-residualized
     against the caution score (matched-caution reading).

Verdict guide: transfer AUROC near the in-population number + high cosine =
one generic answer-commitment axis. Transfer near 0.5 + low cosine = the
direction is confabulation-specific and should be renamed.

Usage:
  python amendment_al_prep_commitment_scope_check.py [--arm true_a0]
"""

import warnings
warnings.filterwarnings("ignore")
import os
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
from amendment_al_prep_doubt_axis_check import load_a0_stack, load_jsonl, auroc  # noqa: E402
from amendment_al_prep_familiarity_vs_knowing import oof_meandiff_proj, unit  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
SEED = 20260705
N_PCA = 128
L_FEAT = 24
L_CAUTION = 35


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="true_a0")
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)

    rows = load_jsonl(al_prep / args.arm / "gen/data/rows_graded.jsonl")
    stack = load_a0_stack(al_prep / args.arm / "extract/data",
                          [r["row_key"] for r in rows])
    X24 = stack[:, L_FEAT, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    del stack

    P24 = StandardScaler().fit_transform(
        PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X24))
    P35 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X35)

    # caution score (same construction as the ceiling sim: OOF logistic on refused)
    y_ref = np.array([1 if r["refused"] else 0 for r in rows])
    c_all = np.zeros(len(rows))
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED + 1)
    for tr, te in skf.split(P35, y_ref):
        sc = StandardScaler().fit(P35[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=SEED).fit(sc.transform(P35[tr]), y_ref[tr])
        c_all[te] = clf.decision_function(sc.transform(P35[te]))
    c_all = (c_all - c_all.mean()) / c_all.std()

    # caution-residualized features (confound removal in feature space, so the
    # mean-diff directions cannot be the caution axis in disguise)
    R = P24 - LinearRegression().fit(c_all.reshape(-1, 1), P24).predict(
        c_all.reshape(-1, 1))

    def idx(pred):
        return np.array([i for i, r in enumerate(rows) if pred(r)])

    confab = idx(lambda r: r["gold_class"] == "unanswerable" and r["answered"])
    un_ref = idx(lambda r: r["gold_class"] == "unanswerable" and r["refused"])
    an_ans = idx(lambda r: r["gold_class"] == "answerable" and r["answered"])
    an_ref = idx(lambda r: r["gold_class"] == "answerable" and r["refused"])
    pops = {"confab": len(confab), "un_refused": len(un_ref),
            "ans_answered": len(an_ans), "ans_refused": len(an_ref)}
    print("populations:", pops, flush=True)

    d_confab = unit(R[confab].mean(0) - R[un_ref].mean(0))
    d_answer = unit(R[an_ans].mean(0) - R[an_ref].mean(0))
    cos = float(d_confab @ d_answer)

    def resid_c(proj, sub):
        lr = LinearRegression().fit(c_all[sub].reshape(-1, 1), proj[sub])
        out = proj.copy()
        out[sub] = proj[sub] - lr.predict(c_all[sub].reshape(-1, 1))
        return out

    # in-population OOF projections
    p_confab_oof = oof_meandiff_proj(R, confab, un_ref, SEED + 2)
    p_answer_oof = oof_meandiff_proj(R, an_ans, an_ref, SEED + 3)
    # cross-population transfer projections (full fit on the other population)
    p_confab_full = R @ d_confab
    p_answer_full = R @ d_answer

    un_all = np.concatenate([confab, un_ref])
    an_all = np.concatenate([an_ans, an_ref])
    findings = {
        "seed": SEED, "arm": args.arm, "layer_feat": L_FEAT,
        "populations": pops,
        "cosine_dconfab_danswer_caution_resid_space": round(cos, 4),
        "in_population_oof": {
            "d_confab: confab_vs_unrefused": round(
                auroc(p_confab_oof[confab], p_confab_oof[un_ref]), 4),
            "d_answer: answered_vs_refused_on_answerable": round(
                auroc(p_answer_oof[an_ans], p_answer_oof[an_ref]), 4),
        },
        "transfer": {
            "d_confab -> answered_vs_refused_on_answerable": round(
                auroc(p_confab_full[an_ans], p_confab_full[an_ref]), 4),
            "d_answer -> confab_vs_unrefused": round(
                auroc(p_answer_full[confab], p_answer_full[un_ref]), 4),
        },
        "transfer_caution_matched": {
            "d_confab -> answered_vs_refused_on_answerable": round(
                auroc(resid_c(p_confab_full, an_all)[an_ans],
                      resid_c(p_confab_full, an_all)[an_ref]), 4),
            "d_answer -> confab_vs_unrefused": round(
                auroc(resid_c(p_answer_full, un_all)[confab],
                      resid_c(p_answer_full, un_all)[un_ref]), 4),
        },
    }
    print(json.dumps(findings, indent=1), flush=True)
    out = al_prep / "commitment_scope_check_report.json"
    out.write_text(json.dumps(findings, indent=2))
    print(f"[scope-check] report -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
