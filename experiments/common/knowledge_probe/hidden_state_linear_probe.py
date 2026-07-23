#!/usr/bin/env python3
"""Diagnostic linear probes over hidden-state extraction artifacts.

Reads one hidden-state extraction directory:
  rows.jsonl
  <row_key_with_pipe_as_underscore>__h_base.safetensors
  <row_key_with_pipe_as_underscore>__h_lora.safetensors
  <row_key_with_pipe_as_underscore>__delta.safetensors

This is a smoke/diagnostic analysis layer only. It is not pre-registered
headline evidence and should not be reported as such.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file


DIAGNOSTIC_NOTICE = (
    "DIAGNOSTIC_SMOKE_ONLY: cross-validated ridge linear probe over extraction "
    "artifacts; not pre-registered headline evidence"
)
DEFAULT_ROLES = ("h_base", "h_lora", "delta")
LABEL_TO_INT = {"known": 0, "unknown": 1}


@dataclass(frozen=True)
class ProbeExample:
    row_key: str
    label: str
    y: int
    safe_key: str


def read_rows(extraction_dir: Path) -> tuple[list[ProbeExample], dict]:
    rows_path = extraction_dir / "rows.jsonl"
    if not rows_path.exists():
        raise FileNotFoundError(f"missing rows.jsonl at {rows_path}")

    examples: list[ProbeExample] = []
    skipped: dict[str, int] = {}
    with rows_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            label = str(row.get("label", "")).lower()
            if label not in LABEL_TO_INT:
                skipped[label or "<missing>"] = skipped.get(label or "<missing>", 0) + 1
                continue
            row_key = row.get("probe_pool_row_key")
            if not row_key:
                raise ValueError(f"{rows_path}:{line_no} missing probe_pool_row_key")
            examples.append(
                ProbeExample(
                    row_key=str(row_key),
                    label=label,
                    y=LABEL_TO_INT[label],
                    safe_key=str(row_key).replace("|", "_"),
                )
            )
    return examples, skipped


def load_role_layers(extraction_dir: Path, examples: list[ProbeExample],
                     role: str) -> dict[int, tuple[list[np.ndarray], list[int]]]:
    by_layer: dict[int, tuple[list[np.ndarray], list[int]]] = {}
    for ex in examples:
        shard = extraction_dir / f"{ex.safe_key}__{role}.safetensors"
        if not shard.exists():
            continue
        tensors = load_file(str(shard))
        for name, vec in tensors.items():
            layer = parse_layer_name(name, shard)
            arr = np.asarray(vec, dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(f"{shard}:{name} expected 1-D vector, got {arr.shape}")
            xs, ys = by_layer.setdefault(layer, ([], []))
            xs.append(arr)
            ys.append(ex.y)
    return by_layer


def parse_layer_name(name: str, shard: Path) -> int:
    if not name.startswith("L"):
        raise ValueError(f"{shard} has non-layer tensor key {name!r}; expected L<int>")
    try:
        return int(name[1:])
    except ValueError as exc:
        raise ValueError(
            f"{shard} has non-integer layer tensor key {name!r}; expected L<int>"
        ) from exc


def make_cv_folds(y: np.ndarray, cv: str, cv_folds: int | None) -> tuple[list[np.ndarray] | None, dict]:
    n = int(y.shape[0])
    n_known = int(np.sum(y == LABEL_TO_INT["known"]))
    n_unknown = int(np.sum(y == LABEL_TO_INT["unknown"]))
    if cv == "loo":
        if n < 4 or n_known < 2 or n_unknown < 2:
            return None, {
                "status": "skipped_insufficient_balanced_examples",
                "reason": "leave-one-out requires at least two examples per class",
                "n": n,
                "n_known": n_known,
                "n_unknown": n_unknown,
                "cv_strategy": cv,
                "cv_folds": n,
            }
        return [np.asarray([holdout], dtype=np.int64) for holdout in range(n)], {
            "cv_strategy": cv,
            "cv_folds": n,
        }

    if cv != "stratified_kfold":
        raise ValueError(f"unsupported cv strategy {cv!r}")
    if cv_folds is None:
        raise ValueError("--cv-folds is required when --cv stratified_kfold")
    folds_count = int(cv_folds)
    if folds_count < 2:
        raise ValueError("--cv-folds must be at least 2")
    if folds_count > n:
        raise ValueError("--cv-folds cannot exceed the number of labeled examples")
    if n_known < folds_count or n_unknown < folds_count:
        return None, {
            "status": "skipped_insufficient_balanced_examples",
            "reason": "stratified k-fold requires at least one example per class in each fold",
            "n": n,
            "n_known": n_known,
            "n_unknown": n_unknown,
            "cv_strategy": cv,
            "cv_folds": folds_count,
        }

    folds: list[list[int]] = [[] for _ in range(folds_count)]
    for label_value in (LABEL_TO_INT["known"], LABEL_TO_INT["unknown"]):
        label_indices = np.flatnonzero(y == label_value)
        for offset, idx in enumerate(label_indices.tolist()):
            folds[offset % folds_count].append(idx)
    return [np.asarray(sorted(fold), dtype=np.int64) for fold in folds], {
        "cv_strategy": cv,
        "cv_folds": folds_count,
    }


def cv_ridge_probe(x: np.ndarray, y: np.ndarray, ridge: float, cv: str,
                   cv_folds: int | None = None) -> dict:
    n = int(y.shape[0])
    n_known = int(np.sum(y == LABEL_TO_INT["known"]))
    n_unknown = int(np.sum(y == LABEL_TO_INT["unknown"]))
    folds, cv_info = make_cv_folds(y, cv, cv_folds)
    if folds is None:
        return cv_info

    predictions = np.full(n, -1, dtype=np.int64)
    scores = np.full(n, np.nan, dtype=np.float64)
    for test_indices in folds:
        train_mask = np.ones(n, dtype=bool)
        train_mask[test_indices] = False
        train_x = x[train_mask]
        train_y = y[train_mask]
        if len(set(train_y.tolist())) < 2:
            return {
                "status": "skipped_insufficient_balanced_examples",
                "reason": "a training fold contains only one class",
                "n": n,
                "n_known": n_known,
                "n_unknown": n_unknown,
                **cv_info,
            }

        mean = train_x.mean(axis=0)
        std = train_x.std(axis=0)
        std[std == 0.0] = 1.0
        train_z = (train_x - mean) / std
        test_z = (x[test_indices] - mean) / std

        target = np.where(train_y == LABEL_TO_INT["unknown"], 1.0, -1.0)
        for local_idx, row_idx in enumerate(test_indices.tolist()):
            score = ridge_score(train_z, target, test_z[local_idx], ridge)
            scores[row_idx] = score
            predictions[row_idx] = (
                LABEL_TO_INT["unknown"] if score >= 0.0 else LABEL_TO_INT["known"]
            )

    if np.any(predictions < 0):
        return {
            "status": "skipped_incomplete_cv_predictions",
            "reason": "cross-validation did not score every labeled example",
            "n": n,
            "n_known": n_known,
            "n_unknown": n_unknown,
            **cv_info,
        }

    correct = predictions == y
    known_mask = y == LABEL_TO_INT["known"]
    unknown_mask = y == LABEL_TO_INT["unknown"]
    known_acc = float(np.mean(correct[known_mask]))
    unknown_acc = float(np.mean(correct[unknown_mask]))
    return {
        "status": "ok",
        "n": n,
        "n_known": n_known,
        "n_unknown": n_unknown,
        "correct": int(np.sum(correct)),
        "accuracy": float(np.mean(correct)),
        "known_accuracy": known_acc,
        "unknown_accuracy": unknown_acc,
        "balanced_accuracy": float((known_acc + unknown_acc) / 2.0),
        "mean_score": float(np.mean(scores)),
        **cv_info,
    }


def loo_ridge_probe(x: np.ndarray, y: np.ndarray, ridge: float) -> dict:
    return cv_ridge_probe(x, y, ridge, cv="loo")


def ridge_score(train_x: np.ndarray, target: np.ndarray, test_x: np.ndarray,
                ridge: float) -> float:
    """Fit ridge linear regression with an unpenalized intercept, score one row.

    The extraction tensors are high dimensional (e.g. width 2560) and the MVP
    diagnostic slice is small (32 rows). Solving the primal `(d+1)x(d+1)` system
    per fold would be wasteful, so for `d > n` we use the equivalent centered
    dual solve: `w = Xc.T @ inv(Xc @ Xc.T + ridge I) @ yc`, with the intercept
    recovered as `target.mean() - train_x.mean(0) @ w`.
    """
    if ridge <= 0:
        raise ValueError("ridge must be positive")
    n, d = train_x.shape
    x_mean = train_x.mean(axis=0)
    y_mean = float(target.mean())
    x_centered = train_x - x_mean
    y_centered = target - y_mean

    if d > n:
        lhs = x_centered @ x_centered.T + ridge * np.eye(n, dtype=np.float64)
        try:
            alpha = np.linalg.solve(lhs, y_centered)
        except np.linalg.LinAlgError:
            alpha = np.linalg.pinv(lhs) @ y_centered
        weights = x_centered.T @ alpha
    else:
        lhs = x_centered.T @ x_centered + ridge * np.eye(d, dtype=np.float64)
        rhs = x_centered.T @ y_centered
        try:
            weights = np.linalg.solve(lhs, rhs)
        except np.linalg.LinAlgError:
            weights = np.linalg.pinv(lhs) @ rhs
    intercept = y_mean - float(x_mean @ weights)
    return float(test_x @ weights + intercept)


def evaluate(extraction_dir: Path, roles: tuple[str, ...], ridge: float, cv: str = "loo",
             cv_folds: int | None = None) -> tuple[list[dict], dict]:
    examples, skipped_labels = read_rows(extraction_dir)
    if not examples:
        raise ValueError(f"{extraction_dir} contains no known/unknown labeled rows")
    output_cv_folds = len(examples) if cv == "loo" else cv_folds
    strategy = (
        "leave_one_out_ridge_linear_classifier_train_fold_standardization_intercept"
        if cv == "loo"
        else "stratified_kfold_ridge_linear_classifier_train_fold_standardization_intercept"
    )

    rows: list[dict] = []
    for role in roles:
        layer_data = load_role_layers(extraction_dir, examples, role)
        for layer in sorted(layer_data):
            xs, ys = layer_data[layer]
            result = cv_ridge_probe(
                np.vstack(xs),
                np.asarray(ys, dtype=np.int64),
                ridge,
                cv=cv,
                cv_folds=cv_folds,
            )
            result.update({
                "role": role,
                "layer": layer,
                "ridge": ridge,
                "diagnostic_notice": DIAGNOSTIC_NOTICE,
            })
            rows.append(result)
        if not layer_data:
            rows.append({
                "role": role,
                "layer": "",
                "ridge": ridge,
                "status": "skipped_missing_role_shards",
                "reason": f"no {role!r} safetensors shards found",
                "n": 0,
                "n_known": 0,
                "n_unknown": 0,
                "cv_strategy": cv,
                "cv_folds": output_cv_folds,
                "diagnostic_notice": DIAGNOSTIC_NOTICE,
            })

    metadata = {
        "analysis_type": "hidden_state_linear_probe_diagnostic_smoke",
        "diagnostic_notice": DIAGNOSTIC_NOTICE,
        "extraction_dir": str(extraction_dir),
        "roles": list(roles),
        "ridge": ridge,
        "cv_strategy": cv,
        "cv_folds": output_cv_folds,
        "strategy": strategy,
        "dependencies": ["numpy", "safetensors"],
        "n_labeled_rows": len(examples),
        "label_counts": {
            label: sum(1 for ex in examples if ex.label == label)
            for label in sorted(LABEL_TO_INT)
        },
        "skipped_input_labels": skipped_labels,
        "results": rows,
    }
    return rows, metadata


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "role", "layer", "status", "n", "n_known", "n_unknown", "correct",
        "accuracy", "known_accuracy", "unknown_accuracy", "balanced_accuracy",
        "mean_score", "ridge", "cv_strategy", "cv_folds", "reason", "diagnostic_notice",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extraction_dir", type=Path,
                        help="directory containing rows.jsonl and safetensors shards")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="directory for summaries; defaults to extraction_dir")
    parser.add_argument("--prefix", default="hidden_state_linear_probe_diagnostic",
                        help="output filename prefix")
    parser.add_argument("--roles", nargs="+", default=list(DEFAULT_ROLES),
                        choices=list(DEFAULT_ROLES),
                        help="tensor roles to evaluate")
    parser.add_argument("--ridge", type=float, default=1.0,
                        help="ridge penalty for the fold-local linear classifier")
    parser.add_argument("--cv", choices=["loo", "stratified_kfold"], default="loo",
                        help="cross-validation strategy; default preserves leave-one-out")
    parser.add_argument("--cv-folds", type=int, default=None,
                        help="number of folds when --cv stratified_kfold")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    extraction_dir = args.extraction_dir.resolve()
    output_dir = (args.output_dir or extraction_dir).resolve()
    rows, metadata = evaluate(
        extraction_dir=extraction_dir,
        roles=tuple(args.roles),
        ridge=float(args.ridge),
        cv=args.cv,
        cv_folds=args.cv_folds,
    )
    csv_path = output_dir / f"{args.prefix}.csv"
    json_path = output_dir / f"{args.prefix}.json"
    write_csv(csv_path, rows)
    write_json(json_path, metadata)
    print(DIAGNOSTIC_NOTICE)
    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")


if __name__ == "__main__":
    main()
