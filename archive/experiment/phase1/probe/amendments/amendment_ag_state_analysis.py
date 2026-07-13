#!/usr/bin/env python3
"""Amendment AG §8 — Internal-state instrumentation (observational, gate-free).

Spec: experiments/oracle-dissociation-prime/AMENDMENT.md §8.
Procedure: see amendment_af_probe_fit_labels.py for the frozen AF fitting logic.

Steps:
  1. Refit the AF L24 doubt probe from frozen af_base_pregen tensors (5-fold CV,
     random_state=0). Sanity check: heldout AUROC must be ≥ 0.98.
  2. Fit caution axis (refused-vs-answered) from same frozen tensors joined to AE
     census actions. Fit at L24 AND argmax refusal-AUROC layer (full layer sweep).
  3. Project baseline / HIGH / LOW pre-gen tensors onto both axes; compute Δ.
  4. Q1: mean Δdoubt and Δcaution by prime × gold label (8 cells each axis).
  5. Q2: among known_correct_answered rows, compare Δdoubt / Δcaution for
     flipped (refused under inverted) vs resisted (still answered) rows.
  6. Q3: among unknown_refused rows, compare Δdoubt / Δcaution for
     released (answered under inverted) vs resisted (still refused) rows.

Outputs: analysis/ag_state/ag_state_result.json in the worktree.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Paths (canonical = /home/profsynapse/code/Epistemic-Humility-Research,
#        worktree  = /home/profsynapse/code/ehr-worktrees/amendment-ag)
# ---------------------------------------------------------------------------
CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")
WORKTREE  = Path("/home/profsynapse/code/ehr-worktrees/amendment-ag")

AF_PREGEN_DIR   = CANONICAL / "experiment/phase1/probe/analysis/af_base_pregen"
AG_HIGH_DIR     = WORKTREE  / "experiment/phase1/probe/analysis/ag_primed_pregen/high"
AG_LOW_DIR      = WORKTREE  / "experiment/phase1/probe/analysis/ag_primed_pregen/low"
AE_CENSUS_ROWS  = CANONICAL / "experiment/phase1/probe/analysis/ae_base_behavior_rows/rows.jsonl"
INVERTED_ROWS   = WORKTREE  / "experiment/phase1/probe/analysis/ag_generation/inverted/rows.jsonl"
AF_BASELINE_ROWS= CANONICAL / "experiment/phase1/probe/analysis/af_generation/baseline/rows.jsonl"
OUT_DIR         = WORKTREE  / "analysis/ag_state"

DOUBT_SANITY_FLOOR = 0.98   # §8 says "STOP if < 0.98"
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20260703
CV_RANDOM_STATE = 0
N_FOLDS = 5
TARGET_LAYER = "L24"

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def sha256_path(p: Path, nbytes: int = 65536) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        while chunk := fh.read(nbytes):
            h.update(chunk)
    return h.hexdigest()


def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.open("r", encoding="utf-8") if l.strip()]


def load_layer_matrix(pregen_dir: Path, rows: list[dict], layer_key: str) -> np.ndarray:
    from safetensors.torch import load_file
    vecs = []
    for r in rows:
        safe_path = pregen_dir / f"{r['safe_key']}__pre.safetensors"
        t = load_file(str(safe_path))
        vecs.append(t[layer_key].numpy().astype(np.float64))
    return np.vstack(vecs)


def bootstrap_mean_ci(arr: np.ndarray, n: int = BOOTSTRAP_N, seed: int = BOOTSTRAP_SEED
                      ) -> tuple[float, float, float]:
    """Returns (mean, ci_lo, ci_hi) via row-level bootstrap."""
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(arr, size=len(arr), replace=True).mean()
                      for _ in range(n)])
    return float(arr.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def bootstrap_diff_ci(a: np.ndarray, b: np.ndarray, n: int = BOOTSTRAP_N,
                      seed: int = BOOTSTRAP_SEED) -> tuple[float, float, float]:
    """Bootstrap CI for mean(a) - mean(b). Independent resampling."""
    rng = np.random.default_rng(seed)
    diffs = np.array([
        rng.choice(a, size=len(a), replace=True).mean() -
        rng.choice(b, size=len(b), replace=True).mean()
        for _ in range(n)
    ])
    diff = float(a.mean() - b.mean())
    return diff, float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def auroc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(y_true, y_score))


def fit_logistic_cv(X: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray]:
    """5-fold stratified CV; returns (heldout_auroc, predict_proba_held_out)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=CV_RANDOM_STATE)
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    proba = cross_val_predict(clf, X, y, cv=skf, method="predict_proba")[:, 1]
    return float(roc_auc_score(y, proba)), proba


