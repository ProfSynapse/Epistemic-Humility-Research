#!/usr/bin/env python3
"""Analyze trained Phase 3 SAE feature activations.

This ranks learned SAE features by label separation over existing hidden-state
rows. It is exploratory feature-screening only, not causal evidence.
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

from phase3_sae_smoke import (
    VALID_LABELS,
    SaeSmokeError,
    load_hidden_matrix,
    load_rows,
    repo_relative,
    resolve_path,
)

try:
    from safetensors.torch import load_file as load_torch_safetensors
except ImportError as exc:  # pragma: no cover
    load_torch_safetensors = None
    SAFETENSORS_TORCH_IMPORT_ERROR = exc
else:
    SAFETENSORS_TORCH_IMPORT_ERROR = None


NOTICE = "SAE_FEATURE_ANALYSIS_ONLY"
ANALYSIS_TYPE = "phase3_sae_feature_analysis"


class SaeFeatureAnalysisError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureAnalysisError(f"{path} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureAnalysisError(f"{path} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_selected_rows(run_dir: Path, extraction_dir: Path) -> list[dict[str, Any]]:
    selected_path = run_dir / "selected_rows.jsonl"
    if not selected_path.is_file():
        raise SaeFeatureAnalysisError(f"missing selected rows: {repo_relative(selected_path)}")
    extraction_rows = {row["row_key"]: row for row in load_rows(extraction_dir)}
    selected: list[dict[str, Any]] = []
    with selected_path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row_key = row.get("row_key")
            if not isinstance(row_key, str) or row_key not in extraction_rows:
                raise SaeFeatureAnalysisError(f"{repo_relative(selected_path)}:{line_number} unknown row_key")
            selected.append(extraction_rows[row_key])
    return selected


def compute_codes(x: np.ndarray, weights_path: Path, training: dict[str, Any]) -> np.ndarray:
    if load_torch_safetensors is None:
        raise SaeFeatureAnalysisError(f"safetensors.torch is required: {SAFETENSORS_TORCH_IMPORT_ERROR}")
    tensors = load_torch_safetensors(str(weights_path))
    required = ["encoder.weight", "encoder.bias", "normalization.mean", "normalization.scale"]
    missing = [key for key in required if key not in tensors]
    if missing:
        raise SaeFeatureAnalysisError(f"{repo_relative(weights_path)} missing tensors {missing}")
    encoder_weight = tensors["encoder.weight"].detach().cpu().numpy().astype(np.float32)
    encoder_bias = tensors["encoder.bias"].detach().cpu().numpy().astype(np.float32)
    mean = tensors["normalization.mean"].detach().cpu().numpy().astype(np.float32)
    scale = tensors["normalization.scale"].detach().cpu().numpy().astype(np.float32)
    x_std = (x.astype(np.float32) - mean[None, :]) / np.maximum(scale[None, :], 1e-6)
    pre_code = x_std @ encoder_weight.T + encoder_bias[None, :]
    activation = training.get("activation", "relu_l1")
    if activation == "relu_l1":
        return np.maximum(pre_code, 0.0).astype(np.float32)
    if activation == "topk_relu":
        top_k = int(training["top_k"])
        if top_k <= 0 or top_k > pre_code.shape[1]:
            raise SaeFeatureAnalysisError(f"invalid top_k {top_k} for dictionary size {pre_code.shape[1]}")
        relu_code = np.maximum(pre_code, 0.0)
        indices = np.argpartition(relu_code, -top_k, axis=1)[:, -top_k:]
        codes = np.zeros_like(relu_code)
        row_indices = np.arange(relu_code.shape[0])[:, None]
        codes[row_indices, indices] = relu_code[row_indices, indices]
        return codes.astype(np.float32)
    raise SaeFeatureAnalysisError(f"unsupported activation {activation!r}")


def hidden_dim_from_manifest(manifest_path: Path, role: str) -> int:
    manifest = load_json(manifest_path)
    tensor_shapes = manifest.get("tensor_shapes")
    if not isinstance(tensor_shapes, dict) or role not in tensor_shapes:
        raise SaeFeatureAnalysisError(f"{repo_relative(manifest_path)} missing tensor shape for role {role!r}")
    role_shape = tensor_shapes[role]
    if (
        not isinstance(role_shape, list)
        or len(role_shape) != 2
        or not all(isinstance(value, int) for value in role_shape)
    ):
        raise SaeFeatureAnalysisError(f"{repo_relative(manifest_path)} invalid tensor shape for role {role!r}")
    return int(role_shape[1])


def feature_rows(codes: np.ndarray, rows: list[dict[str, Any]], feature_index: int, limit: int) -> list[dict[str, Any]]:
    order = np.argsort(-codes[:, feature_index])[:limit]
    examples: list[dict[str, Any]] = []
    for row_index in order:
        row = rows[int(row_index)]
        examples.append(
            {
                "row_key": row["row_key"],
                "label": row["label"],
                "activation": float(codes[int(row_index), feature_index]),
                "question": row.get("question"),
                "strata": row.get("strata", []),
            }
        )
    return examples


def rank_features(codes: np.ndarray, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = np.array([row["label"] for row in rows])
    if set(labels.tolist()) - VALID_LABELS:
        raise SaeFeatureAnalysisError("rows contain labels outside known/unknown")
    known_mask = labels == "known"
    unknown_mask = labels == "unknown"
    ranked: list[dict[str, Any]] = []
    for feature in range(codes.shape[1]):
        values = codes[:, feature]
        known = values[known_mask]
        unknown = values[unknown_mask]
        known_mean = float(np.mean(known))
        unknown_mean = float(np.mean(unknown))
        known_std = float(np.std(known))
        unknown_std = float(np.std(unknown))
        pooled = float(np.sqrt((known_std**2 + unknown_std**2) / 2.0))
        mean_diff = unknown_mean - known_mean
        effect = float(mean_diff / pooled) if pooled > 1e-12 else 0.0
        known_freq = float(np.mean(known > 0.0))
        unknown_freq = float(np.mean(unknown > 0.0))
        freq_diff = unknown_freq - known_freq
        ranked.append(
            {
                "feature": feature,
                "known_mean": known_mean,
                "unknown_mean": unknown_mean,
                "mean_diff_unknown_minus_known": float(mean_diff),
                "abs_mean_diff": float(abs(mean_diff)),
                "cohen_d_unknown_minus_known": effect,
                "abs_cohen_d": float(abs(effect)),
                "known_activation_frequency": known_freq,
                "unknown_activation_frequency": unknown_freq,
                "frequency_diff_unknown_minus_known": float(freq_diff),
                "active_count": int(np.count_nonzero(values > 0.0)),
                "max_activation": float(np.max(values)),
            }
        )
    return sorted(ranked, key=lambda item: (item["abs_cohen_d"], item["abs_mean_diff"]), reverse=True)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_candidate(candidate: dict[str, Any], *, output_root: Path, analysis: dict[str, Any]) -> dict[str, Any]:
    run_dir = resolve_path(candidate["run_dir"])
    manifest = load_json(run_dir / "run_manifest.json")
    source = manifest["candidate"]
    training = manifest["training"]
    extraction_dir = resolve_path(source["extraction_dir"])
    extraction_manifest = resolve_path(source["extraction_manifest"])
    rows = load_selected_rows(run_dir, extraction_dir)
    hidden_dim = hidden_dim_from_manifest(extraction_manifest, str(source["role"]))
    x = load_hidden_matrix(
        {
            "extraction_dir": source["extraction_dir"],
            "role": source["role"],
            "layer": source["layer"],
            "hidden_dim": hidden_dim,
        },
        rows,
    )
    codes = compute_codes(x, run_dir / "sae_weights.safetensors", training)
    ranked = rank_features(codes, rows)
    label = candidate.get("label") or source["label"]
    candidate_out = output_root / label
    top_n = int(analysis.get("top_features", 20))
    top_rows_per_feature = int(analysis.get("top_rows_per_feature", 5))
    feature_csv = candidate_out / "feature_rankings.csv"
    summary_path = candidate_out / "summary.json"
    examples_path = candidate_out / "top_feature_examples.json"

    write_csv(feature_csv, ranked)
    top_features = ranked[:top_n]
    examples = {
        str(item["feature"]): feature_rows(codes, rows, int(item["feature"]), top_rows_per_feature)
        for item in top_features
    }
    write_json(examples_path, {"notice": NOTICE, "top_feature_examples": examples})
    summary = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "candidate_label": label,
        "source_run_manifest": repo_relative(run_dir / "run_manifest.json"),
        "row_count": len(rows),
        "dictionary_size": int(codes.shape[1]),
        "activation": training.get("activation"),
        "top_k": training.get("top_k"),
        "mean_active_features": float(np.mean(np.count_nonzero(codes > 0.0, axis=1))),
        "top_features": top_features,
        "outputs": {
            "feature_rankings": repo_relative(feature_csv),
            "top_feature_examples": repo_relative(examples_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return summary


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    candidates = config.get("candidate_runs")
    analysis = config.get("analysis", {})
    if not isinstance(output, dict) or "root" not in output:
        raise SaeFeatureAnalysisError("config must define output.root")
    if not isinstance(candidates, list) or not candidates:
        raise SaeFeatureAnalysisError("config must define non-empty candidate_runs")
    output_root = resolve_path(output["root"])
    summaries = [run_candidate(candidate, output_root=output_root, analysis=analysis) for candidate in candidates]
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "output_root": repo_relative(output_root),
        "candidate_count": len(summaries),
        "summaries": [summary["outputs"]["summary"] for summary in summaries],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (SaeFeatureAnalysisError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
