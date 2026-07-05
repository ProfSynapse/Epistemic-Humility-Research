#!/usr/bin/env python3
"""AL prep: familiarity vs actually-knowing on the TRUE A0 blind-spot confabs.

The TRUE ceiling table found the residual confabs sit on the reads-as-known
side of the doubt axis (confab-vs-refused 0.84 within unanswerables), so an
answerability gate cannot reach them without collateral. Hypothesis (user):
that elevation is FAMILIARITY masquerading as knowledge - the model recognizes
the surface of the question without holding a retrievable answer. If so, a
familiarity-corrected knowledge readout separates blind-spot confabs from
genuinely-known rows and gives the radial controller a gate with reach.

Context from Amendment AK prep (mi_familiarity_geometry_20260704, GRPO-v2
surface): the internal direction fit to corpus-frequency familiarity was weak
(0.571) and whitened-orthogonal to the commitment axis; text proxies read
confab-vs-refuse at 0.682. This script re-poses the question on the TRUE
checkpoint with the question that matters for AL: not confab-vs-refuse, but
CONFAB-vs-CORRECT-ANSWER - can any readout put the blind-spot confabs and the
answers-to-protect on opposite sides?

Populations (TRUE arm, graded A0 rows):
  confab      unanswerable & answered            (the blind spot)
  un_refused  unanswerable & refused             (correct refusals)
  ans_correct answerable & answered & correct    (the rows to protect)
  ans_wrong   answerable & answered & incorrect
  ans_refused answerable & refused

Readouts (pre-gen states; OOF wherever a row would otherwise score itself):
  doubt   unit(mean(ka)-mean(ur)) at L35 and L24, 5-fold OOF cell means.
  fam_int ridge PCA-128(L24) -> mean_log_freq (pool-internal corpus,
          AK-prep feature defs verbatim), 5-fold OOF projection.
  fam_txt the 5 text proxies themselves (no activations).
  know    correct-vs-wrong mean-diff within answered answerables on
          standardized PCA-128, at L24 and L35, 5-fold OOF.

Tests:
  T1 does familiarity explain the confab doubt elevation? confab-vs-un_refused
     AUROC of the doubt projection, before vs after residualising on text
     familiarity features (and on the internal familiarity projection).
  T2 do confabs read low on actually-knowing? know-projection AUROCs for
     confab-vs-un_refused and (the AL question) ans_correct-vs-confab.
  T3 gate-candidate table: ans_correct-vs-confab AUROC for every readout and
     for doubt-minus-familiarity / know-based combinations. A score >= ~0.8
     here is a gate with reach into the blind spot.

Usage:
  python amendment_al_prep_familiarity_vs_knowing.py [--arm true_a0]
"""

import warnings
warnings.filterwarnings("ignore")
import os
os.environ.setdefault("OMP_NUM_THREADS", "8")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "8")
os.environ.setdefault("MKL_NUM_THREADS", "8")

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler

PROBE_DIR = Path(__file__).resolve().parent
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))
from amendment_al_prep_doubt_axis_check import load_a0_stack, load_jsonl, auroc  # noqa: E402

CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
DEFAULT_AL_PREP = CANONICAL / "experiment/phase1/probe/analysis/amendment_al_prep"
SEED = 20260705
N_PCA = 128
N_SPLITS = 5
LAYERS = {"L24": 24, "L35": 35}


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n else v


def oof_meandiff_proj(X: np.ndarray, pos_idx: np.ndarray, neg_idx: np.ndarray,
                      seed: int) -> np.ndarray:
    """Project ALL rows onto a pos-minus-neg mean-diff direction, where each
    defining-cell row is projected onto a direction fit WITHOUT it (5-fold over
    the defining cells); rows outside both cells use the full-fit direction."""
    proj = np.zeros(len(X))
    outside = np.setdiff1d(np.arange(len(X)), np.concatenate([pos_idx, neg_idx]))
    d_full = unit(X[pos_idx].mean(0) - X[neg_idx].mean(0))
    proj[outside] = X[outside] @ d_full
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
    pos_folds = list(kf.split(pos_idx))
    neg_folds = list(kf.split(neg_idx))
    for (ptr, pte), (ntr, nte) in zip(pos_folds, neg_folds):
        d = unit(X[pos_idx[ptr]].mean(0) - X[neg_idx[ntr]].mean(0))
        held = np.concatenate([pos_idx[pte], neg_idx[nte]])
        proj[held] = X[held] @ d
    return proj


