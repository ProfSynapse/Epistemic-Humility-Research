#!/usr/bin/env python3
"""QUALIFY mode separability on base-model readout: CPU-only fit + score.

Pre-registered in experiments/qualify-mode-separability-base-readout/AMENDMENT.md
(draft; pins at signing). Consumes the features/index written by
extract_hidden_states.py (never re-touches the model or raw row text) and
fits, at each of the four pinned depths, on the 2811-row matched fit
population:

  (a) linear k-regression (Ridge, PCA-128 + standardize)
  (b) direct 3-way multinomial-logistic readout (same preprocessing)
  (c) naive linear QUALIFY-vs-rest logistic regression (comparison floor)

evaluated on the full 602-row dev split, with a 1000-resample percentile
bootstrap CI on every AUROC. Writes an aggregate-only JSON report (no row
text, no raw feature vectors) to analysis-committed/fit_report.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import yaml
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
MODES = ["ABSTAIN", "QUALIFY", "ANSWER"]


def load_cell_and_gates() -> tuple[dict, dict]:
    with open(HERE / "cell.yaml") as f:
        cell = yaml.safe_load(f)
    with open(HERE / "gates.yaml") as f:
        gates = yaml.safe_load(f)
    return cell, gates


def load_index(index_path: Path) -> list[dict]:
    rows = []
    with open(index_path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_features(features_path: Path, n_rows: int, n_depths: int, hidden_size: int) -> np.ndarray:
    record_floats = n_depths * hidden_size
    flat = np.fromfile(features_path, dtype=np.float32, count=n_rows * record_floats)
    assert flat.size == n_rows * record_floats, (
        f"feature file has {flat.size} floats, expected {n_rows * record_floats} "
        f"({n_rows} rows x {record_floats} floats/row) -- extraction incomplete or corrupt"
    )
    return flat.reshape(n_rows, n_depths, hidden_size)


def banded_predict(predicted_k: np.ndarray, thresholds: dict) -> np.ndarray:
    labels = np.empty(predicted_k.shape[0], dtype=object)
    labels[predicted_k <= thresholds["abstain_max"]] = "ABSTAIN"
    labels[(predicted_k > thresholds["abstain_max"]) & (predicted_k <= thresholds["qualify_max"])] = "QUALIFY"
    labels[predicted_k > thresholds["qualify_max"]] = "ANSWER"
    return labels


def bootstrap_auroc_ci(y_true_bin: np.ndarray, score: np.ndarray, n_resamples: int, seed: int) -> dict:
    rng = np.random.RandomState(seed)
    n = len(y_true_bin)
    point = float(roc_auc_score(y_true_bin, score)) if len(np.unique(y_true_bin)) > 1 else float("nan")
    boots = []
    for _ in range(n_resamples):
        idx = rng.randint(0, n, size=n)
        yb, sb = y_true_bin[idx], score[idx]
        if len(np.unique(yb)) < 2:
            continue
        boots.append(roc_auc_score(yb, sb))
    if not boots:
        return {"point": point, "ci_lower": float("nan"), "ci_upper": float("nan"), "n_valid_resamples": 0}
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"point": point, "ci_lower": float(lo), "ci_upper": float(hi), "n_valid_resamples": len(boots)}


def confusion_and_prf(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    conf = {t: {p: 0 for p in MODES} for t in MODES}
    for t, p in zip(y_true, y_pred):
        conf[t][p] += 1
    prf = {}
    for m in MODES:
        tp = conf[m][m]
        fn = sum(conf[m][p] for p in MODES if p != m)
        fp = sum(conf[t][m] for t in MODES if t != m)
        recall = tp / (tp + fn) if (tp + fn) else float("nan")
        precision = tp / (tp + fp) if (tp + fp) else float("nan")
        prf[m] = {"recall": recall, "precision": precision, "n_true": tp + fn}
    accuracy = sum(conf[m][m] for m in MODES) / max(len(y_true), 1)
    return {"confusion": conf, "per_mode": prf, "accuracy": accuracy}


def fit_depth(Z_fit, y_fit_k, y_fit_mode, Z_dev, y_dev_k, y_dev_mode, cell, gates, bootstrap_seed):
    r_cfg = cell["readouts"]
    thresholds = cell["scoring"]["banded_classification_thresholds"]
    n_boot = cell["scoring"]["bootstrap_resamples"]

    # --- (a) k-regression ---
    ridge = Ridge(alpha=r_cfg["a_k_regression"]["alpha"])
    ridge.fit(Z_fit, y_fit_k)
    pred_k_dev = ridge.predict(Z_dev)
    spearman = spearmanr(y_dev_k, pred_k_dev)
    pearson = pearsonr(y_dev_k, pred_k_dev)

    qualify_score_a = -np.abs(pred_k_dev - 16.0)
    abstain_score_a = -pred_k_dev
    answer_score_a = pred_k_dev
    y_dev_qualify_bin = (y_dev_mode == "QUALIFY").astype(int)
    y_dev_abstain_bin = (y_dev_mode == "ABSTAIN").astype(int)
    y_dev_answer_bin = (y_dev_mode == "ANSWER").astype(int)

    a_qualify_auroc = bootstrap_auroc_ci(y_dev_qualify_bin, qualify_score_a, n_boot, bootstrap_seed)
    a_abstain_auroc = bootstrap_auroc_ci(y_dev_abstain_bin, abstain_score_a, n_boot, bootstrap_seed)
    a_answer_auroc = bootstrap_auroc_ci(y_dev_answer_bin, answer_score_a, n_boot, bootstrap_seed)

    pred_mode_a = banded_predict(pred_k_dev, thresholds)
    banded_prf = confusion_and_prf(y_dev_mode, pred_mode_a)

    # --- (b) multinomial 3-way ---
    # sklearn >=1.7 dropped the `multi_class` kwarg: lbfgs already fits a true
    # multinomial (softmax) model automatically for a >2-class target, which is
    # exactly the "can express a band" model class this readout needs.
    mlr = LogisticRegression(
        solver=r_cfg["b_multinomial_3way"]["solver"],
        max_iter=r_cfg["b_multinomial_3way"]["max_iter"],
    )
    mlr.fit(Z_fit, y_fit_mode)
    proba_dev_b = mlr.predict_proba(Z_dev)
    qualify_col_b = list(mlr.classes_).index("QUALIFY")
    b_qualify_auroc = bootstrap_auroc_ci(y_dev_qualify_bin, proba_dev_b[:, qualify_col_b], n_boot, bootstrap_seed)
    pred_mode_b = mlr.predict(Z_dev)
    b_prf = confusion_and_prf(y_dev_mode, pred_mode_b)

    # --- (c) naive QUALIFY-vs-rest floor ---
    y_fit_qualify_bin = (y_fit_mode == "QUALIFY").astype(int)
    naive = LogisticRegression(
        solver=r_cfg["c_naive_qualify_vs_rest"]["solver"],
        max_iter=r_cfg["c_naive_qualify_vs_rest"]["max_iter"],
        class_weight=r_cfg["c_naive_qualify_vs_rest"]["class_weight"],
    )
    naive.fit(Z_fit, y_fit_qualify_bin)
    proba_dev_c = naive.predict_proba(Z_dev)[:, list(naive.classes_).index(1)]
    c_qualify_auroc = bootstrap_auroc_ci(y_dev_qualify_bin, proba_dev_c, n_boot, bootstrap_seed)

    return {
        "a_k_regression": {
            "spearman_r": spearman.correlation, "spearman_p": spearman.pvalue,
            "pearson_r": pearson.statistic, "pearson_p": pearson.pvalue,
            "predicted_k_dev_sd": float(np.std(pred_k_dev)),
            "qualify_vs_rest_auroc": a_qualify_auroc,
            "abstain_vs_rest_auroc": a_abstain_auroc,
            "answer_vs_rest_auroc": a_answer_auroc,
            "banded_classification": banded_prf,
        },
        "b_multinomial_3way": {
            "qualify_vs_rest_auroc": b_qualify_auroc,
            "classification": b_prf,
        },
        "c_naive_qualify_vs_rest": {
            "qualify_vs_rest_auroc": c_qualify_auroc,
        },
        "_fit_objects_for_determinism": {"ridge_coef": ridge.coef_},
    }


def refit_determinism_check(Z_fit, y_fit_k, alpha, cosine_min, maxabs_max):
    r1 = Ridge(alpha=alpha).fit(Z_fit, y_fit_k)
    r2 = Ridge(alpha=alpha).fit(Z_fit, y_fit_k)
    c1, c2 = r1.coef_, r2.coef_
    cosine = float(np.dot(c1, c2) / (np.linalg.norm(c1) * np.linalg.norm(c2)))
    maxabs = float(np.max(np.abs(c1 - c2)))
    return {"cosine": cosine, "maxabs_diff": maxabs, "pass": cosine >= cosine_min and maxabs <= maxabs_max}


def run(args: argparse.Namespace) -> int:
    cell, gates = load_cell_and_gates()
    depths = cell["extraction"]["depths_hidden_state_index"]
    hidden_size = cell["model"]["hidden_size"]

    index_path = HERE / cell["output"]["extraction_index"]
    features_path = HERE / cell["output"]["extraction_features_dir"] / "combined.f32.bin"
    index = load_index(index_path)
    n_rows = len(index)
    features = load_features(features_path, n_rows, len(depths), hidden_size)

    fit_mask = np.array([r["split"] == "fit" for r in index])
    dev_mask = np.array([r["split"] == "dev" for r in index])
    assert fit_mask.sum() == cell["fit_population"]["total_fit_rows"], (
        f"fit population incomplete: {fit_mask.sum()} / {cell['fit_population']['total_fit_rows']}"
    )
    assert dev_mask.sum() == cell["dataset"]["dev"]["rows"], (
        f"dev split incomplete: {dev_mask.sum()} / {cell['dataset']['dev']['rows']}"
    )

    k_all = np.array([r["k"] for r in index], dtype=np.float64)
    mode_all = np.array([r["mode_label"] for r in index], dtype=object)

    y_fit_k, y_dev_k = k_all[fit_mask], k_all[dev_mask]
    y_fit_mode, y_dev_mode = mode_all[fit_mask], mode_all[dev_mask]

    pca_cfg = cell["readouts"]["common_preprocessing"]
    bootstrap_seed = cell["scoring"]["bootstrap_seed"]

    per_depth = {}
    for di, depth_idx in enumerate(depths):
        X_fit = features[fit_mask, di, :]
        X_dev = features[dev_mask, di, :]

        pca = PCA(
            n_components=pca_cfg["pca_components"], svd_solver=pca_cfg["pca_svd_solver"],
            random_state=pca_cfg["pca_random_state"],
        )
        Z_fit = pca.fit_transform(X_fit)
        Z_dev = pca.transform(X_dev)
        scaler = StandardScaler().fit(Z_fit)
        Z_fit = scaler.transform(Z_fit)
        Z_dev = scaler.transform(Z_dev)

        result = fit_depth(Z_fit, y_fit_k, y_fit_mode, Z_dev, y_dev_k, y_dev_mode, cell, gates, bootstrap_seed)
        result.pop("_fit_objects_for_determinism")
        per_depth[f"depth_{depth_idx}"] = result

    # primary gate: max over depths of (a) qualify_vs_rest_auroc point estimate
    best_key = max(per_depth, key=lambda k: per_depth[k]["a_k_regression"]["qualify_vs_rest_auroc"]["point"])
    best_depth_idx = depths[list(per_depth.keys()).index(best_key)]
    best_a = per_depth[best_key]["a_k_regression"]["qualify_vs_rest_auroc"]

    pg = gates["primary_gate"]
    if best_a["point"] >= pg["pass"]["auroc_min"] and best_a["ci_lower"] > pg["pass"]["ci_lower_min"]:
        verdict = "PASS"
    elif best_a["point"] <= pg["fail"]["auroc_max"] or best_a["ci_upper"] < pg["fail"]["ci_upper_max"]:
        verdict = "FAIL"
    else:
        verdict = "INCONCLUSIVE"

    # secondary divergence flag
    best_b = per_depth[best_key]["b_multinomial_3way"]["qualify_vs_rest_auroc"]
    b_max_key = max(per_depth, key=lambda k: per_depth[k]["b_multinomial_3way"]["qualify_vs_rest_auroc"]["point"])
    b_max = per_depth[b_max_key]["b_multinomial_3way"]["qualify_vs_rest_auroc"]
    divergence = abs(b_max["point"] - best_a["point"])
    divergence_flag = divergence > gates["secondary_readout"]["divergence_flag_threshold"]

    # naive floor gap
    c_max_key = max(per_depth, key=lambda k: per_depth[k]["c_naive_qualify_vs_rest"]["qualify_vs_rest_auroc"]["point"])
    c_max = per_depth[c_max_key]["c_naive_qualify_vs_rest"]["qualify_vs_rest_auroc"]
    floor_gap = best_a["point"] - c_max["point"]

    # determinism check at best depth
    X_fit_best = features[fit_mask, list(per_depth.keys()).index(best_key), :]
    pca_best = PCA(
        n_components=pca_cfg["pca_components"], svd_solver=pca_cfg["pca_svd_solver"],
        random_state=pca_cfg["pca_random_state"],
    )
    Z_fit_best = StandardScaler().fit_transform(pca_best.fit_transform(X_fit_best))
    det_cfg = cell["determinism_check"]
    determinism = refit_determinism_check(
        Z_fit_best, y_fit_k, cell["readouts"]["a_k_regression"]["alpha"],
        det_cfg["cosine_min"], det_cfg["maxabs_diff_max"],
    )

    # mechanical checks
    mech = gates["mechanical_checks"]
    predicted_k_sd_ok = all(
        per_depth[k]["a_k_regression"]["predicted_k_dev_sd"] >= mech["predicted_k_dev_sd_min"] for k in per_depth
    )
    nan_ok = not any(
        np.isnan(per_depth[k]["a_k_regression"]["qualify_vs_rest_auroc"]["point"]) for k in per_depth
    )

    report = {
        "cell_sha256_note": "see experiment.yaml instrument.pins for the signed cell.yaml/gates.yaml hashes",
        "n_fit_rows": int(fit_mask.sum()),
        "n_dev_rows": int(dev_mask.sum()),
        "depths": depths,
        "per_depth": per_depth,
        "primary_gate": {
            "best_depth": best_depth_idx, "auroc": best_a, "verdict": verdict,
        },
        "secondary_readout": {
            "best_depth_multinomial": depths[list(per_depth.keys()).index(b_max_key)],
            "auroc": best_b, "max_over_depths_auroc": b_max,
            "divergence_from_primary": divergence, "divergence_flag": divergence_flag,
        },
        "naive_floor": {
            "best_depth": depths[list(per_depth.keys()).index(c_max_key)],
            "max_over_depths_auroc": c_max, "gap_vs_primary": floor_gap,
        },
        "determinism_check": determinism,
        "mechanical_checks": {
            "predicted_k_dev_sd_ok": predicted_k_sd_ok, "no_nan_ok": nan_ok,
            "extraction_complete": True,
        },
    }

    out_path = HERE / cell["output"]["fit_report_out"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2, default=float)

    print(json.dumps({
        "primary_verdict": verdict, "best_depth": best_depth_idx,
        "primary_auroc": best_a, "divergence_flag": divergence_flag,
        "naive_floor_gap": floor_gap, "determinism_pass": determinism["pass"],
    }, indent=2, default=float))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    args = ap.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