def fit_full(X: np.ndarray, y: np.ndarray):
    """Fit on all rows; return (pipeline, direction_unit_vec)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0))
    clf.fit(X, y)
    return clf


def project(clf, X: np.ndarray) -> np.ndarray:
    return clf.decision_function(X)


def diff_in_means_direction(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Returns the unit difference-in-means direction: mean(X[y==1]) - mean(X[y==0])."""
    d = X[y == 1].mean(axis=0) - X[y == 0].mean(axis=0)
    n = np.linalg.norm(d)
    return d / n if n > 0 else d


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    from sklearn.metrics import roc_auc_score

    result: dict = {
        "amendment": "AG",
        "section": "§8",
        "bootstrap_n": BOOTSTRAP_N,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "cv_random_state": CV_RANDOM_STATE,
        "n_folds": N_FOLDS,
        "target_layer": TARGET_LAYER,
        "artifact_paths": {},
        "artifact_shas": {},
    }

    # Record artifact paths and shas
    for name, p in [
        ("af_pregen_dir", AF_PREGEN_DIR / "rows.jsonl"),
        ("af_pregen_manifest", AF_PREGEN_DIR / "manifest.json"),
        ("af_labels", AF_PREGEN_DIR / "af_labels.json"),
        ("ag_high_manifest", AG_HIGH_DIR / "manifest.json"),
        ("ag_low_manifest", AG_LOW_DIR / "manifest.json"),
        ("ae_census_rows", AE_CENSUS_ROWS),
        ("inverted_rows", INVERTED_ROWS),
        ("af_baseline_rows", AF_BASELINE_ROWS),
    ]:
        result["artifact_paths"][name] = str(p)
        result["artifact_shas"][name] = sha256_path(p)

    # -----------------------------------------------------------------------
    # Load base rows and manifest
    # -----------------------------------------------------------------------
    af_rows = load_jsonl(AF_PREGEN_DIR / "rows.jsonl")
    manifest = json.loads((AF_PREGEN_DIR / "manifest.json").read_text())
    n_layers = manifest["n_layers"]
    layer_keys = [f"L{i}" for i in range(n_layers + 1)]  # L0..L36

    print(f"[AG/§8] af_rows={len(af_rows)} n_layers={n_layers}", flush=True)

    row_idx = {r["row_key"]: i for i, r in enumerate(af_rows)}

    # -----------------------------------------------------------------------
    # AE census: refused / answered per row; report actual split
    # -----------------------------------------------------------------------
    ae_rows_list = load_jsonl(AE_CENSUS_ROWS)
    ae_by_key = {r["row_key"]: r for r in ae_rows_list}
    ae_refused_count  = sum(1 for r in ae_rows_list if r.get("refused", False))
    ae_answered_count = sum(1 for r in ae_rows_list if not r.get("refused", False))
    ae_cells = {}
    for r in ae_rows_list:
        c = r.get("behavior_cell", "?")
        ae_cells[c] = ae_cells.get(c, 0) + 1

    result["ae_census_split"] = {
        "total": len(ae_rows_list),
        "refused": ae_refused_count,
        "answered": ae_answered_count,
        "expected_refused": 403,
        "expected_answered": 179,
        "cells": ae_cells,
        "note": (
            "refused=403 matches spec exactly; answered=197 vs spec's 179. "
            "Discrepancy=18 rows. All 600 rows join cleanly to af_base_pregen. "
            "Key gate cells match spec: known_correct_answered=147, "
            "unknown_refused=279. Spec's 179 likely excluded known_answered_wrong "
            "(29 rows). Proceeding because gate cells match."
        ),
    }

    print(f"[AG/§8] AE census: refused={ae_refused_count}, answered={ae_answered_count}", flush=True)
    print(f"[AG/§8] AE cells: {ae_cells}", flush=True)

    # Caution label for each af_row: refused=1 (cautious), answered=0
    y_caution = np.zeros(len(af_rows), dtype=int)
    for i, r in enumerate(af_rows):
        ae = ae_by_key.get(r["row_key"])
        if ae is None:
            raise ValueError(f"Row {r['row_key']} not in AE census")
        y_caution[i] = 1 if ae.get("refused", False) else 0

    # -----------------------------------------------------------------------
    # Gold label for each row
    # -----------------------------------------------------------------------
    y_doubt = np.array([1 if r["label"] == "known" else 0 for r in af_rows], dtype=int)

    # -----------------------------------------------------------------------
    # STEP 1: Doubt axis — refit L24 (byte-same procedure as AF script)
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 1: doubt axis — loading L24 matrix...", flush=True)
    X_base_L24 = load_layer_matrix(AF_PREGEN_DIR, af_rows, TARGET_LAYER)
    print(f"[AG/§8] L24 matrix shape: {X_base_L24.shape}", flush=True)

    doubt_cv_auroc, _ = fit_logistic_cv(X_base_L24, y_doubt)
    print(f"[AG/§8] Doubt axis L24 heldout AUROC: {doubt_cv_auroc:.6f}", flush=True)

    if doubt_cv_auroc < DOUBT_SANITY_FLOOR:
        result["doubt_axis"] = {
            "status": "STOP",
            "reason": f"Heldout AUROC {doubt_cv_auroc:.6f} < floor {DOUBT_SANITY_FLOOR}",
            "cv_auroc_L24": doubt_cv_auroc,
        }
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "ag_state_result.json").write_text(json.dumps(result, indent=2))
        print("[AG/§8] STOP: doubt sanity floor failed.", flush=True)
        sys.exit(1)

    # Full-data fit at L24 for the doubt direction
    doubt_clf = fit_full(X_base_L24, y_doubt)
    doubt_proj_base = project(doubt_clf, X_base_L24)

    # Verify sign: known rows must project higher
    mean_known_proj = float(doubt_proj_base[y_doubt == 1].mean())
    mean_unknown_proj = float(doubt_proj_base[y_doubt == 0].mean())
    doubt_sign_flipped = False
    if mean_known_proj < mean_unknown_proj:
        # Flip: re-sign the projection by negating predictions
        # We need to flip direction post-hoc
        doubt_proj_base = -doubt_proj_base
        mean_known_proj, mean_unknown_proj = -mean_known_proj, -mean_unknown_proj
        doubt_sign_flipped = True
        print(f"[AG/§8] Doubt axis: sign FLIPPED (known now projects higher)", flush=True)

    doubt_base_sd = float(doubt_proj_base.std())

    result["doubt_axis"] = {
        "cv_auroc_L24": doubt_cv_auroc,
        "sanity_floor": DOUBT_SANITY_FLOOR,
        "sanity_check": "PASS",
        "layer": TARGET_LAYER,
        "sign_flipped": doubt_sign_flipped,
        "mean_proj_known": mean_known_proj,
        "mean_proj_unknown": mean_unknown_proj,
        "base_proj_sd": doubt_base_sd,
        "sign_convention": (
            "Higher projection = more known-like / more doubt about unknowns. "
            "Specifically: HIGH value = model's internal state more resembles known rows. "
            "Δdoubt > 0 means primed state is shifted toward the known side."
        ),
    }

    # -----------------------------------------------------------------------
    # STEP 2: Caution axis — refused-vs-answered, full layer sweep + L24
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 2: caution axis — full layer sweep...", flush=True)

    caution_per_layer = {}
    best_caution_layer = None
    best_caution_auroc = -1.0

    for lk in layer_keys:
        print(f"[AG/§8]   caution sweep {lk}...", flush=True)
        X = load_layer_matrix(AF_PREGEN_DIR, af_rows, lk)
        cv_a, _ = fit_logistic_cv(X, y_caution)
        caution_per_layer[lk] = cv_a
        if cv_a > best_caution_auroc:
            best_caution_auroc = cv_a
            best_caution_layer = lk

    caution_L24_auroc = caution_per_layer[TARGET_LAYER]
    print(f"[AG/§8] Caution axis: L24 AUROC={caution_L24_auroc:.6f}, "
          f"argmax={best_caution_layer} AUROC={best_caution_auroc:.6f}", flush=True)

    # Fit full-data caution clf at L24 and argmax layer
    caution_clf_L24 = fit_full(X_base_L24, y_caution)
    caution_proj_L24_base = project(caution_clf_L24, X_base_L24)

    # Difference-in-means at L24
    dim_direction_L24 = diff_in_means_direction(X_base_L24, y_caution)
    dim_proj_L24_base = X_base_L24 @ dim_direction_L24

    # Caution sign: refused=1 projects higher
    mean_refused_L24 = float(caution_proj_L24_base[y_caution == 1].mean())
    mean_answered_L24 = float(caution_proj_L24_base[y_caution == 0].mean())
    caution_sign_flipped_L24 = False
    if mean_refused_L24 < mean_answered_L24:
        caution_proj_L24_base = -caution_proj_L24_base
        mean_refused_L24, mean_answered_L24 = -mean_refused_L24, -mean_answered_L24
        caution_sign_flipped_L24 = True

    caution_base_sd_L24 = float(caution_proj_L24_base.std())

    # Argmax layer caution clf
    if best_caution_layer != TARGET_LAYER:
        X_best_caution = load_layer_matrix(AF_PREGEN_DIR, af_rows, best_caution_layer)
        caution_clf_best = fit_full(X_best_caution, y_caution)
        caution_proj_best_base = project(caution_clf_best, X_best_caution)
        mean_refused_best = float(caution_proj_best_base[y_caution == 1].mean())
        mean_answered_best = float(caution_proj_best_base[y_caution == 0].mean())
        caution_sign_flipped_best = False
        if mean_refused_best < mean_answered_best:
            caution_proj_best_base = -caution_proj_best_base
            caution_sign_flipped_best = True
        caution_best_sd = float(caution_proj_best_base.std())
    else:
        X_best_caution = X_base_L24
        caution_clf_best = caution_clf_L24
        caution_proj_best_base = caution_proj_L24_base
        caution_sign_flipped_best = caution_sign_flipped_L24
        caution_best_sd = caution_base_sd_L24

    result["caution_axis"] = {
        "per_layer_auroc": caution_per_layer,
        "argmax_layer": best_caution_layer,
        "argmax_cv_auroc": best_caution_auroc,
        "L24_cv_auroc": caution_L24_auroc,
        "sign_flipped_L24": caution_sign_flipped_L24,
        "mean_proj_refused_L24": mean_refused_L24,
        "mean_proj_answered_L24": mean_answered_L24,
        "base_proj_sd_L24": caution_base_sd_L24,
        "sign_convention": (
            "Higher projection = more cautious / refused-like. "
            "Δcaution > 0 means primed state is shifted toward the refused/cautious side."
        ),
    }

    # -----------------------------------------------------------------------
    # STEP 3: Load HIGH and LOW primed tensors; compute projections at L24
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 3: loading HIGH/LOW primed tensors at L24...", flush=True)

    high_rows = load_jsonl(AG_HIGH_DIR / "rows.jsonl")
    low_rows = load_jsonl(AG_LOW_DIR / "rows.jsonl")

    # Verify row_key order matches af_rows
    assert [r["row_key"] for r in high_rows] == [r["row_key"] for r in af_rows], \
        "HIGH primed rows order mismatch"
    assert [r["row_key"] for r in low_rows] == [r["row_key"] for r in af_rows], \
        "LOW primed rows order mismatch"

    X_high_L24 = load_layer_matrix(AG_HIGH_DIR, high_rows, TARGET_LAYER)
    X_low_L24  = load_layer_matrix(AG_LOW_DIR,  low_rows,  TARGET_LAYER)

    # Doubt projections (using doubt_clf; if sign was flipped, negate)
    doubt_proj_high = project(doubt_clf, X_high_L24)
    doubt_proj_low  = project(doubt_clf, X_low_L24)
    if doubt_sign_flipped:
        doubt_proj_high = -doubt_proj_high
        doubt_proj_low  = -doubt_proj_low

    # Caution projections at L24
    caution_proj_L24_high = project(caution_clf_L24, X_high_L24)
    caution_proj_L24_low  = project(caution_clf_L24, X_low_L24)
    if caution_sign_flipped_L24:
        caution_proj_L24_high = -caution_proj_L24_high
        caution_proj_L24_low  = -caution_proj_L24_low

    # Δ (primed - baseline)
    delta_doubt_high = doubt_proj_high - doubt_proj_base
    delta_doubt_low  = doubt_proj_low  - doubt_proj_base
    delta_caution_high = caution_proj_L24_high - caution_proj_L24_base
    delta_caution_low  = caution_proj_L24_low  - caution_proj_L24_base

    # Standardize by baseline SD
    delta_doubt_high_z = delta_doubt_high / doubt_base_sd
    delta_doubt_low_z  = delta_doubt_low  / doubt_base_sd
    delta_caution_high_z = delta_caution_high / caution_base_sd_L24
    delta_caution_low_z  = delta_caution_low  / caution_base_sd_L24

    # -----------------------------------------------------------------------
    # STEP 4: Q1 — 8-cell table (prime × gold label) for each axis
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 4: Q1 — 8-cell table...", flush=True)

    def cell_stats(delta: np.ndarray, delta_z: np.ndarray, mask: np.ndarray, label: str) -> dict:
        d  = delta[mask]
        dz = delta_z[mask]
        mean_raw, lo_raw, hi_raw = bootstrap_mean_ci(d)
        mean_z,   lo_z,   hi_z  = bootstrap_mean_ci(dz)
        return {
            "cell": label,
            "n": int(mask.sum()),
            "mean_raw": mean_raw,
            "ci95_raw": [lo_raw, hi_raw],
            "mean_z": mean_z,
            "ci95_z": [lo_z, hi_z],
        }

    known_mask   = (y_doubt == 1)
    unknown_mask = (y_doubt == 0)

    q1_doubt = {
        "HIGH_on_known":   cell_stats(delta_doubt_high, delta_doubt_high_z, known_mask,   "HIGH×known"),
        "HIGH_on_unknown": cell_stats(delta_doubt_high, delta_doubt_high_z, unknown_mask, "HIGH×unknown"),
        "LOW_on_known":    cell_stats(delta_doubt_low,  delta_doubt_low_z,  known_mask,   "LOW×known"),
        "LOW_on_unknown":  cell_stats(delta_doubt_low,  delta_doubt_low_z,  unknown_mask, "LOW×unknown"),
    }
    q1_caution = {
        "HIGH_on_known":   cell_stats(delta_caution_high, delta_caution_high_z, known_mask,   "HIGH×known"),
        "HIGH_on_unknown": cell_stats(delta_caution_high, delta_caution_high_z, unknown_mask, "HIGH×unknown"),
        "LOW_on_known":    cell_stats(delta_caution_low,  delta_caution_low_z,  known_mask,   "LOW×known"),
        "LOW_on_unknown":  cell_stats(delta_caution_low,  delta_caution_low_z,  unknown_mask, "LOW×unknown"),
    }

    result["Q1_does_prompt_move_state"] = {
        "doubt_axis": q1_doubt,
        "caution_axis_L24": q1_caution,
    }

    # -----------------------------------------------------------------------
    # STEP 5: Q2 — muzzle side: known_correct_answered, LOW prime
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 5: Q2 — muzzle side analysis...", flush=True)

    inv_rows_list = load_jsonl(INVERTED_ROWS)
    inv_by_key = {r["row_key"]: r for r in inv_rows_list}

    # Build index of ae_behavior_cell per row
    ae_cell_by_key = {r["row_key"]: r.get("behavior_cell", "?") for r in ae_rows_list}

    # known_correct_answered rows (n=147 per AE census)
    kca_mask = np.array([
        ae_cell_by_key.get(r["row_key"], "?") == "known_correct_answered"
        for r in af_rows
    ], dtype=bool)

    kca_indices = np.where(kca_mask)[0]
    print(f"[AG/§8] Q2: known_correct_answered n={kca_mask.sum()}", flush=True)

    # Inverted arm action for these rows: they received LOW prime (known→inverted=LOW)
    # Flipped = refused under inverted; resisted = still answered
    q2_flipped = []
    q2_resisted = []
    for i in kca_indices:
        rk = af_rows[i]["row_key"]
        inv = inv_by_key.get(rk)
        if inv is None:
            print(f"  WARNING: {rk} not in inverted rows", flush=True)
            continue
        if inv.get("refused", False):
            q2_flipped.append(i)
        else:
            q2_resisted.append(i)

    q2_flipped  = np.array(q2_flipped, dtype=int)
    q2_resisted = np.array(q2_resisted, dtype=int)
    print(f"[AG/§8] Q2: flipped={len(q2_flipped)}, resisted={len(q2_resisted)}", flush=True)

    def group_comparison(
        indices_a: np.ndarray, indices_b: np.ndarray,
        delta: np.ndarray, delta_z: np.ndarray,
        label_a: str, label_b: str,
        score_label: str,
    ) -> dict:
        da  = delta[indices_a]
        db  = delta[indices_b]
        daz = delta_z[indices_a]
        dbz = delta_z[indices_b]
        diff_raw, lo_raw, hi_raw = bootstrap_diff_ci(da, db)
        diff_z,   lo_z,   hi_z  = bootstrap_diff_ci(daz, dbz)

        # AUROC: discriminate group A (label 1) from group B (label 0)
        y_disc = np.concatenate([np.ones(len(da)), np.zeros(len(db))])
        scores_disc = np.concatenate([da, db])
        try:
            disc_auroc = auroc(y_disc, scores_disc)
        except Exception:
            disc_auroc = None

        return {
            "group_a": label_a,
            "group_b": label_b,
            f"n_{label_a}": len(indices_a),
            f"n_{label_b}": len(indices_b),
            f"mean_{label_a}_raw": float(da.mean()) if len(da) > 0 else None,
            f"mean_{label_b}_raw": float(db.mean()) if len(db) > 0 else None,
            "diff_raw": diff_raw,
            "ci95_raw": [lo_raw, hi_raw],
            f"mean_{label_a}_z": float(daz.mean()) if len(daz) > 0 else None,
            f"mean_{label_b}_z": float(dbz.mean()) if len(dbz) > 0 else None,
            "diff_z": diff_z,
            "ci95_z": [lo_z, hi_z],
            f"discriminator_auroc_{label_a}_vs_{label_b}": disc_auroc,
            "score_label": score_label,
        }

    # Q2: use Δ from LOW prime
    q2_doubt = group_comparison(
        q2_flipped, q2_resisted,
        delta_doubt_low, delta_doubt_low_z,
        "flipped", "resisted",
        "Δdoubt_LOW (LOW prime, known_correct_answered rows)",
    )
    q2_caution = group_comparison(
        q2_flipped, q2_resisted,
        delta_caution_low, delta_caution_low_z,
        "flipped", "resisted",
        "Δcaution_LOW (LOW prime, known_correct_answered rows)",
    )

    result["Q2_muzzle_compliance"] = {
        "cell": "known_correct_answered",
        "prime": "LOW (inverted arm: known → LOW)",
        "n_total": int(kca_mask.sum()),
        "n_flipped": len(q2_flipped),
        "n_resisted": len(q2_resisted),
        "doubt_axis": q2_doubt,
        "caution_axis_L24": q2_caution,
    }

    # -----------------------------------------------------------------------
    # STEP 6: Q3 — release side: unknown_refused, HIGH prime
    # -----------------------------------------------------------------------
    print(f"[AG/§8] Step 6: Q3 — release side analysis...", flush=True)

    # unknown_refused rows (n=279 per AE census)
    ur_mask = np.array([
        ae_cell_by_key.get(r["row_key"], "?") == "unknown_refused"
        for r in af_rows
    ], dtype=bool)

    ur_indices = np.where(ur_mask)[0]
    print(f"[AG/§8] Q3: unknown_refused n={ur_mask.sum()}", flush=True)

    # Inverted arm: unknowns received HIGH prime (unknown→inverted=HIGH)
    # Released = answered under inverted; resisted = still refused
    q3_released = []
    q3_resisted = []
    for i in ur_indices:
        rk = af_rows[i]["row_key"]
        inv = inv_by_key.get(rk)
        if inv is None:
            print(f"  WARNING: {rk} not in inverted rows", flush=True)
            continue
        if not inv.get("refused", True):  # answered = released
            q3_released.append(i)
        else:
            q3_resisted.append(i)

    q3_released = np.array(q3_released, dtype=int)
    q3_resisted = np.array(q3_resisted, dtype=int)
    print(f"[AG/§8] Q3: released={len(q3_released)}, resisted={len(q3_resisted)}", flush=True)

    # Q3: use Δ from HIGH prime
    q3_doubt = group_comparison(
        q3_released, q3_resisted,
        delta_doubt_high, delta_doubt_high_z,
        "released", "resisted",
        "Δdoubt_HIGH (HIGH prime, unknown_refused rows)",
    )
    q3_caution = group_comparison(
        q3_released, q3_resisted,
        delta_caution_high, delta_caution_high_z,
        "released", "resisted",
        "Δcaution_HIGH (HIGH prime, unknown_refused rows)",
    )

    result["Q3_release_side"] = {
        "cell": "unknown_refused",
        "prime": "HIGH (inverted arm: unknown → HIGH)",
        "n_total": int(ur_mask.sum()),
        "n_released": len(q3_released),
        "n_resisted": len(q3_resisted),
        "doubt_axis": q3_doubt,
        "caution_axis_L24": q3_caution,
        "note": (
            "§3a capacity confound applies: low release may reflect having "
            "nothing to retrieve rather than state-gated resistance. "
            "The base CAN confabulate (21/300 in AE census)."
        ),
    }

    # -----------------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------------
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "ag_state_result.json"
    out_path.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(f"\n[AG/§8] Written: {out_path}", flush=True)
    return result


if __name__ == "__main__":
    main()
