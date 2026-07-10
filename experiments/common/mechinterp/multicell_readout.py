#!/usr/bin/env python3
"""Multiclass hidden-state readouts for Phase 3 behavior cells.

This CPU-only analysis asks whether behavior cells are linearly readable as a
multi-dimensional subspace rather than as one hand-built axis. It is exploratory
mechanistic evidence, not a causal intervention or headline result.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

try:
    from safetensors.numpy import load_file as load_safetensors
except ImportError as exc:  # pragma: no cover
    load_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_sae_behavior_feature_analysis import row_matches_filter
from phase3_sae_smoke import (
    SaeSmokeError,
    load_json,
    repo_relative,
    resolve_path,
    safe_row_key,
    validate_output_root,
)


ANALYSIS_TYPE = "phase3_multicell_hidden_state_readout"
NOTICE = "MULTICELL_READOUT_ONLY"
DEFAULT_ROLES = ("h_base", "h_lora", "delta")


class MulticellReadoutError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise MulticellReadoutError(f"{path} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_manifest(path: Path, *, roles: list[str]) -> dict[str, Any]:
    if not path.is_file():
        raise MulticellReadoutError(f"missing extraction manifest: {repo_relative(path)}")
    manifest = load_json(path)
    if manifest.get("status") != "ok":
        raise MulticellReadoutError(f"{repo_relative(path)} status is not ok")
    if manifest.get("verified") is not True:
        raise MulticellReadoutError(f"{repo_relative(path)} verified is not true")
    if manifest.get("persistence_format") != "safetensors":
        raise MulticellReadoutError(f"{repo_relative(path)} persistence_format is not safetensors")
    tensor_shapes = manifest.get("tensor_shapes")
    if not isinstance(tensor_shapes, dict):
        raise MulticellReadoutError(f"{repo_relative(path)} missing tensor_shapes")
    for role in roles:
        shape = tensor_shapes.get(role)
        if (
            not isinstance(shape, list)
            or len(shape) != 2
            or not all(isinstance(value, int) for value in shape)
        ):
            raise MulticellReadoutError(f"{repo_relative(path)} missing valid tensor shape for role {role!r}")
    return manifest


def load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise MulticellReadoutError(f"missing rows file: {repo_relative(path)}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    with path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise MulticellReadoutError(f"{repo_relative(path)}:{line_number} row is not an object")
            row_key = row.get("row_key") or row.get("probe_pool_row_key")
            if not isinstance(row_key, str) or not row_key:
                raise MulticellReadoutError(f"{repo_relative(path)}:{line_number} missing row_key")
            if row_key in seen:
                raise MulticellReadoutError(f"{repo_relative(path)}:{line_number} duplicate row_key {row_key!r}")
            seen.add(row_key)
            row["row_key"] = row_key
            rows.append(row)
    return rows


def shard_candidates(extraction_dir: Path, row_key: str, role: str) -> list[Path]:
    candidates = [
        extraction_dir / f"{safe_row_key(row_key)}__{role}.safetensors",
        extraction_dir / f"{row_key.replace('|', '_')}__{role}.safetensors",
        extraction_dir / f"{row_key}__{role}.safetensors",
    ]
    deduped: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    return deduped


def load_role_cube(
    extraction_dir: Path,
    rows: list[dict[str, Any]],
    *,
    role: str,
    layer_count: int,
    hidden_dim: int,
) -> np.ndarray:
    if load_safetensors is None:
        raise MulticellReadoutError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    cube = np.empty((len(rows), layer_count, hidden_dim), dtype=np.float32)
    for row_index, row in enumerate(rows):
        row_key = row["row_key"]
        shard = next((path for path in shard_candidates(extraction_dir, row_key, role) if path.is_file()), None)
        if shard is None:
            attempted = ", ".join(repo_relative(path) for path in shard_candidates(extraction_dir, row_key, role))
            raise MulticellReadoutError(f"missing role shard for {row_key!r}; tried {attempted}")
        tensors = load_safetensors(str(shard))
        for layer in range(layer_count):
            tensor_key = f"L{layer}"
            if tensor_key not in tensors:
                raise MulticellReadoutError(f"{repo_relative(shard)} missing tensor key {tensor_key}")
            vector = np.asarray(tensors[tensor_key], dtype=np.float32)
            if vector.ndim != 1 or vector.shape[0] != hidden_dim:
                raise MulticellReadoutError(
                    f"{repo_relative(shard)} {tensor_key} shape mismatch: "
                    f"expected ({hidden_dim},), got {tuple(vector.shape)}"
                )
            cube[row_index, layer, :] = vector
    return cube


def parse_cells(config: dict[str, Any]) -> list[dict[str, Any]]:
    cells = config.get("cells")
    if not isinstance(cells, list) or len(cells) < 2:
        raise MulticellReadoutError("analysis.cells must contain at least two cells")
    parsed: list[dict[str, Any]] = []
    seen: set[str] = set()
    for cell in cells:
        if not isinstance(cell, dict):
            raise MulticellReadoutError("analysis.cells entries must be mappings")
        label = cell.get("label")
        row_filter = cell.get("filter")
        if not isinstance(label, str) or not label:
            raise MulticellReadoutError("each cell must define a non-empty label")
        if label in seen:
            raise MulticellReadoutError(f"duplicate cell label {label!r}")
        if not isinstance(row_filter, dict):
            raise MulticellReadoutError(f"cell {label!r} must define filter")
        seen.add(label)
        parsed.append({"label": label, "filter": row_filter})
    return parsed


def cell_labels(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    cells: list[dict[str, Any]],
) -> tuple[np.ndarray, dict[str, int], dict[str, int]]:
    labels = np.full(len(rows), -1, dtype=np.int64)
    skipped = {"unmatched": 0, "overlap": 0}
    for row_index, row in enumerate(rows):
        matches = [
            cell_index
            for cell_index, cell in enumerate(cells)
            if row_matches_filter(row, arm, cell["filter"])
        ]
        if len(matches) == 1:
            labels[row_index] = matches[0]
        elif len(matches) == 0:
            skipped["unmatched"] += 1
        else:
            skipped["overlap"] += 1
    counts = {
        cells[cell_index]["label"]: int(np.count_nonzero(labels == cell_index))
        for cell_index in range(len(cells))
    }
    return labels, counts, skipped


def make_stratified_folds(labels: np.ndarray, *, fold_count: int) -> tuple[list[np.ndarray] | None, str]:
    if fold_count < 2:
        raise MulticellReadoutError("cv_folds must be at least 2")
    classes = sorted(int(value) for value in set(labels.tolist()) if value >= 0)
    if len(classes) < 2:
        return None, "need at least two classes"
    for class_id in classes:
        if int(np.count_nonzero(labels == class_id)) < fold_count:
            return None, "each class needs at least cv_folds examples"
    folds: list[list[int]] = [[] for _ in range(fold_count)]
    for class_id in classes:
        indices = np.flatnonzero(labels == class_id)
        for offset, index in enumerate(indices.tolist()):
            folds[offset % fold_count].append(index)
    return [np.asarray(sorted(fold), dtype=np.int64) for fold in folds], ""


def parse_rank(value: Any) -> int | None:
    if isinstance(value, str):
        if value.lower() == "full":
            return None
        try:
            value = int(value)
        except ValueError as exc:
            raise MulticellReadoutError(f"invalid rank {value!r}") from exc
    rank = int(value)
    if rank <= 0:
        raise MulticellReadoutError("readout ranks must be positive or 'full'")
    return rank


def fit_predict_fold(
    train_x: np.ndarray,
    train_y: np.ndarray,
    test_x: np.ndarray,
    *,
    class_count: int,
    ridge: float,
    rank: int | None,
    class_weighting: str,
) -> tuple[np.ndarray, int]:
    if ridge <= 0.0:
        raise MulticellReadoutError("ridge must be positive")
    sample_weight = class_weights(train_y, class_count=class_count, mode=class_weighting)
    mean = weighted_mean(train_x, sample_weight)
    std = weighted_std(train_x, sample_weight, mean)
    std[std == 0.0] = 1.0
    train_z = (train_x - mean) / std
    test_z = (test_x - mean) / std

    effective_rank = train_z.shape[1]
    if rank is not None:
        max_rank = min(int(rank), train_z.shape[0] - 1, train_z.shape[1])
        max_rank = max(max_rank, 1)
        _, _, vt = np.linalg.svd(train_z, full_matrices=False)
        components = vt[:max_rank].T
        train_z = train_z @ components
        test_z = test_z @ components
        effective_rank = max_rank

    y_onehot = np.zeros((train_y.shape[0], class_count), dtype=np.float64)
    y_onehot[np.arange(train_y.shape[0]), train_y] = 1.0
    y_mean = weighted_mean(y_onehot, sample_weight)
    y_centered = y_onehot - y_mean
    sqrt_weight = np.sqrt(sample_weight)[:, None]
    train_weighted = train_z * sqrt_weight
    target_weighted = y_centered * sqrt_weight
    gram = train_weighted @ train_weighted.T + ridge * np.eye(train_z.shape[0], dtype=np.float64)
    try:
        alpha = np.linalg.solve(gram, target_weighted)
    except np.linalg.LinAlgError:
        alpha = np.linalg.pinv(gram) @ target_weighted
    weights = train_weighted.T @ alpha
    scores = test_z @ weights + y_mean
    return np.argmax(scores, axis=1).astype(np.int64), int(effective_rank)


def class_weights(labels: np.ndarray, *, class_count: int, mode: str) -> np.ndarray:
    if mode == "none":
        return np.ones(labels.shape[0], dtype=np.float64)
    if mode != "balanced":
        raise MulticellReadoutError("class_weighting must be 'balanced' or 'none'")
    weights = np.ones(labels.shape[0], dtype=np.float64)
    for class_id in range(class_count):
        mask = labels == class_id
        count = int(np.count_nonzero(mask))
        if count == 0:
            continue
        weights[mask] = labels.shape[0] / float(class_count * count)
    return weights


def weighted_mean(x: np.ndarray, weight: np.ndarray) -> np.ndarray:
    return np.average(x, axis=0, weights=weight)


def weighted_std(x: np.ndarray, weight: np.ndarray, mean: np.ndarray) -> np.ndarray:
    return np.sqrt(np.average((x - mean) ** 2, axis=0, weights=weight))


def score_predictions(y: np.ndarray, predictions: np.ndarray, *, class_count: int) -> dict[str, Any]:
    correct = predictions == y
    recalls: list[float] = []
    confusion = np.zeros((class_count, class_count), dtype=np.int64)
    for actual, predicted in zip(y.tolist(), predictions.tolist(), strict=True):
        confusion[int(actual), int(predicted)] += 1
    for class_id in range(class_count):
        mask = y == class_id
        recalls.append(float(np.mean(correct[mask])) if bool(np.any(mask)) else float("nan"))
    return {
        "accuracy": float(np.mean(correct)),
        "macro_recall": float(np.nanmean(np.asarray(recalls, dtype=np.float64))),
        "correct": int(np.count_nonzero(correct)),
        "confusion": confusion,
        "recalls": recalls,
    }


def evaluate_layer(
    x: np.ndarray,
    labels: np.ndarray,
    *,
    class_count: int,
    ridge: float,
    cv_folds: int,
    ranks: list[int | None],
    class_weighting: str,
) -> list[dict[str, Any]]:
    valid_mask = labels >= 0
    x = x[valid_mask].astype(np.float64)
    y = labels[valid_mask].astype(np.int64)
    folds, skip_reason = make_stratified_folds(y, fold_count=cv_folds)
    rows: list[dict[str, Any]] = []
    if folds is None:
        return [
            {
                "status": "skipped_insufficient_rows",
                "reason": skip_reason,
                "rank": "full" if rank is None else rank,
                "effective_rank": "",
                "n": int(y.shape[0]),
            }
            for rank in ranks
        ]
    for rank in ranks:
        predictions = np.full(y.shape[0], -1, dtype=np.int64)
        effective_ranks: list[int] = []
        for test_indices in folds:
            train_mask = np.ones(y.shape[0], dtype=bool)
            train_mask[test_indices] = False
            pred, effective_rank = fit_predict_fold(
                x[train_mask],
                y[train_mask],
                x[test_indices],
                class_count=class_count,
                ridge=ridge,
                rank=rank,
                class_weighting=class_weighting,
            )
            predictions[test_indices] = pred
            effective_ranks.append(effective_rank)
        metrics = score_predictions(y, predictions, class_count=class_count)
        rows.append(
            {
                "status": "ok",
                "rank": "full" if rank is None else rank,
                "effective_rank": max(effective_ranks),
                "n": int(y.shape[0]),
                "correct": metrics["correct"],
                "accuracy": metrics["accuracy"],
                "macro_recall": metrics["macro_recall"],
                "confusion": metrics["confusion"],
                "recalls": metrics["recalls"],
            }
        )
    return rows


def run_extraction(
    extraction: dict[str, Any],
    *,
    output_root: Path,
    analysis: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    label = extraction.get("label")
    if not isinstance(label, str) or not label:
        raise MulticellReadoutError("each extraction must define a non-empty label")
    behavior_arm = extraction.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise MulticellReadoutError(f"extraction {label!r} must define behavior_arm")
    extraction_dir = resolve_path(extraction["extraction_dir"])
    rows_path = resolve_path(extraction.get("rows_path", extraction_dir / "rows.jsonl"))
    manifest_path = resolve_path(extraction.get("extraction_manifest", extraction_dir / "manifest.json"))
    roles = extraction.get("roles", analysis.get("roles", list(DEFAULT_ROLES)))
    if not isinstance(roles, list) or not roles:
        raise MulticellReadoutError(f"extraction {label!r} must define non-empty roles")
    roles = [str(role) for role in roles]
    cells = parse_cells(analysis)
    min_rows_per_cell = int(analysis.get("min_rows_per_cell", 2))
    cv_folds = int(analysis.get("cv_folds", 4))
    ridge = float(analysis.get("ridge", 1.0))
    class_weighting = str(analysis.get("class_weighting", "balanced"))
    ranks = [parse_rank(value) for value in analysis.get("ranks", [1, 2, 4, 8, "full"])]

    manifest = validate_manifest(manifest_path, roles=roles)
    rows = load_rows(rows_path)
    labels, counts, skipped = cell_labels(rows, arm=behavior_arm, cells=cells)
    low_cells = {cell: count for cell, count in counts.items() if count < min_rows_per_cell}
    if low_cells:
        raise MulticellReadoutError(f"extraction {label!r} has insufficient cell counts: {low_cells}")

    all_rows: list[dict[str, Any]] = []
    confusion_payload: list[dict[str, Any]] = []
    for role in roles:
        layer_count, hidden_dim = manifest["tensor_shapes"][role]
        cube = load_role_cube(extraction_dir, rows, role=role, layer_count=layer_count, hidden_dim=hidden_dim)
        for layer in range(layer_count):
            eval_rows = evaluate_layer(
                cube[:, layer, :],
                labels,
                class_count=len(cells),
                ridge=ridge,
                cv_folds=cv_folds,
                ranks=ranks,
                class_weighting=class_weighting,
            )
            for eval_row in eval_rows:
                row: dict[str, Any] = {
                    "analysis_type": ANALYSIS_TYPE,
                    "notice": NOTICE,
                    "extraction_label": label,
                    "behavior_arm": behavior_arm,
                    "role": role,
                    "layer": layer,
                    "rank": eval_row["rank"],
                    "effective_rank": eval_row["effective_rank"],
                    "status": eval_row["status"],
                    "n": eval_row["n"],
                    "ridge": ridge,
                    "cv_folds": cv_folds,
                    "class_weighting": class_weighting,
                    "cell_count_min": min(counts.values()),
                    "cell_count_max": max(counts.values()),
                    "accuracy": eval_row.get("accuracy", ""),
                    "macro_recall": eval_row.get("macro_recall", ""),
                    "correct": eval_row.get("correct", ""),
                    "reason": eval_row.get("reason", ""),
                }
                for cell_index, cell in enumerate(cells):
                    row[f"count_{cell['label']}"] = counts[cell["label"]]
                    recalls = eval_row.get("recalls")
                    row[f"recall_{cell['label']}"] = (
                        float(recalls[cell_index]) if isinstance(recalls, list) else ""
                    )
                all_rows.append(row)
                if eval_row["status"] == "ok":
                    confusion_payload.append(
                        {
                            "extraction_label": label,
                            "role": role,
                            "layer": layer,
                            "rank": eval_row["rank"],
                            "cells": [cell["label"] for cell in cells],
                            "confusion": eval_row["confusion"].tolist(),
                        }
                    )
    output_dir = output_root / label
    readout_path = output_dir / "readout_summary.csv"
    top_path = output_dir / "top_readouts.csv"
    confusion_path = output_dir / "confusion.json"
    summary_path = output_dir / "summary.json"
    top_rows = top_readouts(all_rows)
    write_csv(readout_path, all_rows)
    write_csv(top_path, top_rows)
    write_json(confusion_path, {"cells": [cell["label"] for cell in cells], "items": confusion_payload})
    summary = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "extraction_label": label,
        "behavior_arm": behavior_arm,
        "extraction_dir": repo_relative(extraction_dir),
        "extraction_manifest": repo_relative(manifest_path),
        "rows_path": repo_relative(rows_path),
        "row_count": len(rows),
        "labeled_row_count": int(np.count_nonzero(labels >= 0)),
        "roles": roles,
        "ranks": ["full" if rank is None else rank for rank in ranks],
        "cell_counts": counts,
        "skipped_rows": skipped,
        "outputs": {
            "readout_summary": repo_relative(readout_path),
            "top_readouts": repo_relative(top_path),
            "confusion": repo_relative(confusion_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return all_rows, summary


def top_readouts(rows: list[dict[str, Any]], *, per_group: int = 5) -> list[dict[str, Any]]:
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in ok_rows:
        grouped.setdefault((str(row["extraction_label"]), str(row["role"])), []).append(row)
    top: list[dict[str, Any]] = []
    for group_rows in grouped.values():
        ranked = sorted(
            group_rows,
            key=lambda row: (
                float(row["macro_recall"]),
                float(row["accuracy"]),
                -9999 if row["rank"] == "full" else -int(row["effective_rank"]),
            ),
            reverse=True,
        )
        top.extend(ranked[:per_group])
    return top


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    analysis = config.get("analysis")
    extractions = config.get("extractions")
    if not isinstance(output, dict) or "root" not in output:
        raise MulticellReadoutError("config must define output.root")
    if not isinstance(analysis, dict):
        raise MulticellReadoutError("config must define analysis")
    if not isinstance(extractions, list) or not extractions:
        raise MulticellReadoutError("config must define non-empty extractions")
    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(extraction["extraction_dir"]) for extraction in extractions]
    validate_output_root(output_root, extraction_dirs)

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for extraction in extractions:
        rows, summary = run_extraction(extraction, output_root=output_root, analysis=analysis)
        all_rows.extend(rows)
        summaries.append(summary)

    combined_path = output_root / "readout_summary_all.csv"
    top_path = output_root / "top_readouts_all.csv"
    summary_path = output_root / "summary.json"
    write_csv(combined_path, all_rows)
    write_csv(top_path, top_readouts(all_rows))
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "output_root": repo_relative(output_root),
        "extraction_count": len(summaries),
        "row_count": len(all_rows),
        "outputs": {
            "readout_summary_all": repo_relative(combined_path),
            "top_readouts_all": repo_relative(top_path),
            "summary": repo_relative(summary_path),
        },
        "extraction_summaries": [summary["outputs"]["summary"] for summary in summaries],
    }
    write_json(summary_path, summary)
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (MulticellReadoutError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
