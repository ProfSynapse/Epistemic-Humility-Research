#!/usr/bin/env python3
"""Build composite SAE-feature directions from exported feature directions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from phase3_sae_smoke import repo_relative, resolve_path

try:
    from safetensors.numpy import load_file as load_numpy_safetensors
    from safetensors.numpy import save_file as save_numpy_safetensors
except ImportError as exc:  # pragma: no cover
    load_numpy_safetensors = None
    save_numpy_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None


NOTICE = "SAE_FEATURE_COMPOSITE_DIRECTION_CANDIDATES_ONLY"
ANALYSIS_TYPE = "phase3_sae_feature_composite_direction_export"
TENSOR_KEY = "direction"


class SaeFeatureCompositeError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureCompositeError(f"{repo_relative(path)} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureCompositeError(f"{repo_relative(path)} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def vector_sha256(vector: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(vector.astype(np.float32))
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def safe_label(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def load_source_directions(manifest_path: Path) -> dict[str, dict[str, Any]]:
    manifest = load_json(manifest_path)
    rows = manifest.get("directions")
    if not isinstance(rows, list) or not rows:
        raise SaeFeatureCompositeError("source_manifest must contain non-empty directions")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise SaeFeatureCompositeError("source_manifest directions must be objects")
        direction_id = row.get("direction_id")
        if not isinstance(direction_id, str) or not direction_id:
            raise SaeFeatureCompositeError("source direction missing direction_id")
        if direction_id in by_id:
            raise SaeFeatureCompositeError(f"duplicate source direction_id {direction_id!r}")
        by_id[direction_id] = row
    return by_id


def load_vector(row: dict[str, Any]) -> np.ndarray:
    if load_numpy_safetensors is None:
        raise SaeFeatureCompositeError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    vector_file = row.get("vector_file")
    tensor_key = row.get("tensor_key", TENSOR_KEY)
    if not isinstance(vector_file, str) or not vector_file:
        raise SaeFeatureCompositeError(f"source direction {row.get('direction_id')} missing vector_file")
    if not isinstance(tensor_key, str) or not tensor_key:
        raise SaeFeatureCompositeError(f"source direction {row.get('direction_id')} missing tensor_key")
    tensors = load_numpy_safetensors(str(resolve_path(vector_file)))
    if tensor_key not in tensors:
        raise SaeFeatureCompositeError(f"{vector_file} missing tensor key {tensor_key!r}")
    vector = np.asarray(tensors[tensor_key], dtype=np.float32)
    if vector.ndim != 1:
        raise SaeFeatureCompositeError(f"{vector_file}:{tensor_key} must be a 1D vector")
    return vector


def normalized(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise SaeFeatureCompositeError("cannot normalize zero-norm source vector")
    return (vector / norm).astype(np.float32)


def build_composite_vector(
    sources: list[tuple[dict[str, Any], np.ndarray, float]],
    *,
    combine: str,
    rescale: str,
) -> tuple[np.ndarray, dict[str, Any]]:
    if combine not in {"raw_weighted_mean", "unit_weighted_mean"}:
        raise SaeFeatureCompositeError("composite.combine must be raw_weighted_mean or unit_weighted_mean")
    if rescale not in {"none", "mean_source_norm", "sum_abs_weighted_source_norm"}:
        raise SaeFeatureCompositeError(
            "composite.rescale must be none, mean_source_norm, or sum_abs_weighted_source_norm"
        )

    vectors = []
    source_norms = []
    abs_weights = []
    for _row, vector, weight in sources:
        source_norms.append(float(np.linalg.norm(vector)))
        abs_weights.append(abs(float(weight)))
        base = normalized(vector) if combine == "unit_weighted_mean" else vector
        vectors.append(base * float(weight))
    combined = np.sum(np.stack(vectors, axis=0), axis=0).astype(np.float32)
    if len(vectors) > 1:
        combined = (combined / float(len(vectors))).astype(np.float32)

    pre_rescale_norm = float(np.linalg.norm(combined))
    if pre_rescale_norm <= 0.0:
        raise SaeFeatureCompositeError("composite vector has zero norm")
    scale_factor = 1.0
    if rescale == "mean_source_norm":
        scale_factor = float(np.mean(source_norms)) / pre_rescale_norm
    elif rescale == "sum_abs_weighted_source_norm":
        scale_factor = float(np.sum(np.asarray(source_norms) * np.asarray(abs_weights))) / pre_rescale_norm
    vector = (combined * scale_factor).astype(np.float32)
    return vector, {
        "combine": combine,
        "rescale": rescale,
        "pre_rescale_norm": pre_rescale_norm,
        "scale_factor": scale_factor,
        "source_norm_mean": float(np.mean(source_norms)),
    }


def validate_sources(rows: list[dict[str, Any]]) -> tuple[int, str]:
    layers = {int(row["layer"]) for row in rows}
    roles = {str(row["role"]) for row in rows}
    hidden_dims = {int(row["hidden_dim"]) for row in rows}
    if len(layers) != 1:
        raise SaeFeatureCompositeError(f"composite sources must share one layer; found {sorted(layers)}")
    if len(roles) != 1:
        raise SaeFeatureCompositeError(f"composite sources must share one role; found {sorted(roles)}")
    if len(hidden_dims) != 1:
        raise SaeFeatureCompositeError(f"composite sources must share hidden_dim; found {sorted(hidden_dims)}")
    return next(iter(layers)), next(iter(roles))


def build_composite(
    composite: dict[str, Any],
    *,
    source_by_id: dict[str, dict[str, Any]],
    output_root: Path,
) -> dict[str, Any]:
    label = composite.get("label")
    source_ids = composite.get("source_direction_ids")
    if not isinstance(label, str) or not label:
        raise SaeFeatureCompositeError("each composite must define non-empty label")
    if not isinstance(source_ids, list) or not source_ids:
        raise SaeFeatureCompositeError(f"composite {label!r} must define source_direction_ids")
    if not all(isinstance(source_id, str) and source_id for source_id in source_ids):
        raise SaeFeatureCompositeError(f"composite {label!r} source_direction_ids must be non-empty strings")
    if len(set(source_ids)) != len(source_ids):
        raise SaeFeatureCompositeError(f"composite {label!r} source_direction_ids must not contain duplicates")
    raw_weights = composite.get("weights", [1.0] * len(source_ids))
    if not isinstance(raw_weights, list) or len(raw_weights) != len(source_ids):
        raise SaeFeatureCompositeError(f"composite {label!r} weights must match source_direction_ids length")
    weights = [float(weight) for weight in raw_weights]

    missing = [source_id for source_id in source_ids if source_id not in source_by_id]
    if missing:
        raise SaeFeatureCompositeError(f"composite {label!r} missing source_direction_ids {missing}")
    source_rows = [source_by_id[source_id] for source_id in source_ids]
    layer, role = validate_sources(source_rows)
    vector_sources = [(row, load_vector(row), weight) for row, weight in zip(source_rows, weights)]
    vector, method = build_composite_vector(
        vector_sources,
        combine=str(composite.get("combine", "unit_weighted_mean")),
        rescale=str(composite.get("rescale", "mean_source_norm")),
    )
    sha = vector_sha256(vector)
    direction_id = f"sae_feature_composite__{safe_label(label)}__{sha[:12]}"
    vector_path = output_root / safe_label(label) / "directions" / f"{direction_id}.safetensors"
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    if save_numpy_safetensors is None:
        raise SaeFeatureCompositeError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    save_numpy_safetensors({TENSOR_KEY: vector}, str(vector_path))

    source_features = [int(row["feature"]) for row in source_rows if "feature" in row]
    record = {
        "direction_id": direction_id,
        "candidate_label": label,
        "status": "ok",
        "role": role,
        "layer": layer,
        "hidden_dim": int(vector.shape[0]),
        "norm": float(np.linalg.norm(vector)),
        "vector_sha256": sha,
        "tensor_key": TENSOR_KEY,
        "vector_file": repo_relative(vector_path),
        "notice": NOTICE,
        "analysis_type": ANALYSIS_TYPE,
        "method": "sae_feature_composite_direction",
        "direction_space": "raw_hidden_composite_of_sae_feature_directions",
        "source_direction_ids": source_ids,
        "source_features": source_features,
        "weights": weights,
        "combine": method["combine"],
        "rescale": method["rescale"],
        "pre_rescale_norm": method["pre_rescale_norm"],
        "scale_factor": method["scale_factor"],
        "source_norm_mean": method["source_norm_mean"],
        "feature_skew_label": composite.get("feature_skew_label", "mixed"),
        "source_candidate_labels": sorted({str(row["candidate_label"]) for row in source_rows}),
    }
    return record


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    source_manifest = config.get("source_manifest")
    output = config.get("output")
    composites = config.get("composites")
    if not isinstance(source_manifest, str) or not source_manifest:
        raise SaeFeatureCompositeError("config must define source_manifest")
    if not isinstance(output, dict) or "root" not in output:
        raise SaeFeatureCompositeError("config must define output.root")
    if not isinstance(composites, list) or not composites:
        raise SaeFeatureCompositeError("config must define non-empty composites")

    source_manifest_path = resolve_path(source_manifest)
    output_root = resolve_path(output["root"])
    source_by_id = load_source_directions(source_manifest_path)
    records = [
        build_composite(composite, source_by_id=source_by_id, output_root=output_root)
        for composite in composites
    ]
    csv_path = output_root / "sae_feature_composite_directions.csv"
    manifest_path = output_root / "sae_feature_composite_directions.manifest.json"
    write_csv(csv_path, records)
    write_json(
        manifest_path,
        {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "config": repo_relative(config_path),
            "source_manifest": repo_relative(source_manifest_path),
            "output_root": repo_relative(output_root),
            "direction_count": len(records),
            "directions": records,
        },
    )
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "output_root": repo_relative(output_root),
        "direction_count": len(records),
        "manifest": repo_relative(manifest_path),
        "csv": repo_relative(csv_path),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except SaeFeatureCompositeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
