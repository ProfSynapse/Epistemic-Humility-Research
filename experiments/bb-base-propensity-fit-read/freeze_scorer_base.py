#!/usr/bin/env python3
"""BB phase 1 step 2 (CPU, no GPU): fit and freeze the BASE confab-propensity
scorer (AMENDMENT.md section 5.2/5.4).

Applies AL's exact recipe (`amendment_al_select_and_direction.py:122-142,
197-204`) to BASE's own fit-surface extraction and BASE's own generation
grades (never AL's AI-TRUE grades, AMENDMENT.md section 2.3). The core fitting
functions below (`unit`, `load_stack`, `oof_caution`, `oof_meandiff_proj`,
and the PCA -> standardize -> caution-residualize -> mean-diff -> z-scale
sequence in `fit_frozen_scorer`) are copied verbatim from H9's
`freeze_scorer.py` (H9 experiment.yaml pin
`1b64ddd5d24477aa779db58f181e3f50e24c1258bd7df18c731896fcf2d7da8d`, read on
the h9-propensity-gate branch): same math, same helper bodies. This script's
FILE is necessarily NOT byte-identical to H9's freeze_scorer.py -- it reads a
different fit surface (BB's own base extraction + base grades, not AL's
al_run_dir/al_extract_dir/al_graded), has no on-disk d_raw.npy/prop_z.npy to
cross-reference (AMENDMENT.md section 5.4: "there is NO prior base direction
on disk, so cross-reference fidelity does not apply"), and therefore
implements BB-FID-1/BB-FID-2 as determinism + recipe-parity checks instead of
H9's FID-1/FID-2 cross-reference checks. See the STOP-flagged note in
build_and_verify() on gates.yaml's literal "freeze_scorer.py sha256 == H9
pinned scorer" wording.

FIDELITY GATE (gates.yaml `fidelity`), asserted here:
  BB-FID-1 (determinism): refitting on the identical extraction with the same
    pca_seed twice reproduces d_raw at cosine >= 0.999999 and max|diff| <= 1e-5.
  BB-FID-2 (recipe parity): the AL section-3.2 knobs (pca_seed=20260705,
    pca_components=128, n_splits=5, fit_layers propensity=24/caution=35) match
    cell.yaml exactly, AND the core fit-math functions in this file are a
    verbatim copy of H9's freeze_scorer.py (function-level parity; see the
    STOP note -- a whole-FILE sha256 match against H9's pin is not achievable
    given this file's necessarily different I/O and fidelity-reporting code).

Usage:
  python freeze_scorer_base.py --cell cell.yaml --gates gates.yaml \
    [--fit-extract-dir DIR] [--fit-graded PATH] [--smoke]

Real GPU inputs (fit-surface extraction + fit-surface base grades) are
gitignored and land under analysis/phase1/ once pulled back from the Modal
volume; they do not exist on this host yet (no model has been run). --smoke
exercises the identical fit path on synthetic random activations so the
plumbing (I/O, PCA/fit math, persistence, fidelity checks) is verified before
any GPU spend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import yaml
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.preprocessing import StandardScaler

N_LAYERS = 37

# H9's freeze_scorer.py pin (h9-propensity-gate branch experiment.yaml), the
# function-level parity target for BB-FID-2. See the module docstring.
H9_FREEZE_SCORER_PIN_SHA256 = "1b64ddd5d24477aa779db58f181e3f50e24c1258bd7df18c731896fcf2d7da8d"


# --- core fit-math functions: verbatim copy of H9's freeze_scorer.py --------
def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_stack(extract_data: Path, row_keys: list[str]) -> np.ndarray:
    """[n_rows, 37, dim] float32; one safetensors open per row."""
    from safetensors import safe_open

    safe = {r["row_key"]: r["safe_key"]
            for r in load_jsonl(extract_data / "rows.jsonl")}
    keys = [f"L{i}" for i in range(N_LAYERS)]
    out = None
    for i, rk in enumerate(row_keys):
        path = extract_data / f"{safe[rk]}__pre.safetensors"
        with safe_open(str(path), "np") as h:
            if out is None:
                dim = h.get_tensor("L0").shape[0]
                out = np.empty((len(row_keys), N_LAYERS, dim), dtype=np.float32)
            for li, key in enumerate(keys):
                out[i, li] = h.get_tensor(key)
    return out


def oof_meandiff_proj(X, pos_idx, neg_idx, seed, n_splits):
    """OOF mean-diff projection. Used for the honest in-cell prop OOF AUROC
    record (non-gating; AMENDMENT.md section 6, honest_prior)."""
    proj = np.zeros(len(X))
    outside = np.setdiff1d(np.arange(len(X)), np.concatenate([pos_idx, neg_idx]))
    d_full = unit(X[pos_idx].mean(0) - X[neg_idx].mean(0))
    proj[outside] = X[outside] @ d_full
    kf = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    pos_folds = list(kf.split(pos_idx))
    neg_folds = list(kf.split(neg_idx))
    for (ptr, pte), (ntr, nte) in zip(pos_folds, neg_folds):
        d = unit(X[pos_idx[ptr]].mean(0) - X[neg_idx[ntr]].mean(0))
        held = np.concatenate([pos_idx[pte], neg_idx[nte]])
        proj[held] = X[held] @ d
    return proj


def oof_caution(P35, y_ref, seed, n_splits):
    """5-fold OOF caution log-odds, z-scored."""
    out = np.zeros(len(y_ref))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in skf.split(P35, y_ref):
        sc = StandardScaler().fit(P35[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=seed).fit(sc.transform(P35[tr]),
                                                        y_ref[tr])
        out[te] = clf.decision_function(sc.transform(P35[te]))
    return (out - out.mean()) / out.std()


def fit_frozen_scorer(X24: np.ndarray, X35: np.ndarray, y_ref: np.ndarray,
                       confab_idx: np.ndarray, un_ref_idx: np.ndarray,
                       seed: int, n_pca: int, n_splits: int) -> dict:
    """Pure fit function: PCA -> standardize -> caution-residualize (OOF, for
    d_raw) -> mean-diff -> map to raw space -> frozen full-sample deployment
    objects. Identical sequence to H9's build_frozen_scorer body. Returns a
    dict of fitted sklearn/numpy objects plus d_raw (for BB-FID-1 determinism
    comparison) and the in-cell readouts needed for the honest-prior record.
    """
    pca24 = PCA(n_pca, svd_solver="randomized", random_state=seed).fit(X24)
    Z24 = pca24.transform(X24)
    scaler24 = StandardScaler().fit(Z24)
    P24 = scaler24.transform(Z24)
    pca35 = PCA(n_pca, svd_solver="randomized", random_state=seed).fit(X35)
    P35 = pca35.transform(X35)

    c_oof = oof_caution(P35, y_ref, seed + 1, n_splits)

    # d_raw: OOF-c-residualized full-sample mean-diff (identical construction
    # to AL's d_raw and H9's FID-1 target).
    R_oof = P24 - LinearRegression().fit(c_oof.reshape(-1, 1), P24).predict(
        c_oof.reshape(-1, 1))
    d_confab_full = unit(R_oof[confab_idx].mean(0) - R_oof[un_ref_idx].mean(0))
    d_raw_unnorm = (d_confab_full / scaler24.scale_) @ pca24.components_
    d_raw = unit(d_raw_unnorm)

    # deployable frozen scorer (full-sample caution, frozen residualizer)
    sc35 = StandardScaler().fit(P35)
    caution_clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                     random_state=seed + 1).fit(sc35.transform(P35), y_ref)
    c_frozen_raw = caution_clf.decision_function(sc35.transform(P35))
    c_frozen_mean, c_frozen_std = float(c_frozen_raw.mean()), float(c_frozen_raw.std())
    c_frozen = (c_frozen_raw - c_frozen_mean) / c_frozen_std
    caution_residualizer = LinearRegression().fit(c_frozen.reshape(-1, 1), P24)
    R_frozen = P24 - caution_residualizer.predict(c_frozen.reshape(-1, 1))
    prop_full_raw = R_frozen @ d_confab_full
    prop_mean, prop_std = float(prop_full_raw.mean()), float(prop_full_raw.std())
    prop_full = (prop_full_raw - prop_mean) / prop_std

    caution_incell_auroc = float(roc_auc_score(y_ref, c_frozen))
    fullsample_prop_incell_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop_full[confab_idx], prop_full[un_ref_idx]]))

    return {
        "pca24": pca24, "pca35": pca35, "scaler24": scaler24, "scaler35": sc35,
        "caution_clf": caution_clf, "caution_residualizer": caution_residualizer,
        "d_confab_full": d_confab_full, "d_raw": d_raw,
        "prop_mean": prop_mean, "prop_std": prop_std,
        "caution_zscale_mean": c_frozen_mean, "caution_zscale_std": c_frozen_std,
        "c_oof": c_oof, "caution_incell_auroc_frozen": caution_incell_auroc,
        "fullsample_prop_incell_auroc_NONGATING": fullsample_prop_incell_auroc,
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


# --- BB build wrapper: reads BB's own inputs, runs the fit twice for BB-FID-1,
#     asserts BB-FID-2 recipe knobs, persists frozen objects ------------------
def build_and_verify(cell: dict, gates: dict, X24: np.ndarray, X35: np.ndarray,
                      rows: list[dict], exp_dir: Path, smoke: bool) -> dict:
    sc_cfg = cell["phase1"]["scorer"]
    L_PROP = sc_cfg["fit_layers"]["propensity"]      # 24
    L_CAUTION = sc_cfg["fit_layers"]["caution"]      # 35
    N_PCA = sc_cfg["pca_components"]                  # 128
    N_SPLITS = sc_cfg["n_splits"]                     # 5
    seed = sc_cfg["pca_seed"]                         # 20260705

    fid = gates["fidelity"]
    # BB-FID-2 (recipe parity, knob half): AL section 3.2 constants must match
    # cell.yaml exactly (mirrors H9's assert pca_seed == SEED).
    AL_SEED, AL_N_PCA, AL_N_SPLITS = 20260705, 128, 5
    AL_L_PROP, AL_L_CAUTION = 24, 35
    knobs_match = (seed == AL_SEED and N_PCA == AL_N_PCA and N_SPLITS == AL_N_SPLITS
                   and L_PROP == AL_L_PROP and L_CAUTION == AL_L_CAUTION)
    assert knobs_match, (
        f"cell.yaml phase1.scorer knobs do not match AL section 3.2: "
        f"seed={seed} (want {AL_SEED}), n_pca={N_PCA} (want {AL_N_PCA}), "
        f"n_splits={N_SPLITS} (want {AL_N_SPLITS}), "
        f"fit_layers=({L_PROP},{L_CAUTION}) (want ({AL_L_PROP},{AL_L_CAUTION}))")

    y_ref = np.array([1 if r["refused"] else 0 for r in rows])
    confab_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["answered"]])
    un_ref_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["refused"]])

    # BB-P1-G0 (fit-surface evaluability precondition, checked before G1 is
    # read; AMENDMENT.md section 6 / gates.yaml fit_evaluability).
    fe = gates["fit_evaluability"]
    g0 = {"n_confab": int(len(confab_idx)), "n_un_refused": int(len(un_ref_idx)),
          "min_confabs": fe["min_confabs"], "min_un_refused": fe["min_unanswerable_refusals"],
          "met": bool(len(confab_idx) >= fe["min_confabs"]
                      and len(un_ref_idx) >= fe["min_unanswerable_refusals"])}

    # BB-FID-1 (determinism): fit TWICE on the identical extraction with the
    # same seed, compare d_raw. This is BB's substitute for H9's cross-
    # reference to an on-disk array (AMENDMENT.md section 5.4: no prior base
    # direction exists to reproduce).
    fit_a = fit_frozen_scorer(X24, X35, y_ref, confab_idx, un_ref_idx, seed, N_PCA, N_SPLITS)
    fit_b = fit_frozen_scorer(X24, X35, y_ref, confab_idx, un_ref_idx, seed, N_PCA, N_SPLITS)
    d_raw_a, d_raw_b = fit_a["d_raw"], fit_b["d_raw"]
    det_cos = float(d_raw_a @ d_raw_b / (np.linalg.norm(d_raw_a) * np.linalg.norm(d_raw_b)))
    det_maxabs = float(np.max(np.abs(d_raw_a - d_raw_b)))
    bb_fid1_pass = (det_cos >= fid["BB-FID-1_determinism_cosine_min"]
                    and det_maxabs <= fid["BB-FID-1_determinism_maxabs_diff_max"])

    # honest in-cell OOF priors (non-gating; gates.yaml honest_prior). Residualize
    # P24 by OOF caution before the OOF mean-diff projection, matching AL's own
    # R construction (see fit_frozen_scorer's R_oof).
    Z24 = fit_a["pca24"].transform(X24)
    P24 = fit_a["scaler24"].transform(Z24)
    R24 = P24 - LinearRegression().fit(fit_a["c_oof"].reshape(-1, 1), P24).predict(
        fit_a["c_oof"].reshape(-1, 1))
    prop_oof_proj = oof_meandiff_proj(R24, confab_idx, un_ref_idx, seed + 2, N_SPLITS)
    prop_oof_z = (prop_oof_proj - prop_oof_proj.mean()) / prop_oof_proj.std()
    prop_incell_oof_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop_oof_z[confab_idx], prop_oof_z[un_ref_idx]]))
    caution_incell_oof_auroc = float(roc_auc_score(y_ref, fit_a["c_oof"]))

    # ---- persist frozen objects + sha256 manifest (fit_a is the canonical
    #      frozen scorer; fit_b existed only for the determinism check) ----
    import joblib
    frozen_out = exp_dir / sc_cfg["frozen_out"]
    frozen_out.mkdir(parents=True, exist_ok=True)
    joblib.dump(fit_a["pca24"], frozen_out / "pca24.joblib")
    joblib.dump(fit_a["pca35"], frozen_out / "pca35.joblib")
    joblib.dump(fit_a["scaler24"], frozen_out / "scaler24.joblib")
    joblib.dump(fit_a["scaler35"], frozen_out / "scaler35.joblib")
    joblib.dump(fit_a["caution_clf"], frozen_out / "caution_logistic.joblib")
    joblib.dump(fit_a["caution_residualizer"], frozen_out / "caution_residualizer.joblib")
    np.save(frozen_out / "d_confab_full.npy", fit_a["d_confab_full"].astype(np.float64))
    np.save(frozen_out / "d_raw_rederived.npy", fit_a["d_raw"].astype(np.float64))
    (frozen_out / "prop_zscale.json").write_text(json.dumps({
        "prop_mean": fit_a["prop_mean"], "prop_std": fit_a["prop_std"],
        "caution_zscale_mean": fit_a["caution_zscale_mean"],
        "caution_zscale_std": fit_a["caution_zscale_std"],
        "fit_layers": {"propensity": L_PROP, "caution": L_CAUTION},
        "pca_components": N_PCA, "pca_seed": seed}, indent=2))
    obj_files = ["pca24.joblib", "pca35.joblib", "scaler24.joblib", "scaler35.joblib",
                 "caution_logistic.joblib", "caution_residualizer.joblib",
                 "d_confab_full.npy", "d_raw_rederived.npy", "prop_zscale.json"]
    scorer_manifest = {f: _sha256(frozen_out / f) for f in obj_files}
    (frozen_out / "scorer_manifest.json").write_text(json.dumps(scorer_manifest, indent=2))

    this_file_sha256 = _sha256(Path(__file__).resolve())
    report = {
        "tier": "smoke" if smoke else "registered",
        "n_rows": len(rows), "n_confab": g0["n_confab"], "n_un_refused": g0["n_un_refused"],
        "BB-P1-G0_fit_evaluability": g0,
        "BB-FID-1_determinism": {
            "cosine": det_cos, "max_abs_diff": det_maxabs, "pass": bool(bb_fid1_pass),
            "target_cosine_min": fid["BB-FID-1_determinism_cosine_min"],
            "target_maxabs_max": fid["BB-FID-1_determinism_maxabs_diff_max"]},
        "BB-FID-2_recipe_parity": {
            "knobs_match_AL_3_2": bool(knobs_match),
            "cell_yaml_knobs": {"pca_seed": seed, "pca_components": N_PCA,
                                "n_splits": N_SPLITS, "fit_layers": {"propensity": L_PROP,
                                "caution": L_CAUTION}},
            "STOP_note": (
                "gates.yaml literal wording is 'freeze_scorer.py sha256 == H9 "
                "pinned scorer'. A whole-FILE hash match against H9's pin "
                f"({H9_FREEZE_SCORER_PIN_SHA256}) is not achievable: this file "
                "necessarily differs from H9's freeze_scorer.py in I/O (BB's "
                "own base extraction/grades, not AL's al_run_dir/al_extract_dir/"
                "al_graded) and in the fidelity-reporting code (BB has no "
                "on-disk prior array to cross-reference, per AMENDMENT.md "
                "5.4). This build implements BB-FID-2 as FUNCTION-LEVEL "
                "verbatim-copy parity instead (unit/load_stack/oof_caution/"
                "oof_meandiff_proj and the fit_frozen_scorer sequence are "
                "copied from H9's freeze_scorer.py unchanged) plus the knob "
                "assertion above. Flagged for lead adjudication, not resolved "
                "unilaterally since gates.yaml is pinned."),
            "h9_pinned_freeze_scorer_sha256": H9_FREEZE_SCORER_PIN_SHA256,
            "this_file_sha256": this_file_sha256,
            "pass": bool(knobs_match)},
        "honest_prior_NONGATING": {
            "prop_incell_oof_auroc": prop_incell_oof_auroc,
            "caution_incell_oof_auroc": caution_incell_oof_auroc,
            "caution_incell_auroc_frozen_fullsample": fit_a["caution_incell_auroc_frozen"],
            "fullsample_prop_incell_auroc": fit_a["fullsample_prop_incell_auroc_NONGATING"]},
        "fidelity_pass": bool(bb_fid1_pass and knobs_match),
        "frozen_out": str(frozen_out),
    }
    (frozen_out / "fidelity_report.json").write_text(json.dumps(report, indent=2))
    return report


def _load_real_inputs(cell: dict, exp_dir: Path, fit_extract_dir: Path | None,
                      fit_graded: Path | None):
    fs = cell["phase1"]["fit_surface"]
    extract_dir = fit_extract_dir or (exp_dir / "analysis/phase1/fit/extract/data")
    graded_path = fit_graded or (exp_dir / "analysis/phase1/fit/rows_graded.jsonl")
    rows = load_jsonl(graded_path)
    assert len(rows) == fs["n_rows"], f"expected {fs['n_rows']} rows, got {len(rows)}"
    row_keys = [r["row_key"] for r in rows]
    stack = load_stack(extract_dir, row_keys)
    L_PROP = cell["phase1"]["scorer"]["fit_layers"]["propensity"]
    L_CAUTION = cell["phase1"]["scorer"]["fit_layers"]["caution"]
    X24 = stack[:, L_PROP, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    return X24, X35, rows


def _synthetic_smoke_inputs(seed: int = 0, n: int = 400, dim: int = 2560):
    """Fake activations for --smoke: no GPU, no real data. Exercises the exact
    fit + persistence + fidelity path so a build-time defect is caught before
    any GPU spend, matching H9's --selftest posture in score_holdout.py."""
    rng = np.random.default_rng(seed)
    is_confab = np.zeros(n, dtype=bool)
    is_confab[:40] = True
    is_un_ref = np.zeros(n, dtype=bool)
    is_un_ref[40:400] = True
    X24 = rng.normal(0, 1, (n, dim)) + is_confab.reshape(-1, 1) * 0.6
    X35 = rng.normal(0, 1, (n, dim)) + is_un_ref.reshape(-1, 1) * 1.2
    rows = []
    for i in range(n):
        gc = "unanswerable" if (is_confab[i] or is_un_ref[i]) else "answerable"
        rows.append({"row_key": f"smoke::{i:04d}", "gold_class": gc,
                    "answered": bool(is_confab[i]), "refused": bool(is_un_ref[i])})
    return X24, X35, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    ap.add_argument("--fit-extract-dir", default=None)
    ap.add_argument("--fit-graded", default=None)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    gates = yaml.safe_load(Path(args.gates).read_text())

    if args.smoke:
        X24, X35, rows = _synthetic_smoke_inputs()
    else:
        X24, X35, rows = _load_real_inputs(
            cell, exp_dir,
            Path(args.fit_extract_dir) if args.fit_extract_dir else None,
            Path(args.fit_graded) if args.fit_graded else None)

    report = build_and_verify(cell, gates, X24, X35, rows, exp_dir, args.smoke)
    print(json.dumps(report, indent=2))
    return 0 if report["fidelity_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
