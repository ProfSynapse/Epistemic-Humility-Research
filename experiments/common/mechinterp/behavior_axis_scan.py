#!/usr/bin/env python3
"""Layerwise behavior-axis scans over mechinterp hidden-state extractions.

This is an offline CPU analysis. It reads existing hidden-state shards and
behavior labels from extraction rows, then measures how separable configured
behavior groups are at each layer and tensor role.
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
except ImportError as exc:  # pragma: no cover - only exercised without dependency
    load_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "archive/experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from sae_behavior_feature_analysis import row_matches_filter
from sae_smoke import (
    SaeSmokeError,
    load_json,
    load_rows,
    repo_relative,
    resolve_path,
    safe_row_key,
    validate_output_root,
)


ANALYSIS_TYPE = "mechinterp_behavior_axis_scan"
NOTICE = "BEHAVIOR_AXIS_SCAN_ONLY"
DEFAULT_ROLES = ("h_base", "h_lora", "delta")


class BehaviorAxisScanError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise BehaviorAxisScanError(f"{path} did not load to a YAML object")
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
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_manifest(path: Path, *, roles: list[str]) -> dict[str, Any]:
    if not path.is_file():
        raise BehaviorAxisScanError(f"missing extraction manifest: {repo_relative(path)}")
    manifest = load_json(path)
    if manifest.get("status") != "ok":
        raise BehaviorAxisScanError(f"{repo_relative(path)} status is not ok")
    if manifest.get("verified") is not True:
        raise BehaviorAxisScanError(f"{repo_relative(path)} verified is not true")
    if manifest.get("persistence_format") != "safetensors":
        raise BehaviorAxisScanError(f"{repo_relative(path)} persistence_format is not safetensors")
    tensor_shapes = manifest.get("tensor_shapes")
    if not isinstance(tensor_shapes, dict):
        raise BehaviorAxisScanError(f"{repo_relative(path)} missing tensor_shapes")
    for role in roles:
        shape = tensor_shapes.get(role)
        if not isinstance(shape, list) or len(shape) != 2 or not all(isinstance(value, int) for value in shape):
            raise BehaviorAxisScanError(f"{repo_relative(path)} missing valid tensor shape for role {role!r}")
    return manifest


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
        raise BehaviorAxisScanError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    cube = np.empty((len(rows), layer_count, hidden_dim), dtype=np.float32)
    for row_index, row in enumerate(rows):
        row_key = row["row_key"]
        shard = next((path for path in shard_candidates(extraction_dir, row_key, role) if path.is_file()), None)
        if shard is None:
            attempted = ", ".join(repo_relative(path) for path in shard_candidates(extraction_dir, row_key, role))
            raise BehaviorAxisScanError(f"missing role shard for {row_key!r}; tried {attempted}")
        tensors = load_safetensors(str(shard))
        for layer in range(layer_count):
            tensor_key = f"L{layer}"
            if tensor_key not in tensors:
                raise BehaviorAxisScanError(f"{repo_relative(shard)} missing tensor key {tensor_key}")
            vector = np.asarray(tensors[tensor_key], dtype=np.float32)
            if vector.ndim != 1 or vector.shape[0] != hidden_dim:
                raise BehaviorAxisScanError(
                    f"{repo_relative(shard)} {tensor_key} shape mismatch: "
                    f"expected ({hidden_dim},), got {tuple(vector.shape)}"
                )
            cube[row_index, layer, :] = vector
    return cube


def load_extraction_rows(extraction_dir: Path, *, rows_path: Path | None = None) -> list[dict[str, Any]]:
    if rows_path is None:
        return load_rows(extraction_dir)
    if not rows_path.is_file():
        raise BehaviorAxisScanError(f"missing rows file: {repo_relative(rows_path)}")
    rows: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    with rows_path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise BehaviorAxisScanError(f"{repo_relative(rows_path)}:{line_number} row is not an object")
            label = row.get("label")
            if label not in {"known", "unknown"}:
                raise BehaviorAxisScanError(f"{repo_relative(rows_path)}:{line_number} invalid label {label!r}")
            row_key = row.get("row_key") or row.get("probe_pool_row_key")
            if not isinstance(row_key, str) or not row_key:
                raise BehaviorAxisScanError(f"{repo_relative(rows_path)}:{line_number} missing row_key")
            if row_key in seen_keys:
                raise BehaviorAxisScanError(f"{repo_relative(rows_path)}:{line_number} duplicate row_key {row_key!r}")
            seen_keys.add(row_key)
            row["row_key"] = row_key
            rows.append(row)
    return rows


def rank_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    positives = labels.astype(bool)
    n_pos = int(np.count_nonzero(positives))
    n_neg = int(scores.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")

    order = np.argsort(scores, kind="mergesort")
    sorted_scores = scores[order]
    ranks = np.empty(scores.size, dtype=np.float64)
    start = 0
    while start < scores.size:
        end = start + 1
        while end < scores.size and sorted_scores[end] == sorted_scores[start]:
            end += 1
        average_rank = (start + 1 + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    rank_sum_pos = float(np.sum(ranks[positives]))
    return (rank_sum_pos - (n_pos * (n_pos + 1) / 2.0)) / float(n_pos * n_neg)


def cohen_d(positive: np.ndarray, negative: np.ndarray) -> float:
    positive_std = float(np.std(positive))
    negative_std = float(np.std(negative))
    pooled = float(np.sqrt((positive_std**2 + negative_std**2) / 2.0))
    if pooled <= 1e-12:
        return 0.0
    return float((np.mean(positive) - np.mean(negative)) / pooled)


def balanced_accuracy(positive: np.ndarray, negative: np.ndarray) -> float:
    threshold = float((np.mean(positive) + np.mean(negative)) / 2.0)
    tpr = float(np.mean(positive >= threshold))
    tnr = float(np.mean(negative < threshold))
    return (tpr + tnr) / 2.0


def contrast_masks(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    contrast: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    positive = contrast.get("positive")
    negative = contrast.get("negative")
    if not isinstance(positive, dict) or not isinstance(negative, dict):
        raise BehaviorAxisScanError(f"contrast {contrast.get('name')} must define positive/negative filters")
    positive_mask = np.asarray([row_matches_filter(row, arm, positive) for row in rows], dtype=bool)
    negative_mask = np.asarray([row_matches_filter(row, arm, negative) for row in rows], dtype=bool)
    if bool(np.any(positive_mask & negative_mask)):
        raise BehaviorAxisScanError(f"contrast {contrast.get('name')} filters overlap")
    return positive_mask, negative_mask


def scan_layer(
    matrix: np.ndarray,
    *,
    positive_mask: np.ndarray,
    negative_mask: np.ndarray,
) -> tuple[dict[str, Any], np.ndarray]:
    positive = matrix[positive_mask]
    negative = matrix[negative_mask]
    positive_mean = np.mean(positive, axis=0)
    negative_mean = np.mean(negative, axis=0)
    direction = positive_mean - negative_mean
    norm = float(np.linalg.norm(direction.astype(np.float64)))
    unit_direction = direction if norm <= 1e-12 else (direction / norm).astype(np.float32)
    positive_projection = positive @ unit_direction
    negative_projection = negative @ unit_direction
    scores = np.concatenate([positive_projection, negative_projection]).astype(np.float64)
    labels = np.concatenate(
        [np.ones(positive_projection.shape[0], dtype=bool), np.zeros(negative_projection.shape[0], dtype=bool)]
    )
    metrics = {
        "mean_diff_norm": norm,
        "projection_cohen_d": cohen_d(positive_projection, negative_projection),
        "auc": rank_auc(scores, labels),
        "balanced_accuracy": balanced_accuracy(positive_projection, negative_projection),
        "positive_projection_mean": float(np.mean(positive_projection)),
        "negative_projection_mean": float(np.mean(negative_projection)),
        "positive_projection_std": float(np.std(positive_projection)),
        "negative_projection_std": float(np.std(negative_projection)),
    }
    return metrics, np.asarray(unit_direction, dtype=np.float32)


def run_extraction(
    extraction: dict[str, Any],
    *,
    output_root: Path,
    analysis: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    label = extraction.get("label")
    if not isinstance(label, str) or not label:
        raise BehaviorAxisScanError("each extraction must define a non-empty label")
    behavior_arm = extraction.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise BehaviorAxisScanError(f"extraction {label!r} must define behavior_arm")
    extraction_dir = resolve_path(extraction["extraction_dir"])
    manifest_path = resolve_path(extraction.get("extraction_manifest", extraction_dir / "manifest.json"))
    roles = extraction.get("roles", analysis.get("roles", list(DEFAULT_ROLES)))
    if not isinstance(roles, list) or not roles:
        raise BehaviorAxisScanError(f"extraction {label!r} must define non-empty roles")
    roles = [str(role) for role in roles]
    contrasts = extraction.get("contrasts", analysis.get("contrasts"))
    if not isinstance(contrasts, list) or not contrasts:
        raise BehaviorAxisScanError(f"extraction {label!r} must define non-empty contrasts")

    manifest = validate_manifest(manifest_path, roles=roles)
    override_rows_path = extraction.get("rows_path")
    rows_path = resolve_path(override_rows_path) if override_rows_path else None
    rows = load_extraction_rows(extraction_dir, rows_path=rows_path)
    all_rows: list[dict[str, Any]] = []
    contrast_summaries: list[dict[str, Any]] = []
    for role in roles:
        layer_count, hidden_dim = manifest["tensor_shapes"][role]
        cube = load_role_cube(extraction_dir, rows, role=role, layer_count=layer_count, hidden_dim=hidden_dim)
        for contrast in contrasts:
            name = contrast.get("name")
            if not isinstance(name, str) or not name:
                raise BehaviorAxisScanError("each contrast must define non-empty name")
            positive_mask, negative_mask = contrast_masks(rows, arm=behavior_arm, contrast=contrast)
            positive_count = int(np.count_nonzero(positive_mask))
            negative_count = int(np.count_nonzero(negative_mask))
            min_rows = int(contrast.get("min_rows_per_group", 1))
            summary = {
                "extraction_label": label,
                "behavior_arm": behavior_arm,
                "role": role,
                "contrast": name,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "min_rows_per_group": min_rows,
                "skipped": positive_count < min_rows or negative_count < min_rows,
            }
            if summary["skipped"]:
                summary["reason"] = "insufficient_rows"
                contrast_summaries.append(summary)
                continue
            previous_direction: np.ndarray | None = None
            for layer in range(layer_count):
                metrics, direction = scan_layer(cube[:, layer, :], positive_mask=positive_mask, negative_mask=negative_mask)
                previous_cosine = ""
                if previous_direction is not None:
                    previous_cosine = float(np.dot(previous_direction, direction))
                all_rows.append(
                    {
                        "analysis_type": ANALYSIS_TYPE,
                        "notice": NOTICE,
                        "extraction_label": label,
                        "behavior_arm": behavior_arm,
                        "role": role,
                        "layer": layer,
                        "contrast": name,
                        "positive_label": contrast.get("positive_label", "positive"),
                        "negative_label": contrast.get("negative_label", "negative"),
                        "positive_count": positive_count,
                        "negative_count": negative_count,
                        "hidden_dim": hidden_dim,
                        "prev_layer_direction_cosine": previous_cosine,
                        **metrics,
                    }
                )
                previous_direction = direction
            contrast_summaries.append(summary)
    output_dir = output_root / label
    axis_scan_path = output_dir / "axis_scan.csv"
    summary_path = output_dir / "summary.json"
    top_path = output_dir / "top_layers.csv"
    top_rows = top_layers(all_rows)
    write_csv(axis_scan_path, all_rows)
    write_csv(top_path, top_rows)
    summary = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "extraction_label": label,
        "behavior_arm": behavior_arm,
        "extraction_dir": repo_relative(extraction_dir),
        "extraction_manifest": repo_relative(manifest_path),
        "rows_path": repo_relative(rows_path) if rows_path is not None else repo_relative(extraction_dir / "rows.jsonl"),
        "row_count": len(rows),
        "roles": roles,
        "contrast_summaries": contrast_summaries,
        "outputs": {
            "axis_scan": repo_relative(axis_scan_path),
            "top_layers": repo_relative(top_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return all_rows, summary


def top_layers(rows: list[dict[str, Any]], *, per_group: int = 5) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["extraction_label"]), str(row["role"]), str(row["contrast"]))
        grouped.setdefault(key, []).append(row)
    top: list[dict[str, Any]] = []
    for key_rows in grouped.values():
        ranked = sorted(
            key_rows,
            key=lambda row: (abs(float(row["projection_cohen_d"])), float(row["auc"]), float(row["mean_diff_norm"])),
            reverse=True,
        )
        top.extend(ranked[:per_group])
    return top


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    analysis = config.get("analysis", {})
    extractions = config.get("extractions")
    if not isinstance(output, dict) or "root" not in output:
        raise BehaviorAxisScanError("config must define output.root")
    if not isinstance(analysis, dict):
        raise BehaviorAxisScanError("analysis must be a mapping when provided")
    if not isinstance(extractions, list) or not extractions:
        raise BehaviorAxisScanError("config must define non-empty extractions")
    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(extraction["extraction_dir"]) for extraction in extractions]
    validate_output_root(output_root, extraction_dirs)

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for extraction in extractions:
        rows, summary = run_extraction(extraction, output_root=output_root, analysis=analysis)
        all_rows.extend(rows)
        summaries.append(summary)

    combined_path = output_root / "axis_scan_all.csv"
    top_path = output_root / "top_layers_all.csv"
    summary_path = output_root / "summary.json"
    write_csv(combined_path, all_rows)
    write_csv(top_path, top_layers(all_rows))
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "output_root": repo_relative(output_root),
        "extraction_count": len(summaries),
        "row_count": len(all_rows),
        "outputs": {
            "axis_scan_all": repo_relative(combined_path),
            "top_layers_all": repo_relative(top_path),
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
    except (BehaviorAxisScanError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
