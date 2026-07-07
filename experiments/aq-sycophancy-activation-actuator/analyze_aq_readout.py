"""Local diagnostics for the AQ answer-sycophancy r2 readout.

This script is CPU-only. It consumes the gitignored local artifacts downloaded
from the Modal readout checkpoint:

  - analysis/row_pool.jsonl
  - analysis/probe_fit_labels.jsonl
  - analysis/extraction/*.safetensors
  - directions/sycophancy_answer_direction.json

It intentionally does not adjudicate any actuator claim. The output is a
readout-screen and confound report for deciding whether steering is worth a
separate approved launch.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from safetensors.torch import load_file
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold


HERE = Path(__file__).resolve().parent
DEFAULT_ANALYSIS_DIR = HERE / "analysis"
DEFAULT_EXTRACTION_DIR = DEFAULT_ANALYSIS_DIR / "extraction"
DEFAULT_LABELS = DEFAULT_ANALYSIS_DIR / "probe_fit_labels.jsonl"
DEFAULT_ROWS = DEFAULT_ANALYSIS_DIR / "row_pool.jsonl"
DEFAULT_DIRECTION = HERE / "directions" / "sycophancy_answer_direction.json"
DEFAULT_OUT = DEFAULT_ANALYSIS_DIR / "readout_diagnostics"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")


def safe_key(row_key: str) -> str:
    return row_key.replace("::", "__").replace("|", "_").replace("/", "_")


def load_matrix(
    extraction_dir: Path,
    rows: list[dict[str, Any]],
    family: str,
) -> tuple[dict[int, np.ndarray], list[dict[str, Any]]]:
    per_layer: dict[int, list[np.ndarray]] = defaultdict(list)
    kept: list[dict[str, Any]] = []
    for row in rows:
        row_key = str(row["row_key"])
        path = extraction_dir / f"{safe_key(row_key)}__{family}.safetensors"
        if not path.exists():
            continue
        tensors = load_file(str(path))
        for key, tensor in tensors.items():
            per_layer[int(key[1:])].append(tensor[0].cpu().numpy().astype(np.float64))
        kept.append(row)
    return {layer: np.vstack(vals) for layer, vals in per_layer.items()}, kept


def rank_auroc(y_true: np.ndarray, scores: np.ndarray) -> float:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=np.float64)
    pos = y == 1
    n_pos = int(pos.sum())
    n_neg = int((~pos).sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s), dtype=np.float64)
    sorted_scores = s[order]
    i = 0
    while i < len(sorted_scores):
        j = i + 1
        while j < len(sorted_scores) and sorted_scores[j] == sorted_scores[i]:
            j += 1
        # Ranks are 1-indexed; ties receive their average rank.
        avg_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg_rank
        i = j
    rank_sum_pos = float(ranks[pos].sum())
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def bootstrap_auc_ci(
    y_true: np.ndarray,
    scores: np.ndarray,
    *,
    n: int = 2000,
    seed: int = 20260707,
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=np.float64)
    vals: list[float] = []
    for _ in range(n):
        idx = rng.integers(0, len(y), size=len(y))
        if len(np.unique(y[idx])) < 2:
            continue
        vals.append(rank_auroc(y[idx], s[idx]))
    arr = np.asarray(vals, dtype=np.float64)
    return {
        "n": int(len(arr)),
        "seed": int(seed),
        "lo": float(np.quantile(arr, 0.025)),
        "hi": float(np.quantile(arr, 0.975)),
    }


def mean_ci(values: np.ndarray, *, n: int = 2000, seed: int = 20260707) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    v = np.asarray(values, dtype=np.float64)
    if len(v) == 0:
        return {"mean": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": 0}
    samples = np.empty(n, dtype=np.float64)
    for i in range(n):
        samples[i] = float(v[rng.integers(0, len(v), size=len(v))].mean())
    return {
        "mean": float(v.mean()),
        "lo": float(np.quantile(samples, 0.025)),
        "hi": float(np.quantile(samples, 0.975)),
        "n": int(len(v)),
    }


def cv_scores(
    X: np.ndarray,
    y: np.ndarray,
    *,
    n_components: int,
    n_splits: int,
    seed: int,
    solver: str,
    tol: float,
    C: float,
    max_iter: int = 2000,
) -> dict[str, Any]:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=int)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.full(len(y), np.nan, dtype=np.float64)
    fold_aucs: list[float] = []
    for train_idx, test_idx in skf.split(X, y):
        mu = X[train_idx].mean(axis=0)
        k = min(n_components, len(train_idx) - 1, X.shape[1])
        pca = PCA(n_components=k, svd_solver="randomized", random_state=seed)
        z_train = pca.fit_transform(X[train_idx] - mu)
        z_test = pca.transform(X[test_idx] - mu)
        clf = LogisticRegression(
            solver=solver,
            tol=tol,
            C=C,
            max_iter=max_iter,
            random_state=seed,
        )
        clf.fit(z_train, y[train_idx])
        scores = clf.decision_function(z_test)
        oof[test_idx] = scores
        fold_aucs.append(rank_auroc(y[test_idx], scores))
    if np.isnan(oof).any():
        raise RuntimeError("every row must receive an out-of-fold score")
    return {
        "fold_mean_auc": float(np.mean(fold_aucs)),
        "fold_std_auc": float(np.std(fold_aucs)),
        "global_oof_auc": rank_auroc(y, oof),
        "oof_scores": oof,
        "fold_aucs": [float(x) for x in fold_aucs],
    }


def cv_scores_residualized(
    X: np.ndarray,
    y: np.ndarray,
    nuisance: np.ndarray,
    *,
    n_components: int,
    n_splits: int,
    seed: int,
    solver: str,
    tol: float,
    C: float,
    max_iter: int = 2000,
) -> dict[str, Any]:
    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=int)
    nuisance = np.asarray(nuisance, dtype=np.float64)
    if nuisance.ndim == 1:
        nuisance = nuisance[:, None]
    min_class = int(np.bincount(y).min())
    n_splits = min(n_splits, min_class)
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    oof = np.full(len(y), np.nan, dtype=np.float64)
    fold_aucs: list[float] = []
    for train_idx, test_idx in skf.split(X, y):
        z_train = np.column_stack([np.ones(len(train_idx)), nuisance[train_idx]])
        z_test = np.column_stack([np.ones(len(test_idx)), nuisance[test_idx]])
        beta, *_ = np.linalg.lstsq(z_train, X[train_idx], rcond=None)
        X_train_resid = X[train_idx] - z_train @ beta
        X_test_resid = X[test_idx] - z_test @ beta
        mu = X_train_resid.mean(axis=0)
        k = min(n_components, len(train_idx) - 1, X.shape[1])
        pca = PCA(n_components=k, svd_solver="randomized", random_state=seed)
        pca_train = pca.fit_transform(X_train_resid - mu)
        pca_test = pca.transform(X_test_resid - mu)
        clf = LogisticRegression(
            solver=solver,
            tol=tol,
            C=C,
            max_iter=max_iter,
            random_state=seed,
        )
        clf.fit(pca_train, y[train_idx])
        scores = clf.decision_function(pca_test)
        oof[test_idx] = scores
        fold_aucs.append(rank_auroc(y[test_idx], scores))
    if np.isnan(oof).any():
        raise RuntimeError("every row must receive an out-of-fold score")
    return {
        "fold_mean_auc": float(np.mean(fold_aucs)),
        "fold_std_auc": float(np.std(fold_aucs)),
        "global_oof_auc": rank_auroc(y, oof),
        "oof_scores": oof,
        "fold_aucs": [float(x) for x in fold_aucs],
    }


def cv_summary(cv: dict[str, Any]) -> dict[str, Any]:
    return {
        "fold_mean_auc": cv["fold_mean_auc"],
        "fold_std_auc": cv["fold_std_auc"],
        "global_oof_auc": cv["global_oof_auc"],
        "fold_aucs": cv["fold_aucs"],
    }


def condition_projected(
    X: np.ndarray, condition_labels: np.ndarray
) -> tuple[np.ndarray, np.ndarray, float]:
    X = np.asarray(X, dtype=np.float64)
    labels = np.asarray(condition_labels, dtype=int)
    axis = X[labels == 1].mean(axis=0) - X[labels == 0].mean(axis=0)
    norm = float(np.linalg.norm(axis))
    if norm == 0.0:
        return X.copy(), axis, norm
    unit = axis / norm
    return X - np.outer(X @ unit, unit), unit, norm


def zscore(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    sd = float(arr.std())
    if sd == 0.0:
        return arr - arr.mean()
    return (arr - arr.mean()) / sd


def parse_confidence(row: dict[str, Any]) -> float:
    raw = row.get("baseline_generated_answer") or ""
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return float("nan")
    try:
        return float(parsed.get("confidence"))
    except (TypeError, ValueError):
        return float("nan")


def hydra_component(row: dict[str, Any]) -> str:
    hinted = row.get("prompt_condition") == "incorrect_hint"
    if hinted and row.get("wrong_hint_followed"):
        return "hint_followed"
    if hinted and row.get("baseline_refused"):
        return "hint_refused_or_avoid"
    if hinted and row.get("baseline_correct"):
        return "hint_resisted_correct"
    if hinted:
        return "hint_other_wrong"
    if row.get("baseline_refused"):
        return "neutral_refused"
    if row.get("baseline_correct"):
        return "neutral_correct"
    return "neutral_wrong"


def matched_binary_indices(
    labels: np.ndarray,
    covariates: np.ndarray,
    *,
    seed: int = 20260707,
) -> np.ndarray:
    labels = np.asarray(labels, dtype=int)
    covariates = np.asarray(covariates, dtype=np.float64)
    if covariates.ndim == 1:
        covariates = covariates[:, None]
    covariates = np.column_stack([zscore(covariates[:, i]) for i in range(covariates.shape[1])])
    rng = np.random.default_rng(seed)
    pos = list(np.where(labels == 1)[0])
    neg = list(np.where(labels == 0)[0])
    if len(pos) <= len(neg):
        minority, majority = pos, neg
    else:
        minority, majority = neg, pos
    rng.shuffle(minority)
    available = set(majority)
    chosen = list(minority)
    for idx in minority:
        best = min(
            available,
            key=lambda j: float(np.sum((covariates[idx] - covariates[j]) ** 2)),
        )
        available.remove(best)
        chosen.append(best)
    return np.asarray(sorted(chosen), dtype=int)


def full_direction_scores(X: np.ndarray, direction: dict[str, Any]) -> np.ndarray:
    vector = np.asarray(direction["vector"], dtype=np.float64)
    if vector.shape[0] != X.shape[1]:
        raise ValueError(f"direction dim {vector.shape[0]} != X dim {X.shape[1]}")
    return np.asarray(X, dtype=np.float64) @ vector


def logistic_scores(X: np.ndarray, direction: dict[str, Any]) -> np.ndarray:
    vector = np.asarray(direction["vector"], dtype=np.float64)
    raw_norm = float(direction.get("raw_norm", 1.0))
    coef = vector * raw_norm if direction.get("normalized", False) else vector
    intercept = float(direction.get("intercept", 0.0))
    return np.asarray(X, dtype=np.float64) @ coef + intercept


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if len(x) < 2 or x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def summarize_binary(
    name: str,
    labels: np.ndarray,
    scores: np.ndarray,
    *,
    positive_name: str = "positive",
    negative_name: str = "negative",
) -> dict[str, Any]:
    labels = np.asarray(labels, dtype=int)
    scores = np.asarray(scores, dtype=np.float64)
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    return {
        "name": name,
        "n_positive": int((labels == 1).sum()),
        "n_negative": int((labels == 0).sum()),
        "positive_name": positive_name,
        "negative_name": negative_name,
        "auroc": rank_auroc(labels, scores),
        "positive": mean_ci(pos),
        "negative": mean_ci(neg),
        "mean_diff_positive_minus_negative": float(pos.mean() - neg.mean())
        if len(pos) and len(neg)
        else float("nan"),
    }


def row_text_len(row: dict[str, Any]) -> int:
    text = str(row.get("baseline_generated_answer") or row.get("answer_text") or "")
    return len(text.split())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-dir", type=Path, default=DEFAULT_ANALYSIS_DIR)
    parser.add_argument("--extraction-dir", type=Path, default=DEFAULT_EXTRACTION_DIR)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--direction", type=Path, default=DEFAULT_DIRECTION)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--bootstrap-n", type=int, default=2000)
    args = parser.parse_args()

    labels = load_jsonl(args.labels)
    rows = load_jsonl(args.rows)
    direction = json.loads(args.direction.read_text(encoding="utf-8"))
    manifest = json.loads((args.extraction_dir / "manifest.json").read_text(encoding="utf-8"))
    rows_by_key = {r["row_key"]: r for r in rows}

    probe_rows = []
    for rec in labels:
        row = dict(rows_by_key[rec["row_key"]])
        row["_probe_label"] = int(rec["label"])
        probe_rows.append(row)

    anchor_mats, kept_probe_rows = load_matrix(args.extraction_dir, probe_rows, "anchor")
    answer_mats, _ = load_matrix(args.extraction_dir, probe_rows, "answer_end")
    y = np.asarray([int(r["_probe_label"]) for r in kept_probe_rows], dtype=int)

    recipe = direction.get("recipe") or {}
    cv_kwargs = {
        "n_components": int(recipe.get("n_components", 128)),
        "n_splits": 5,
        "seed": int(recipe.get("seed", 20260707)),
        "solver": str(recipe.get("solver", "saga")),
        "tol": float(recipe.get("tol", 0.001)),
        "C": float(recipe.get("C", 1.0)),
    }

    cv_by_position: dict[str, dict[str, Any]] = {}
    for family_name, matrices in (("anchor", anchor_mats), ("answer_end", answer_mats)):
        layer_results = {}
        for layer, X in sorted(matrices.items()):
            cv = cv_scores(X, y, **cv_kwargs)
            layer_results[str(layer)] = {
                "fold_mean_auc": cv["fold_mean_auc"],
                "fold_std_auc": cv["fold_std_auc"],
                "global_oof_auc": cv["global_oof_auc"],
                "fold_aucs": cv["fold_aucs"],
            }
            if layer == int(direction["layer"]) and family_name == "anchor":
                selected_oof = cv["oof_scores"]
        cv_by_position[family_name] = layer_results

    selected_layer = int(direction["layer"])
    selected_X = anchor_mats[selected_layer]
    selected_scores = logistic_scores(selected_X, direction)
    selected_unit_projection = full_direction_scores(selected_X, direction)
    selected_oof_auc = rank_auroc(y, selected_oof)
    selected_oof_ci = bootstrap_auc_ci(
        y, selected_oof, n=args.bootstrap_n, seed=20260707
    )
    selected_full_ci = bootstrap_auc_ci(
        y, selected_scores, n=args.bootstrap_n, seed=20260708
    )

    all_anchor_mats, all_rows = load_matrix(args.extraction_dir, rows, "anchor")
    all_answer_mats, _ = load_matrix(args.extraction_dir, rows, "answer_end")
    all_by_key = {r["row_key"]: i for i, r in enumerate(all_rows)}
    all_scores_anchor = logistic_scores(all_anchor_mats[selected_layer], direction)
    all_scores_answer = logistic_scores(all_answer_mats[selected_layer], direction)
    all_unit_anchor = full_direction_scores(all_anchor_mats[selected_layer], direction)
    probe_all_indices = np.asarray([all_by_key[r["row_key"]] for r in kept_probe_rows], dtype=int)

    # Condition confound: can the selected direction merely separate hinted
    # prompts from neutral prompts?
    condition_labels = np.asarray(
        [1 if r.get("prompt_condition") == "incorrect_hint" else 0 for r in all_rows],
        dtype=int,
    )
    condition_anchor = summarize_binary(
        "incorrect_hint_vs_neutral_anchor",
        condition_labels,
        all_scores_anchor,
        positive_name="incorrect_hint",
        negative_name="neutral",
    )
    condition_answer = summarize_binary(
        "incorrect_hint_vs_neutral_answer_end",
        condition_labels,
        all_scores_answer,
        positive_name="incorrect_hint",
        negative_name="neutral",
    )

    correctness_labels = np.asarray(
        [1 if r.get("baseline_correct") else 0 for r in kept_probe_rows],
        dtype=int,
    )
    incorrect_mask = correctness_labels == 0
    refused_labels = np.asarray(
        [1 if r.get("baseline_refused") else 0 for r in kept_probe_rows],
        dtype=int,
    )
    answer_lengths = np.asarray([row_text_len(r) for r in kept_probe_rows], dtype=float)
    prompt_lengths = np.asarray(
        [len(str(r.get("prompt") or "").split()) for r in kept_probe_rows], dtype=float
    )

    confounds = {
        "correctness_on_probe_rows": summarize_binary(
            "baseline_correct_vs_not",
            correctness_labels,
            selected_scores,
            positive_name="baseline_correct",
            negative_name="baseline_not_correct",
        ),
        "label_within_baseline_incorrect_rows": summarize_binary(
            "wrong_hint_followed_vs_other_wrong",
            y[incorrect_mask],
            selected_scores[incorrect_mask],
            positive_name="wrong_hint_followed",
            negative_name="wrong_but_not_wrong_hint_followed",
        ),
        "label_within_baseline_incorrect_rows_oof": summarize_binary(
            "wrong_hint_followed_vs_other_wrong_oof",
            y[incorrect_mask],
            selected_oof[incorrect_mask],
            positive_name="wrong_hint_followed",
            negative_name="wrong_but_not_wrong_hint_followed",
        ),
        "label_by_correctness_counts": {
            f"label_{int(label)}__baseline_correct_{int(correct)}": int(
                ((y == label) & (correctness_labels == correct)).sum()
            )
            for label in (0, 1)
            for correct in (0, 1)
        },
        "refusal_on_probe_rows": {
            "n_refused": int(refused_labels.sum()),
            "n_not_refused": int((refused_labels == 0).sum()),
            "auroc": rank_auroc(refused_labels, selected_scores),
            "note": "AUROC is NaN when one class is absent.",
        },
        "answer_length_correlation": pearson(answer_lengths, selected_scores),
        "prompt_length_correlation": pearson(prompt_lengths, selected_scores),
        "condition_anchor": condition_anchor,
        "condition_answer_end": condition_answer,
    }

    (
        selected_condition_resid_all,
        selected_condition_axis,
        selected_condition_axis_norm,
    ) = condition_projected(
        all_anchor_mats[selected_layer], condition_labels
    )
    selected_condition_resid_X = selected_condition_resid_all[probe_all_indices]
    condition_resid_cv = cv_scores(selected_condition_resid_X, y, **cv_kwargs)

    confidences = np.asarray([parse_confidence(r) for r in kept_probe_rows], dtype=float)
    if np.isnan(confidences).all():
        confidences = np.zeros_like(confidences)
    else:
        fill = float(np.nanmean(confidences))
        confidences = np.where(np.isnan(confidences), fill, confidences)
    behavioral_nuisance = np.column_stack(
        [
            correctness_labels.astype(float),
            refused_labels.astype(float),
            zscore(answer_lengths),
            zscore(prompt_lengths),
            zscore(confidences),
        ]
    )
    condition_behavior_resid_cv = cv_scores_residualized(
        selected_condition_resid_X, y, behavioral_nuisance, **cv_kwargs
    )

    paired_rows = []
    paired_deltas = []
    paired_delta_cv_by_layer: dict[str, Any] = {}
    paired_delta_selected_X = None
    for layer, X_all_layer in sorted(all_anchor_mats.items()):
        delta_vectors = []
        delta_labels = []
        for row in kept_probe_rows:
            counterpart = rows_by_key.get(row.get("counterpart_row_key"))
            if not counterpart:
                continue
            i_probe = all_by_key[row["row_key"]]
            i_neutral = all_by_key[counterpart["row_key"]]
            delta_vectors.append(X_all_layer[i_probe] - X_all_layer[i_neutral])
            delta_labels.append(int(row["_probe_label"]))
        X_delta = np.vstack(delta_vectors)
        y_delta = np.asarray(delta_labels, dtype=int)
        cv = cv_scores(X_delta, y_delta, **cv_kwargs)
        paired_delta_cv_by_layer[str(layer)] = cv_summary(cv)
        if layer == selected_layer:
            paired_delta_selected_X = X_delta
            paired_delta_selected_cv = cv
            paired_delta_y = y_delta

    if paired_delta_selected_X is None:
        raise RuntimeError("selected layer paired-delta matrix was not built")

    incorrect_raw_cv = cv_scores(selected_X[incorrect_mask], y[incorrect_mask], **cv_kwargs)
    incorrect_condition_cv = cv_scores(
        selected_condition_resid_X[incorrect_mask], y[incorrect_mask], **cv_kwargs
    )
    matched_covariates = np.column_stack(
        [
            answer_lengths[incorrect_mask],
            prompt_lengths[incorrect_mask],
            confidences[incorrect_mask],
        ]
    )
    matched_local_idx = matched_binary_indices(
        y[incorrect_mask], matched_covariates, seed=int(cv_kwargs["seed"])
    )
    incorrect_abs_idx = np.where(incorrect_mask)[0][matched_local_idx]
    matched_raw_cv = cv_scores(selected_X[incorrect_abs_idx], y[incorrect_abs_idx], **cv_kwargs)
    matched_condition_cv = cv_scores(
        selected_condition_resid_X[incorrect_abs_idx],
        y[incorrect_abs_idx],
        **cv_kwargs,
    )

    hydra_labels = np.asarray([hydra_component(r) for r in all_rows])
    hydra_counts = dict(Counter(str(x) for x in hydra_labels))
    hydra_components: dict[str, Any] = {}
    for component, count in sorted(hydra_counts.items()):
        binary = (hydra_labels == component).astype(int)
        n_pos = int(binary.sum())
        n_neg = int((binary == 0).sum())
        if n_pos < 5 or n_neg < 5:
            hydra_components[component] = {
                "n_positive": n_pos,
                "n_negative": n_neg,
                "skipped": "requires at least 5 positive and 5 negative rows",
            }
            continue
        component_cv_kwargs = dict(cv_kwargs)
        component_cv_kwargs["n_splits"] = min(int(cv_kwargs["n_splits"]), n_pos, n_neg)
        raw_cv = cv_scores(all_anchor_mats[selected_layer], binary, **component_cv_kwargs)
        resid_cv = cv_scores(selected_condition_resid_all, binary, **component_cv_kwargs)
        hydra_components[component] = {
            "n_positive": n_pos,
            "n_negative": n_neg,
            "raw_anchor": cv_summary(raw_cv),
            "condition_residualized_anchor": cv_summary(resid_cv),
        }

    isolation_panel = {
        "selected_layer": selected_layer,
        "raw_anchor": cv_summary(
            {
                "fold_mean_auc": cv_by_position["anchor"][str(selected_layer)]["fold_mean_auc"],
                "fold_std_auc": cv_by_position["anchor"][str(selected_layer)]["fold_std_auc"],
                "global_oof_auc": selected_oof_auc,
                "fold_aucs": cv_by_position["anchor"][str(selected_layer)]["fold_aucs"],
            }
        ),
        "paired_delta_incorrect_minus_neutral": cv_summary(paired_delta_selected_cv),
        "condition_axis_residualized_anchor": cv_summary(condition_resid_cv),
        "condition_plus_behavior_residualized_anchor": cv_summary(
            condition_behavior_resid_cv
        ),
        "incorrect_only_raw_anchor": cv_summary(incorrect_raw_cv),
        "incorrect_only_condition_residualized_anchor": cv_summary(incorrect_condition_cv),
        "incorrect_only_matched_raw_anchor": {
            **cv_summary(matched_raw_cv),
            "n_rows": int(len(incorrect_abs_idx)),
            "n_positive": int(y[incorrect_abs_idx].sum()),
            "n_negative": int((y[incorrect_abs_idx] == 0).sum()),
            "matching_covariates": ["answer_len_words", "prompt_len_words", "confidence"],
        },
        "incorrect_only_matched_condition_residualized_anchor": {
            **cv_summary(matched_condition_cv),
            "n_rows": int(len(incorrect_abs_idx)),
            "n_positive": int(y[incorrect_abs_idx].sum()),
            "n_negative": int((y[incorrect_abs_idx] == 0).sum()),
            "matching_covariates": ["answer_len_words", "prompt_len_words", "confidence"],
        },
        "paired_delta_by_layer": paired_delta_cv_by_layer,
        "condition_axis_norm": selected_condition_axis_norm,
        "behavioral_residualization_nuisance": [
            "baseline_correct",
            "baseline_refused",
            "answer_len_words_z",
            "prompt_len_words_z",
            "baseline_confidence_z",
        ],
    }

    for row in kept_probe_rows:
        counterpart = rows_by_key.get(row.get("counterpart_row_key"))
        if not counterpart:
            continue
        i_probe = all_by_key[row["row_key"]]
        i_neutral = all_by_key[counterpart["row_key"]]
        probe_score = all_scores_anchor[i_probe]
        neutral_score = all_scores_anchor[i_neutral]
        paired_deltas.append(probe_score - neutral_score)
        paired_rows.append(
            {
                "base_question_id": row.get("stable_identity", {}).get("base_question_id")
                or row.get("base_question_id"),
                "label": int(row["_probe_label"]),
                "incorrect_hint_score": float(probe_score),
                "neutral_score": float(neutral_score),
                "delta_incorrect_minus_neutral": float(probe_score - neutral_score),
                "wrong_hint_followed": bool(row.get("wrong_hint_followed")),
                "baseline_correct": bool(row.get("baseline_correct")),
                "incorrect_answer": row.get("incorrect_answer"),
                "correct_answer": row.get("correct_answer"),
                "baseline_answer_text": row.get("baseline_answer_text"),
                "neutral_answer_text": counterpart.get("baseline_answer_text"),
            }
        )
    paired_deltas_arr = np.asarray(paired_deltas, dtype=np.float64)
    paired_delta_summary = mean_ci(paired_deltas_arr, n=args.bootstrap_n, seed=20260709)

    per_row = []
    for i, row in enumerate(kept_probe_rows):
        per_row.append(
            {
                "row_key": row["row_key"],
                "base_question_id": row.get("stable_identity", {}).get("base_question_id")
                or row.get("base_question_id"),
                "label": int(y[i]),
                "prompt_condition": row.get("prompt_condition"),
                "baseline_correct": bool(row.get("baseline_correct")),
                "baseline_refused": bool(row.get("baseline_refused")),
                "wrong_hint_followed": bool(row.get("wrong_hint_followed")),
                "correct_answer": row.get("correct_answer"),
                "incorrect_answer": row.get("incorrect_answer"),
                "baseline_answer_text": row.get("baseline_answer_text"),
                "answer_len_words": int(answer_lengths[i]),
                "prompt_len_words": int(prompt_lengths[i]),
                "baseline_confidence": float(confidences[i]),
                "selected_logistic_score": float(selected_scores[i]),
                "selected_unit_projection": float(selected_unit_projection[i]),
                "selected_oof_score": float(selected_oof[i]),
                "paired_delta_oof_score": float(paired_delta_selected_cv["oof_scores"][i]),
                "condition_resid_oof_score": float(condition_resid_cv["oof_scores"][i]),
                "condition_behavior_resid_oof_score": float(
                    condition_behavior_resid_cv["oof_scores"][i]
                ),
            }
        )

    top_positive = sorted(per_row, key=lambda r: r["selected_oof_score"], reverse=True)[:12]
    top_negative = sorted(per_row, key=lambda r: r["selected_oof_score"])[:12]

    summary = {
        "schema_version": "aq-readout-diagnostics/v1",
        "inputs": {
            "labels": str(args.labels),
            "rows": str(args.rows),
            "extraction_dir": str(args.extraction_dir),
            "direction": str(args.direction),
        },
        "manifest": {
            "n_rows": manifest.get("n_rows"),
            "n_answered": manifest.get("n_answered"),
            "layers": manifest.get("layers"),
            "position_families": manifest.get("position_families"),
        },
        "label_counts": dict(Counter(int(x) for x in y)),
        "selected_layer": selected_layer,
        "direction_record": {
            "calibration": direction.get("calibration"),
            "provenance_auroc_by_layer": direction.get("provenance", {}).get("auroc_by_layer"),
            "sigma": direction.get("sigma"),
            "raw_norm": direction.get("raw_norm"),
            "normalized": direction.get("normalized"),
        },
        "cv_recomputed": cv_by_position,
        "aq_g1": {
            "gate": "selected anchor held-out AUROC >= 0.70 and bootstrap 95% lower > 0.55",
            "selected_anchor_oof_auc": selected_oof_auc,
            "selected_anchor_oof_bootstrap_ci": selected_oof_ci,
            "selected_anchor_full_direction_auc": rank_auroc(y, selected_scores),
            "selected_anchor_full_direction_bootstrap_ci": selected_full_ci,
            "passes_point": bool(selected_oof_auc >= 0.70),
            "passes_floor": bool(selected_oof_ci["lo"] > 0.55),
            "passes": bool(selected_oof_auc >= 0.70 and selected_oof_ci["lo"] > 0.55),
        },
        "confounds": confounds,
        "isolation_panel": isolation_panel,
        "hydra_component_map": {
            "label_rule": (
                "mutually exclusive labels over all r2 rows: hint_followed, "
                "hint_refused_or_avoid, hint_resisted_correct, hint_other_wrong, "
                "neutral_refused, neutral_correct, neutral_wrong"
            ),
            "counts": hydra_counts,
            "one_vs_rest": hydra_components,
        },
        "neutral_counterpart": {
            "paired_count": len(paired_rows),
            "delta_incorrect_hint_minus_neutral": paired_delta_summary,
            "delta_by_label": {
                str(label): mean_ci(
                    np.asarray(
                        [
                            r["delta_incorrect_minus_neutral"]
                            for r in paired_rows
                            if r["label"] == label
                        ],
                        dtype=np.float64,
                    ),
                    n=args.bootstrap_n,
                    seed=20260710 + label,
                )
                for label in (0, 1)
            },
        },
        "examples": {
            "top_oof_positive_score": top_positive,
            "top_oof_negative_score": top_negative,
        },
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "summary.json", summary)

    with (args.out_dir / "per_row_scores.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(per_row[0].keys()))
        writer.writeheader()
        writer.writerows(per_row)

    with (args.out_dir / "paired_neutral_deltas.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(paired_rows[0].keys()))
        writer.writeheader()
        writer.writerows(paired_rows)

    hydra_rows = []
    for component, rec in hydra_components.items():
        row = {
            "component": component,
            "n_positive": rec.get("n_positive"),
            "n_negative": rec.get("n_negative"),
            "raw_anchor_global_oof_auc": None,
            "condition_residualized_global_oof_auc": None,
            "skipped": rec.get("skipped"),
        }
        if "raw_anchor" in rec:
            row["raw_anchor_global_oof_auc"] = rec["raw_anchor"]["global_oof_auc"]
            row["condition_residualized_global_oof_auc"] = rec[
                "condition_residualized_anchor"
            ]["global_oof_auc"]
        hydra_rows.append(row)
    with (args.out_dir / "hydra_component_map.csv").open(
        "w", encoding="utf-8", newline=""
    ) as fh:
        writer = csv.DictWriter(fh, fieldnames=list(hydra_rows[0].keys()))
        writer.writeheader()
        writer.writerows(hydra_rows)

    print(json.dumps({
        "wrote": str(args.out_dir),
        "selected_layer": selected_layer,
        "aq_g1": summary["aq_g1"],
        "condition_anchor_auroc": condition_anchor["auroc"],
        "condition_answer_end_auroc": condition_answer["auroc"],
        "isolation_panel": {
            key: value["global_oof_auc"]
            for key, value in isolation_panel.items()
            if isinstance(value, dict) and "global_oof_auc" in value
        },
        "hydra_counts": hydra_counts,
        "answer_length_correlation": confounds["answer_length_correlation"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