def residualise(scores: np.ndarray, covars: np.ndarray) -> np.ndarray:
    lr = LinearRegression().fit(covars, scores)
    return scores - lr.predict(covars)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="true_a0")
    ap.add_argument("--al-prep-dir", default=str(DEFAULT_AL_PREP))
    args = ap.parse_args()
    al_prep = Path(args.al_prep_dir)

    rows = load_jsonl(al_prep / args.arm / "gen/data/rows_graded.jsonl")
    stack = load_a0_stack(al_prep / args.arm / "extract/data",
                          [r["row_key"] for r in rows])

    # ---------------- populations
    def idx(pred):
        return np.array([i for i, r in enumerate(rows) if pred(r)])

    pop = {
        "confab": idx(lambda r: r["gold_class"] == "unanswerable" and r["answered"]),
        "un_refused": idx(lambda r: r["gold_class"] == "unanswerable" and r["refused"]),
        "ans_correct": idx(lambda r: r["gold_class"] == "answerable"
                           and r["answered"] and r["correct"] is True),
        "ans_wrong": idx(lambda r: r["gold_class"] == "answerable"
                         and r["answered"] and r["correct"] is False),
        "ans_refused": idx(lambda r: r["gold_class"] == "answerable" and r["refused"]),
    }
    findings = {"seed": SEED, "arm": args.arm,
                "populations": {k: int(len(v)) for k, v in pop.items()}}
    print("populations:", findings["populations"], flush=True)

    # ---------------- text familiarity features (AK-prep defs, pool corpus)
    tok_re = re.compile(r"[A-Za-z']+")
    from collections import Counter
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

    FAM = np.array([fam_feats(r["question"]) for r in rows])
    mean_log_freq = FAM[:, 1]

    # ---------------- per-layer machinery
    P = {}
    for name, li in LAYERS.items():
        X = stack[:, li, :].astype(np.float64)
        Xp = PCA(N_PCA, svd_solver="randomized",
                 random_state=SEED).fit_transform(X)
        P[name] = StandardScaler().fit_transform(Xp)
    del stack

    ka, ur = pop["ans_correct"], pop["un_refused"]
    cw_pos, cw_neg = pop["ans_correct"], pop["ans_wrong"]

    scores = {}
    for name in LAYERS:
        scores[f"doubt_{name}"] = oof_meandiff_proj(P[name], ka, ur, SEED)
        scores[f"know_{name}"] = oof_meandiff_proj(P[name], cw_pos, cw_neg, SEED + 1)

    # internal familiarity: OOF ridge PCA-128(L24) -> mean_log_freq
    fam_int = np.zeros(len(rows))
    kf = KFold(n_splits=N_SPLITS, shuffle=True, random_state=SEED + 2)
    for tr, te in kf.split(P["L24"]):
        rg = Ridge(alpha=10.0).fit(P["L24"][tr], mean_log_freq[tr])
        fam_int[te] = rg.predict(P["L24"][te])
    scores["fam_int_L24"] = fam_int
    findings["fam_int_r"] = round(float(np.corrcoef(fam_int, mean_log_freq)[0, 1]), 4)

    # ---------------- population means per score (the 2-axis map)
    findings["population_means"] = {
        s: {k: round(float(v[pop[k]].mean()), 3) for k in pop}
        for s, v in scores.items()}
    findings["population_means"]["mean_log_freq"] = {
        k: round(float(mean_log_freq[pop[k]].mean()), 3) for k in pop}

    def pair_auroc(score, pos_key, neg_key):
        return round(auroc(score[pop[pos_key]], score[pop[neg_key]]), 4)

    # ---------------- T1: does familiarity explain the confab doubt elevation?
    t1 = {}
    for name in LAYERS:
        d = scores[f"doubt_{name}"]
        t1[name] = {
            "doubt_raw": pair_auroc(d, "confab", "un_refused"),
            "doubt_resid_txtfam": pair_auroc(residualise(d, FAM),
                                             "confab", "un_refused"),
            "doubt_resid_famint": pair_auroc(
                residualise(d, scores["fam_int_L24"].reshape(-1, 1)),
                "confab", "un_refused"),
            "txtfam_alone_meanlogfreq": pair_auroc(mean_log_freq,
                                                   "confab", "un_refused"),
            "famint_alone": pair_auroc(scores["fam_int_L24"],
                                       "confab", "un_refused"),
        }
    findings["T1_confab_doubt_elevation_vs_familiarity"] = t1
    print("T1:", json.dumps(t1), flush=True)

    # ---------------- T2: do confabs read low on actually-knowing?
    t2 = {}
    for name in LAYERS:
        k = scores[f"know_{name}"]
        t2[name] = {
            "know_oof_auroc_correct_vs_wrong": round(
                auroc(k[cw_pos], k[cw_neg]), 4),
            "know_confab_vs_unrefused": pair_auroc(k, "confab", "un_refused"),
            "know_anscorrect_vs_confab": pair_auroc(k, "ans_correct", "confab"),
        }
    findings["T2_actually_knowing"] = t2
    print("T2:", json.dumps(t2), flush=True)

    # ---------------- T3: gate-candidate table (ans_correct vs confab)
    t3 = {}
    for s, v in scores.items():
        t3[s] = pair_auroc(v, "ans_correct", "confab")
    t3["mean_log_freq"] = pair_auroc(mean_log_freq, "ans_correct", "confab")
    for name in LAYERS:
        d_resid = residualise(scores[f"doubt_{name}"], FAM)
        t3[f"doubt_{name}_resid_txtfam"] = pair_auroc(d_resid,
                                                      "ans_correct", "confab")
        combo = ((scores[f"doubt_{name}"] - scores[f"doubt_{name}"].mean())
                 / scores[f"doubt_{name}"].std()
                 + (scores[f"know_{name}"] - scores[f"know_{name}"].mean())
                 / scores[f"know_{name}"].std())
        t3[f"doubt_plus_know_{name}"] = pair_auroc(combo, "ans_correct", "confab")
    findings["T3_gate_candidates_anscorrect_vs_confab"] = t3
    print("T3:", json.dumps(t3, indent=1), flush=True)

    out = al_prep / "familiarity_vs_knowing_report.json"
    out.write_text(json.dumps(findings, indent=2))
    print(f"[fam-vs-knowing] report -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
