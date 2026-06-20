#!/usr/bin/env python3
"""Export transformed Phase 3 direction candidates from existing manifests."""

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


NOTICE = "DIRECTION_TRANSFORM_CANDIDATES_ONLY"
ANALYSIS_TYPE = "phase3_direction_transform_export"
TENSOR_KEY = "direction"


class DirectionTransformError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise DirectionTransformError(f"{repo_relative(path)} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise DirectionTransformError(f"{repo_relative(path)} did not load to a YAML object")
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


def resolve_vector_file(raw_path: str, manifest_path: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    repo_candidate = resolve_path(raw_path)
    if repo_candidate.exists():
        return repo_candidate
    return manifest_path.parent / path


def load_source_manifest(path: Path) -> dict[str, dict[str, Any]]:
    manifest = load_json(path)
    rows = manifest.get("directions")
    if not isinstance(rows, list) or not rows:
        raise DirectionTransformError("source_manifest must contain non-empty directions")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise DirectionTransformError("source_manifest directions must be objects")
        direction_id = row.get("direction_id")
        if not isinstance(direction_id, str) or not direction_id:
            raise DirectionTransformError("source direction missing direction_id")
        if direction_id in by_id:
            raise DirectionTransformError(f"duplicate source direction_id {direction_id!r}")
        by_id[direction_id] = row
    return by_id


def load_vector(row: dict[str, Any], manifest_path: Path) -> np.ndarray:
    if load_numpy_safetensors is None:
        raise DirectionTransformError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    vector_file = row.get("vector_file")
    tensor_key = row.get("tensor_key", TENSOR_KEY)
    if not isinstance(vector_file, str) or not vector_file:
        raise DirectionTransformError(f"source direction {row.get('direction_id')} missing vector_file")
    if not isinstance(tensor_key, str) or not tensor_key:
        raise DirectionTransformError(f"source direction {row.get('direction_id')} missing tensor_key")
    tensors = load_numpy_safetensors(str(resolve_vector_file(vector_file, manifest_path)))
    if tensor_key not in tensors:
        raise DirectionTransformError(f"{vector_file} missing tensor key {tensor_key!r}")
    vector = np.asarray(tensors[tensor_key], dtype=np.float32)
    if vector.ndim != 1:
        raise DirectionTransformError(f"{vector_file}:{tensor_key} must be a 1D vector")
    return vector


def transform_vector(vector: np.ndarray, spec: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    method = str(spec.get("method", "unit_rescale_to_norm"))
    source_norm = float(np.linalg.norm(vector))
    if source_norm <= 0.0:
        raise DirectionTransformError("cannot transform zero-norm source vector")
    if method == "unit_rescale_to_norm":
        target_norm = float(spec["target_norm"])
        if target_norm <= 0.0:
            raise DirectionTransformError("target_norm must be positive")
        transformed = (vector / source_norm * target_norm).astype(np.float32)
        return transformed, {
            "transform_method": method,
            "source_norm": source_norm,
            "target_norm": target_norm,
            "scale_factor": target_norm / source_norm,
        }
    if method == "multiply":
        scale_factor = float(spec["scale_factor"])
        transformed = (vector * scale_factor).astype(np.float32)
        return transformed, {
            "transform_method": method,
            "source_norm": source_norm,
            "target_norm": float(np.linalg.norm(transformed)),
            "scale_factor": scale_factor,
        }
    if method == "identity":
        transformed = vector.astype(np.float32)
        return transformed, {
            "transform_method": method,
            "source_norm": source_norm,
            "target_norm": source_norm,
            "scale_factor": 1.0,
        }
    raise DirectionTransformError("transform method must be unit_rescale_to_norm, multiply, or identity")


def build_record(
    transform: dict[str, Any],
    *,
    source_by_id: dict[str, dict[str, Any]],
    source_manifest_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    label = transform.get("label")
    source_id = transform.get("source_direction_id")
    if not isinstance(label, str) or not label:
        raise DirectionTransformError("each transform must define non-empty label")
    if not isinstance(source_id, str) or not source_id:
        raise DirectionTransformError(f"transform {label!r} must define source_direction_id")
    if source_id not in source_by_id:
        raise DirectionTransformError(f"transform {label!r} source_direction_id {source_id!r} not found")

    source_row = source_by_id[source_id]
    vector = load_vector(source_row, source_manifest_path)
    transformed, metadata = transform_vector(vector, transform)
    sha = vector_sha256(transformed)
    direction_id = f"direction_transform__{safe_label(label)}__{sha[:12]}"
    vector_path = output_root / safe_label(label) / "directions" / f"{direction_id}.safetensors"
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    if save_numpy_safetensors is None:
        raise DirectionTransformError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    save_numpy_safetensors({TENSOR_KEY: transformed}, str(vector_path))

    record = {
        "direction_id": direction_id,
        "candidate_label": label,
        "status": "ok",
        "role": source_row.get("role"),
        "layer": int(source_row["layer"]),
        "hidden_dim": int(transformed.shape[0]),
        "norm": float(np.linalg.norm(transformed)),
        "vector_sha256": sha,
        "tensor_key": TENSOR_KEY,
        "vector_file": repo_relative(vector_path),
        "notice": NOTICE,
        "analysis_type": ANALYSIS_TYPE,
        "method": "direction_transform",
        "source_method": source_row.get("method"),
        "source_contrast": source_row.get("contrast"),
        "contrast": transform.get("contrast", source_row.get("contrast")),
        "positive_label": source_row.get("positive_label"),
        "negative_label": source_row.get("negative_label"),
        "source_direction_id": source_id,
        "source_direction_manifest": repo_relative(source_manifest_path),
        "source_vector_sha256": source_row.get("vector_sha256"),
        **metadata,
    }
    extra = transform.get("metadata", {})
    if extra is not None:
        if not isinstance(extra, dict):
            raise DirectionTransformError(f"transform {label!r} metadata must be a mapping")
        record.update(extra)
    return record


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    source_manifest = config.get("source_manifest")
    output = config.get("output")
    transforms = config.get("transforms")
    if not isinstance(source_manifest, str) or not source_manifest:
        raise DirectionTransformError("config must define source_manifest")
    if not isinstance(output, dict) or not output.get("root"):
        raise DirectionTransformError("config must define output.root")
    if not isinstance(transforms, list) or not transforms:
        raise DirectionTransformError("config must define non-empty transforms")

    source_manifest_path = resolve_path(source_manifest)
    output_root = resolve_path(output["root"])
    source_by_id = load_source_manifest(source_manifest_path)
    records = [
        build_record(
            transform,
            source_by_id=source_by_id,
            source_manifest_path=source_manifest_path,
            output_root=output_root,
        )
        for transform in transforms
    ]
    csv_path = output_root / "direction_transforms.csv"
    manifest_path = output_root / "direction_transforms.manifest.json"
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
    except DirectionTransformError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
