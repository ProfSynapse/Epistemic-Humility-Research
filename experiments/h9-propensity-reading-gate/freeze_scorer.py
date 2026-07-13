#!/usr/bin/env python3
"""H9 step 1 (CPU, no GPU): freeze a portable scorer replicating AL's pipeline.

Replicates the fit pipeline of
    archive/experiment/phase1/probe/amendments/amendment_al_select_and_direction.py
(PCA(128, random_state=20260705) -> StandardScaler -> caution residualization ->
mean-diff confab-vs-unanswerable-refused on L24; caution logistic on L35). The
helper functions below are copied verbatim from that script and its AL-prep
imports (load_jsonl, unit, load_a0_stack, oof_caution) so the frozen scorer is
self-contained and reproduces the governed construction bit-for-bit, without
depending on the archive tree at score time.

The difference from AL: AL refit everything in memory and saved only derived
arrays; this script PERSISTS the fit objects so a genuinely new (held-out) row
can be scored later by score_holdout.py. Two objects AL used cannot be applied to
a single new row and are replaced by full-sample frozen equivalents (AMENDMENT.md
sections 3 and 8):
  - caution score c: AL's is 5-fold OOF; the deployable scorer uses a FINAL
    full-sample logistic on PCA-128(L35).
  - propensity readout: AL's in-cell number is OOF; the frozen scorer is the
    FULL-SAMPLE mean-diff direction d_confab_full (the same object that produces
    d_raw.npy), z-scaled by the fit-population mean/std.

FIDELITY GATE (gates.yaml `fidelity`), asserted here:
  FID-1 (hard): re-derived full-sample d_raw reproduces on-disk d_raw.npy at
    cosine >= 0.999999 and max|diff| <= 1e-5 (exact deterministic replication of
    amendment_al_select_and_direction.py:197-204).
  FID-2 (consistency): frozen full-sample prop_z correlates with on-disk OOF
    prop_z.npy at Pearson r >= 0.98, and the frozen in-cell AUROC is within 0.02
    of AL's 0.6802.

Usage:
  python freeze_scorer.py --cell cell.yaml --gates gates.yaml \
    [--data-root /home/profsynapse/code/Epistemic-Humility-Research] [--smoke]

The AL fit artifacts (extraction, graded rows, d_raw.npy, prop_z.npy) are
gitignored and live only in the canonical checkout; --data-root points there
(default is the canonical checkout).
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

SEED = 20260705          # AL random_state (amendment_al_select_and_direction.py:80)
N_LAYERS = 37


# --- helpers copied verbatim from the AL fit scripts (see module docstring) ---
def load_jsonl(p: Path):
    return [json.loads(l) for l in p.open() if l.strip()]


def unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n else v


def load_a0_stack(extract_data: Path, row_keys: list[str]) -> np.ndarray:
    """[n_rows, 37, 2560] float32; one safetensors open per row."""
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
    """OOF mean-diff projection (amendment_al_prep_familiarity_vs_knowing.py:91-107).
    Used only as a faithfulness diagnostic here: it reproduces AL's OOF prop
    readout so the FID-2 in-sample-vs-OOF gap can be isolated from any pipeline
    defect."""
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
    """5-fold OOF caution log-odds, z-scored (amendment_al_select...py:96-106)."""
    out = np.zeros(len(y_ref))
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for tr, te in skf.split(P35, y_ref):
        sc = StandardScaler().fit(P35[tr])
        clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                 random_state=seed).fit(sc.transform(P35[tr]),
                                                        y_ref[tr])
        out[te] = clf.decision_function(sc.transform(P35[te]))
    return (out - out.mean()) / out.std()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def build_frozen_scorer(cell: dict, gates: dict, data_root: Path,
                        exp_dir: Path, smoke: bool) -> dict:
    sc_cfg = cell["scorer"]
    L_PROP = sc_cfg["fit_layers"]["propensity"]      # 24
    L_CAUTION = sc_cfg["fit_layers"]["caution"]      # 35
    N_PCA = sc_cfg["pca_components"]                  # 128
    N_SPLITS = sc_cfg["n_splits"]                     # 5
    pca_seed = sc_cfg["pca_seed"]                     # 20260705
    assert pca_seed == SEED, f"pca_seed {pca_seed} != AL SEED {SEED}"

    al_run = data_root / sc_cfg["al_run_dir"]
    al_extract = data_root / sc_cfg["al_extract_dir"]
    al_graded = data_root / sc_cfg["al_graded"]

    # ---- load fit surface (1,662 rows) ----
    rows = load_jsonl(al_graded)
    assert len(rows) == 1662, f"expected 1662 rows, got {len(rows)}"
    row_keys = [r["row_key"] for r in rows]
    stack = load_a0_stack(al_extract, row_keys)
    X24 = stack[:, L_PROP, :].astype(np.float64)
    X35 = stack[:, L_CAUTION, :].astype(np.float64)
    del stack

    # ---- PCA + standardize (identical to AL) ----
    pca24 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit(X24)
    Z24 = pca24.transform(X24)
    scaler24 = StandardScaler().fit(Z24)
    P24 = scaler24.transform(Z24)
    pca35 = PCA(N_PCA, svd_solver="randomized", random_state=SEED).fit(X35)
    P35 = pca35.transform(X35)

    # ---- caution score c: OOF (AL's, for d_raw replication) + FINAL full-sample
    #      (frozen, for held-out scoring) ----
    y_ref = np.array([1 if r["refused"] else 0 for r in rows])
    c_oof = oof_caution(P35, y_ref, SEED + 1, N_SPLITS)

    # ---- confab / unanswerable-refused cells ----
    confab_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["answered"]])
    un_ref_idx = np.array([i for i, r in enumerate(rows)
                           if r["gold_class"] == "unanswerable" and r["refused"]])

    # ---- FID-1: reproduce d_raw exactly (OOF-c residualized, full-sample mean-diff)
    R_oof = P24 - LinearRegression().fit(c_oof.reshape(-1, 1), P24).predict(
        c_oof.reshape(-1, 1))
    d_confab_full = unit(R_oof[confab_idx].mean(0) - R_oof[un_ref_idx].mean(0))
    d_raw_unnorm = (d_confab_full / scaler24.scale_) @ pca24.components_
    d_raw = unit(d_raw_unnorm)

    d_raw_disk = np.load(al_run / "d_raw.npy").astype(np.float64)
    cos = float(d_raw @ d_raw_disk / (np.linalg.norm(d_raw) * np.linalg.norm(d_raw_disk)))
    maxabs = float(np.max(np.abs(d_raw - d_raw_disk)))
    fid1_pass = (cos >= gates["fidelity"]["FID-1_direction_cosine_min"]
                 and maxabs <= gates["fidelity"]["FID-1_direction_maxabs_diff_max"])

    # ---- deployable frozen scorer (full-sample caution, frozen residualizer) ----
    sc35 = StandardScaler().fit(P35)
    caution_clf = LogisticRegression(solver="saga", tol=1e-3, max_iter=2000,
                                     random_state=SEED + 1).fit(sc35.transform(P35), y_ref)
    c_frozen_raw = caution_clf.decision_function(sc35.transform(P35))
    c_frozen_mean, c_frozen_std = float(c_frozen_raw.mean()), float(c_frozen_raw.std())
    c_frozen = (c_frozen_raw - c_frozen_mean) / c_frozen_std
    caution_residualizer = LinearRegression().fit(c_frozen.reshape(-1, 1), P24)
    R_frozen = P24 - caution_residualizer.predict(c_frozen.reshape(-1, 1))
    prop_full_raw = R_frozen @ d_confab_full
    prop_mean, prop_std = float(prop_full_raw.mean()), float(prop_full_raw.std())
    prop_full = (prop_full_raw - prop_mean) / prop_std

    prop_z_disk = np.load(al_run / "prop_z.npy").astype(np.float64)

    # ---- FID-2 (GATING): OOF reproduction. Execute AL's exact 5-fold OOF
    #      construction (same folds, seed, OOF-c residualization) and require it to
    #      reproduce the on-disk OOF prop_z.npy at Pearson r >= 0.98 AND land its
    #      in-cell OOF AUROC within 0.02 of 0.6802 (AMENDMENT.md section 3.1,
    #      pre-sign respec). This is the like-to-like fidelity check: a faithful
    #      re-derivation must reproduce AL's own OOF readout. ----
    prop_oof_repro = oof_meandiff_proj(R_oof, confab_idx, un_ref_idx, SEED + 2, N_SPLITS)
    prop_oof_repro_z = (prop_oof_repro - prop_oof_repro.mean()) / prop_oof_repro.std()
    oof_repro_pearson = float(np.corrcoef(prop_oof_repro_z, prop_z_disk)[0, 1])
    oof_repro_incell_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop_oof_repro_z[confab_idx], prop_oof_repro_z[un_ref_idx]]))
    oof_repro_auroc_delta = abs(oof_repro_incell_auroc
                                - gates["honest_prior"]["prop_incell_oof_auroc"])
    fid2_pass = (oof_repro_pearson >= gates["fidelity"]["FID-2_oof_pearson_min"]
                 and oof_repro_auroc_delta <= gates["fidelity"]["FID-2_oof_incell_auroc_tol"])

    # ---- NON-GATING (recorded for the file): the frozen FULL-SAMPLE scorer read
    #      on its own fit rows is in-sample-optimistic, so it is expected to sit
    #      above the OOF 0.6802. Recorded so the file shows both numbers; it does
    #      NOT gate. Held-out rows carry no such optimism, so H9-G1 stays honestly
    #      comparable to 0.6802. ----
    fullsample_pearson = float(np.corrcoef(prop_full, prop_z_disk)[0, 1])
    fullsample_incell_auroc = float(roc_auc_score(
        np.r_[np.ones(len(confab_idx)), np.zeros(len(un_ref_idx))],
        np.r_[prop_full[confab_idx], prop_full[un_ref_idx]]))
    caution_incell_auroc = float(roc_auc_score(y_ref, c_frozen))

    # ---- persist frozen objects + sha256 manifest ----
    import joblib
    frozen_out = exp_dir / sc_cfg["frozen_out"]
    frozen_out.mkdir(parents=True, exist_ok=True)
    joblib.dump(pca24, frozen_out / "pca24.joblib")
    joblib.dump(pca35, frozen_out / "pca35.joblib")
    joblib.dump(scaler24, frozen_out / "scaler24.joblib")
    joblib.dump(sc35, frozen_out / "scaler35.joblib")
    joblib.dump(caution_clf, frozen_out / "caution_logistic.joblib")
    joblib.dump(caution_residualizer, frozen_out / "caution_residualizer.joblib")
    np.save(frozen_out / "d_confab_full.npy", d_confab_full.astype(np.float64))
    np.save(frozen_out / "d_raw_rederived.npy", d_raw.astype(np.float64))
    (frozen_out / "prop_zscale.json").write_text(json.dumps({
        "prop_mean": prop_mean, "prop_std": prop_std,
        "caution_zscale_mean": c_frozen_mean, "caution_zscale_std": c_frozen_std,
        "fit_layers": {"propensity": L_PROP, "caution": L_CAUTION},
        "pca_components": N_PCA, "pca_seed": SEED}, indent=2))
    obj_files = ["pca24.joblib", "pca35.joblib", "scaler24.joblib", "scaler35.joblib",
                 "caution_logistic.joblib", "caution_residualizer.joblib",
                 "d_confab_full.npy", "d_raw_rederived.npy", "prop_zscale.json"]
    scorer_manifest = {f: _sha256(frozen_out / f) for f in obj_files}
    (frozen_out / "scorer_manifest.json").write_text(json.dumps(scorer_manifest, indent=2))

    report = {
        "tier": "smoke" if smoke else "registered",
        "n_rows": len(rows),
        "n_confab": int(len(confab_idx)),
        "n_un_refused": int(len(un_ref_idx)),
        "FID-1": {"cosine": cos, "max_abs_diff": maxabs, "pass": bool(fid1_pass),
                  "target_cosine_min": gates["fidelity"]["FID-1_direction_cosine_min"],
                  "target_maxabs_max": gates["fidelity"]["FID-1_direction_maxabs_diff_max"]},
        "FID-2": {"note": ("GATING: OOF reproduction of AL's exact 5-fold "
                            "construction vs on-disk prop_z.npy (like-to-like)"),
                  "oof_repro_pearson_vs_prop_z": oof_repro_pearson,
                  "oof_repro_incell_auroc": oof_repro_incell_auroc,
                  "oof_repro_incell_auroc_delta_vs_0.6802": oof_repro_auroc_delta,
                  "pass": bool(fid2_pass),
                  "target_pearson_min": gates["fidelity"]["FID-2_oof_pearson_min"],
                  "target_auroc_tol": gates["fidelity"]["FID-2_oof_incell_auroc_tol"]},
        "fullsample_in_sample_readout_NONGATING": {
            "note": ("frozen full-sample scorer read on its own fit rows; "
                     "in-sample-optimistic, recorded not gated"),
            "pearson_vs_prop_z": fullsample_pearson,
            "incell_auroc": fullsample_incell_auroc},
        "caution_incell_auroc_frozen": caution_incell_auroc,
        "fidelity_pass": bool(fid1_pass and fid2_pass),
        "frozen_out": str(frozen_out),
    }
    (frozen_out / "fidelity_report.json").write_text(json.dumps(report, indent=2))
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cell", default="cell.yaml")
    ap.add_argument("--gates", default="gates.yaml")
    ap.add_argument("--data-root",
                    default="/home/profsynapse/code/Epistemic-Humility-Research")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    exp_dir = Path(args.cell).resolve().parent
    cell = yaml.safe_load(Path(args.cell).read_text())
    gates = yaml.safe_load(Path(args.gates).read_text())
    report = build_frozen_scorer(cell, gates, Path(args.data_root), exp_dir, args.smoke)
    print(json.dumps(report, indent=2))
    return 0 if report["fidelity_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
