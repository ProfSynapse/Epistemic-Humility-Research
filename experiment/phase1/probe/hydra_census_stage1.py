#!/usr/bin/env python3
"""Hydra Stage 1 census — CPU-only hunt for latent directions ("heads") that
support the caution/refusal mechanism beyond the known doubt axis, on the
AI-TRUE checkpoint pre-generation states.

Lab-notebook exploratory diagnostic (NOT an amendment). Readout-level only;
no behavioral claims. Design frozen before running (session 0038 hydra
follow-up + MI fog-of-war backlog):

  1. DEFLATION CURVES  — at L24, L35 and a coarse sweep every 4 layers L8..L36,
     iteratively project out the top discriminative direction for a population
     split and re-fit; AUROC vs number of directions removed. Two signals:
       refused-vs-answered  (caution)   and  confab-vs-unref  (propensity).
     Each with a permutation-label control curve. Cliff => low-rank; plateau
     => many-headed.
  2. ICA PANEL — FastICA (n=16, n=32) on the caution-residualised PCA-128
     space at L24. For each component: AUROC against every population split and
     |cosine| against the reference axes (doubt, caution, propensity,
     familiarity-internal, actually-knowing). Candidate new head = population
     discrimination >= 0.65 AND |cos| < 0.3 to every named axis.
  3. CORRELATE PANEL — for each candidate: text-surface correlates (fam_feats
     from amendment_al_prep_familiarity_vs_knowing: rare_word_frac,
     mean_log_freq, proper nouns, token count, char length) and flavor
     breakdown across the unanswerability flavors (category_canon). Tells us
     if a "head" is just a surface-form or flavor detector.
  4. STABILITY — refit ICA on two random halves; candidate reproduces if
     max |cosine| across halves > 0.6. Only reproducing heads count.

Probe discipline (this box): full-dim 2560 logistic probes are unusably slow.
Reduce with randomized PCA-128 per layer (label-agnostic, fit once per layer)
then LogisticRegression(solver="saga", tol=1e-3). Seed 20260705.

Data (untracked, canonical checkout): the TRUE A0 surface. gen graded rows +
full-stack (L0..L36) pre-gen safetensors. Loaders reuse
amendment_al_prep_doubt_axis_check (load_a0_stack, load_jsonl, auroc).

Usage:
  python hydra_census_stage1.py [--out <dir>] [--quick]
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
import time
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA, FastICA
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, KFold
from sklearn.preprocessing import StandardScaler

# The AL-prep loaders live only on the AL branch (untracked helper not on main),
# so the three small helpers are inlined verbatim from
# amendment_al_prep_doubt_axis_check.py to keep this census committable on its
# own branch. Conventions preserved exactly (37-layer stack, one safetensors
# open per row, rank-based tie-aware AUROC).
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
CPROBE = CANONICAL / "experiment/phase1/probe"
AL_PREP = CPROBE / "analysis/amendment_al_prep"
N_STACK_LAYERS = 37


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def auroc(pos, neg):
    """Rank-based AUROC, ties handled; no sklearn dependency. Verbatim from
    amendment_al_prep_doubt_axis_check.auroc."""
    pos = np.asarray(pos)
    neg = np.asarray(neg)
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    scores = np.concatenate([pos, neg])
    order = scores.argsort(kind="mergesort")
    ranks = np.empty(len(scores))
    ranks[order] = np.arange(1, len(scores) + 1)
    sorted_scores = scores[order]
    i = 0
    while i < len(sorted_scores):
        j = i
        while j + 1 < len(sorted_scores) and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def load_a0_stack(extract_data, row_keys):
    """[n_rows, 37, 2560] float32; one safetensors open per row. Verbatim from
    amendment_al_prep_doubt_axis_check.load_a0_stack."""
    from safetensors import safe_open
    extract_data = Path(extract_data)
    safe = {r["row_key"]: r["safe_key"]
            for r in load_jsonl(extract_data / "rows.jsonl")}
    keys = [f"L{i}" for i in range(N_STACK_LAYERS)]
    out = None
    for i, rk in enumerate(row_keys):
        path = extract_data / f"{safe[rk]}__pre.safetensors"
        with safe_open(str(path), "np") as h:
            if out is None:
                dim = h.get_tensor("L0").shape[0]
                out = np.empty((len(row_keys), N_STACK_LAYERS, dim), dtype=np.float32)
            for li, key in enumerate(keys):
                out[i, li] = h.get_tensor(key)
    return out

SEED = 20260705
N_PCA = 128
N_FOLDS = 5
DEFLATION_LAYERS = [24, 35]
SWEEP_LAYERS = list(range(8, 37, 4))  # 8,12,16,20,24,28,32,36
N_DEFLATION_ITERS = 12
ICA_LAYER = 24
ICA_NS = [16, 32]
CAND_AUROC = 0.65
CAND_COS = 0.30
STAB_COS = 0.60
DEFAULT_OUT = CANONICAL / "experiment/phase1/probe/analysis/hydra_census_stage1"


def unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n else v


def logreg():
    # saga + tol=1e-3 per the box's probe-discipline note.
    return LogisticRegression(solver="saga", tol=1e-3, max_iter=5000, C=1.0)


def project_out(X, d):
    """Remove component along unit direction d from rows of X."""
    return X - np.outer(X @ d, d)


# ------------------------------------------------------------------ populations
def build_populations(rows):
    def idx(pred):
        return np.array([i for i, r in enumerate(rows) if pred(r)], dtype=int)

    answerable = np.array([r["gold_class"] == "answerable" for r in rows])
    refused = np.array([bool(r["refused"]) for r in rows])
    answered = np.array([bool(r["answered"]) for r in rows])
    pop = {
        "confab": idx(lambda r: r["gold_class"] == "unanswerable" and r["answered"]),
        "un_refused": idx(lambda r: r["gold_class"] == "unanswerable" and r["refused"]),
        "ans_correct": idx(lambda r: r["gold_class"] == "answerable"
                           and r["answered"] and r["correct"] is True),
        "ans_wrong": idx(lambda r: r["gold_class"] == "answerable"
                         and r["answered"] and r["correct"] is False),
        "ans_refused": idx(lambda r: r["gold_class"] == "answerable" and r["refused"]),
    }
    masks = {"answerable": answerable, "refused": refused, "answered": answered}
    return pop, masks


def label_vectors(rows, pop, masks):
    """Binary label vectors for each population split we score against."""
    n = len(rows)
    y = {}
    # refused vs answered (caution) over ALL rows
    y["refused_vs_answered"] = masks["refused"].astype(int)
    # answerable vs unanswerable
    y["answerable_vs_unanswerable"] = masks["answerable"].astype(int)
    # correct vs wrong within answered answerables
    cw = np.full(n, -1)
    cw[pop["ans_correct"]] = 1
    cw[pop["ans_wrong"]] = 0
    y["correct_vs_wrong"] = cw  # -1 = not in split
    # confab vs unanswerable-refused (propensity)
    cvr = np.full(n, -1)
    cvr[pop["confab"]] = 1
    cvr[pop["un_refused"]] = 0
    y["confab_vs_unref"] = cvr
    return y


# ------------------------------------------------------------------ deflation
def deflation_curve(Xs, y_full, mask_split, n_iters, permute_seed=None):
    """Iterative removal with proper within-fold fitting on a binary split.

    Xs           standardized (or PCA-standardized) matrix, all rows.
    y_full       int labels aligned to Xs rows; entries outside the split are
                 ignored via mask_split.
    mask_split   boolean over rows selecting the two-class subset to score.
    Returns list length n_iters+1 of held-out AUROC (iter 0 = full).
    """
    sub = np.where(mask_split)[0]
    Xsub = Xs[sub]
    ysub = y_full[sub].astype(int)
    if permute_seed is not None:
        ysub = np.random.default_rng(permute_seed).permutation(ysub)

    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=0)
    folds = []
    for tr, te in skf.split(Xsub, ysub):
        sc = StandardScaler().fit(Xsub[tr])
        folds.append({"tr": tr, "te": te,
                      "Xtr": sc.transform(Xsub[tr]).copy(),
                      "Xte": sc.transform(Xsub[te]).copy()})

    def score():
        yt, sc_all = [], []
        for st in folds:
            clf = logreg().fit(st["Xtr"], ysub[st["tr"]])
            sc_all.append(clf.decision_function(st["Xte"]))
            yt.append(ysub[st["te"]])
        return float(roc_auc_score(np.concatenate(yt), np.concatenate(sc_all)))

    curve = [score()]
    for _ in range(n_iters):
        for st in folds:
            clf = logreg().fit(st["Xtr"], ysub[st["tr"]])
            w = clf.coef_.ravel()
            nrm = np.linalg.norm(w)
            w = w / nrm if nrm else w
            st["Xtr"] = project_out(st["Xtr"], w)
            st["Xte"] = project_out(st["Xte"], w)
        curve.append(score())
    return curve


def heads_to_floor(curve, ctrl_curve):
    """Number of removed directions until real AUROC drops within 0.02 of the
    permuted-control AUROC (i.e. signal exhausted)."""
    base = curve[0]
    for i, a in enumerate(curve):
        if a <= ctrl_curve[i] + 0.02:
            return i
    return None


# ------------------------------------------------------------------ ref axes
def build_reference_axes(P, pop, mean_log_freq, seed):
    """Reference axes in the standardized PCA-128 space at ICA_LAYER (P is that
    space). All defined OOF-free as full-data mean-diff / ridge directions in the
    reduced space (used only for cosine comparison, not scoring)."""
    def meandiff(pos, neg):
        return unit(P[pos].mean(0) - P[neg].mean(0))

    axes = {}
    axes["doubt"] = meandiff(pop["ans_correct"], pop["un_refused"])
    # caution: refused - answered (all rows)
    refused_idx = np.concatenate([pop["un_refused"], pop["ans_refused"]])
    answered_idx = np.concatenate([pop["ans_correct"], pop["ans_wrong"], pop["confab"]])
    axes["caution"] = unit(P[refused_idx].mean(0) - P[answered_idx].mean(0))
    # propensity: confab - un_refused (within unanswerable)
    axes["propensity"] = meandiff(pop["confab"], pop["un_refused"])
    # actually-knowing: correct - wrong within answered answerables
    axes["knowing"] = meandiff(pop["ans_correct"], pop["ans_wrong"])
    # familiarity-internal: ridge PCA-128 -> mean_log_freq (full-data direction)
    rg = Ridge(alpha=10.0).fit(P, mean_log_freq)
    axes["familiarity_internal"] = unit(rg.coef_.astype(np.float64))
    return axes


# ------------------------------------------------------------------ fam feats
def build_fam_feats(rows):
    tok_re = re.compile(r"[A-Za-z']+")
    corpus = Counter()
    for r in rows:
        for w in tok_re.findall(r["question"].lower()):
            corpus[w] += 1
    tot = sum(corpus.values())

    def fam_feats(q):
        toks = tok_re.findall(q.lower())
        n = len(toks)
        if n == 0:
            return [0.0, 0.0, 0.0, 0.0, 0.0]
        rare = sum(1 for w in toks if corpus[w] <= 2) / n
        mean_logf = float(np.mean([math.log(corpus[w] / tot + 1e-9) for w in toks]))
        proper = sum(1 for w in q.split()[1:] if re.match(r"^[A-Z][a-z]+", w))
        return [rare, mean_logf, float(proper), float(n), float(len(q))]

    FAM = np.array([fam_feats(r["question"]) for r in rows])
    names = ["rare_word_frac", "mean_log_freq", "proper_nouns",
             "token_count", "char_length"]
    return FAM, names


# ------------------------------------------------------------------ ICA panel
def ica_components(Xs_resid, n_comp, seed):
    """FastICA on the (caution-residualised) standardized matrix; return the
    mixing directions in the input space, unit-normalised, and the sources."""
    ica = FastICA(n_components=n_comp, random_state=seed, max_iter=2000,
                  tol=1e-4, whiten="unit-variance")
    S = ica.fit_transform(Xs_resid)  # [n, n_comp]
    # mixing_ maps sources -> data; its columns are directions in input space.
    A = ica.mixing_  # [d, n_comp]
    dirs = np.array([unit(A[:, k]) for k in range(n_comp)])
    return S, dirs


def component_auroc_table(S, y_dict, pop, masks):
    """For each component (column of S) AUROC against every split."""
    out = []
    n_comp = S.shape[1]
    for k in range(n_comp):
        s = S[:, k]
        row = {}
        # refused vs answered
        row["refused_vs_answered"] = round(
            auroc(s[masks["refused"]], s[masks["answered"]]), 4)
        # answerable vs unanswerable
        row["answerable_vs_unanswerable"] = round(
            auroc(s[masks["answerable"]], s[~masks["answerable"]]), 4)
        # correct vs wrong
        row["correct_vs_wrong"] = round(
            auroc(s[pop["ans_correct"]], s[pop["ans_wrong"]]), 4)
        # confab vs unref
        row["confab_vs_unref"] = round(
            auroc(s[pop["confab"]], s[pop["un_refused"]]), 4)
        out.append(row)
    return out


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--arm", default="true_a0")
    ap.add_argument("--quick", action="store_true",
                    help="fewer deflation iters / skip sweep for a smoke")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    graded = load_jsonl(AL_PREP / args.arm / "gen/data/rows_graded.jsonl")
    row_keys = [r["row_key"] for r in graded]
    print(f"[census] {len(graded)} graded rows ({time.time()-t0:.0f}s)", flush=True)

    pop, masks = build_populations(graded)
    y_dict = label_vectors(graded, pop, masks)
    findings = {
        "seed": SEED, "arm": args.arm, "n_rows": len(graded),
        "n_pca": N_PCA, "populations": {k: int(len(v)) for k, v in pop.items()},
    }
    print("[census] populations:", findings["populations"], flush=True)

    FAM, fam_names = build_fam_feats(graded)
    mean_log_freq = FAM[:, 1]

    # ---- load the full stack once; PCA-reduce per layer (label-agnostic).
    print("[census] loading full stack ...", flush=True)
    stack = load_a0_stack(AL_PREP / args.arm / "extract/data", row_keys)
    print(f"[census] stack {stack.shape} ({time.time()-t0:.0f}s)", flush=True)

    layers_needed = sorted(set(DEFLATION_LAYERS + SWEEP_LAYERS + [ICA_LAYER]))
    P_by_layer = {}   # standardized PCA-128 per layer
    for li in layers_needed:
        X = stack[:, li, :].astype(np.float64)
        Xp = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit_transform(X)
        P_by_layer[li] = StandardScaler().fit_transform(Xp)
        print(f"[census] PCA L{li} done ({time.time()-t0:.0f}s)", flush=True)
    del stack

    # ============================================================ 1. deflation
    n_iters = 4 if args.quick else N_DEFLATION_ITERS
    deflation = {}
    signals = {
        "caution_refused_vs_answered": ("refused_vs_answered",
                                        masks["refused"] | masks["answered"]),
        "propensity_confab_vs_unref": ("confab_vs_unref",
                                       y_dict["confab_vs_unref"] >= 0),
    }
    sweep_ls = DEFLATION_LAYERS if args.quick else sorted(set(DEFLATION_LAYERS + SWEEP_LAYERS))
    for li in sweep_ls:
        P = P_by_layer[li]
        deflation[f"L{li}"] = {}
        for sig_name, (ykey, split_mask) in signals.items():
            real = deflation_curve(P, y_dict[ykey], split_mask, n_iters)
            ctrl = deflation_curve(P, y_dict[ykey], split_mask, n_iters,
                                   permute_seed=SEED)
            deflation[f"L{li}"][sig_name] = {
                "real_auroc_by_iter": [round(a, 4) for a in real],
                "permuted_auroc_by_iter": [round(a, 4) for a in ctrl],
                "heads_to_floor": heads_to_floor(real, ctrl),
                "auroc_full": round(real[0], 4),
                "auroc_after_1": round(real[1], 4),
            }
            print(f"[census] deflation L{li} {sig_name}: full {real[0]:.3f} "
                  f"after1 {real[1]:.3f} heads {deflation[f'L{li}'][sig_name]['heads_to_floor']} "
                  f"({time.time()-t0:.0f}s)", flush=True)
    findings["deflation"] = deflation

    # ============================================================ 2/4. ICA panel + stability
    P24 = P_by_layer[ICA_LAYER]
    # caution-residualise: remove the full-data caution direction (refused vs
    # answered mean-diff in this space) so ICA looks for structure BEYOND caution.
    ref_axes = build_reference_axes(P24, pop, mean_log_freq, SEED)
    caution_dir = ref_axes["caution"]
    P24_resid = project_out(P24, caution_dir)

    ica_panel = {}
    for n_comp in ICA_NS:
        S, dirs = ica_components(P24_resid, n_comp, SEED)
        auroc_tbl = component_auroc_table(S, y_dict, pop, masks)
        # cosine of each component direction against reference axes (also in the
        # residualised space -> residualise the ref axes for a fair cosine).
        ref_resid = {k: unit(project_out(v.reshape(1, -1), caution_dir).ravel())
                     if k != "caution" else v
                     for k, v in ref_axes.items()}
        comps = []
        for k in range(n_comp):
            d = dirs[k]
            cosines = {name: round(float(abs(d @ rv)), 4)
                       for name, rv in ref_resid.items()}
            best_auroc = max(auroc_tbl[k].values(),
                             key=lambda a: abs(a - 0.5))
            max_cos = max(cosines.values())
            is_cand = (abs(best_auroc - 0.5) + 0.5 >= CAND_AUROC) and (max_cos < CAND_COS)
            comps.append({
                "component": k,
                "auroc": auroc_tbl[k],
                "abs_cos_to_ref": cosines,
                "max_abs_cos_ref": round(max_cos, 4),
                "best_split_auroc_dist_from_chance": round(abs(best_auroc - 0.5), 4),
                "is_candidate_head": bool(is_cand),
            })
        ica_panel[f"n{n_comp}"] = {"components": comps}
        print(f"[census] ICA n={n_comp}: "
              f"{sum(c['is_candidate_head'] for c in comps)} candidate heads "
              f"({time.time()-t0:.0f}s)", flush=True)

    findings["ica_panel"] = ica_panel

    # ---- stability: refit ICA on two random halves, match components by |cos|.
    rng = np.random.default_rng(SEED)
    perm = rng.permutation(len(graded))
    half_a, half_b = perm[: len(perm) // 2], perm[len(perm) // 2:]
    stability = {}
    for n_comp in ICA_NS:
        Sa, dirs_a = ica_components(P24_resid[half_a], n_comp, SEED + 1)
        Sb, dirs_b = ica_components(P24_resid[half_b], n_comp, SEED + 2)
        # full-fit dirs (reference for candidate indexing)
        _, dirs_full = ica_components(P24_resid, n_comp, SEED)
        repro = []
        for k in range(n_comp):
            d = dirs_full[k]
            best_a = max(abs(d @ da) for da in dirs_a)
            best_b = max(abs(d @ db) for db in dirs_b)
            repro.append({
                "component": k,
                "max_abs_cos_halfA": round(float(best_a), 4),
                "max_abs_cos_halfB": round(float(best_b), 4),
                "reproduces": bool(best_a > STAB_COS and best_b > STAB_COS),
            })
        stability[f"n{n_comp}"] = repro
    findings["ica_stability"] = stability

    # ============================================================ 3. correlate panel
    # Only for candidate heads that also reproduce; report their text-surface
    # correlates and flavor breakdown so we can tell surface-detectors apart.
    flavor_key = "category_canon"
    flavors = sorted(set(r.get(flavor_key, "(none)") for r in graded))
    correlate_panel = {}
    for n_comp in ICA_NS:
        S, dirs = ica_components(P24_resid, n_comp, SEED)
        repro_map = {r["component"]: r["reproduces"]
                     for r in stability[f"n{n_comp}"]}
        cand_map = {c["component"]: c["is_candidate_head"]
                    for c in ica_panel[f"n{n_comp}"]["components"]}
        rows_out = []
        for k in range(n_comp):
            if not (cand_map.get(k) and repro_map.get(k)):
                continue
            s = S[:, k]
            # text-surface correlates
            txt = {}
            for j, nm in enumerate(fam_names):
                r = float(np.corrcoef(s, FAM[:, j])[0, 1])
                txt[nm] = round(r, 4)
            # flavor breakdown: mean component score per flavor (unanswerables)
            fl = {}
            for f in flavors:
                m = np.array([r.get(flavor_key, "(none)") == f for r in graded])
                if m.sum() >= 5:
                    fl[f] = round(float(s[m].mean()), 4)
            rows_out.append({"component": k, "text_correlates": txt,
                             "flavor_mean_score": fl})
        correlate_panel[f"n{n_comp}"] = rows_out
    findings["correlate_panel_reproducing_candidates"] = correlate_panel

    # ---- summary
    n_repro_cand = sum(
        1 for n in ICA_NS
        for c in ica_panel[f"n{n}"]["components"]
        if c["is_candidate_head"]
        and next(r for r in stability[f"n{n}"] if r["component"] == c["component"])["reproduces"]
    )
    findings["summary"] = {
        "reproducing_candidate_heads_total": n_repro_cand,
        "null_result": n_repro_cand == 0,
        "elapsed_s": round(time.time() - t0, 1),
    }

    (out / "hydra_census_report.json").write_text(json.dumps(findings, indent=2))
    print(f"[census] report -> {out/'hydra_census_report.json'} "
          f"({time.time()-t0:.0f}s)", flush=True)
    print(f"[census] reproducing candidate heads: {n_repro_cand}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
