#!/usr/bin/env python3
"""Export behavior-axis direction candidates from hidden-state extractions."""

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

try:
    from safetensors.numpy import save_file as save_safetensors
except ImportError as exc:  # pragma: no cover
    save_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_behavior_axis_scan import (
    ANALYSIS_TYPE as SCAN_ANALYSIS_TYPE,
    BehaviorAxisScanError,
    contrast_masks,
    load_extraction_rows,
    load_role_cube,
    scan_layer,
    validate_manifest,
)
from sae_smoke import (
    SaeSmokeError,
    repo_relative,
    resolve_path,
    validate_output_root,
)


ANALYSIS_TYPE = "phase3_behavior_axis_direction_export"
NOTICE = "BEHAVIOR_AXIS_DIRECTION_CANDIDATES_ONLY"
TENSOR_KEY = "direction"


class BehaviorAxisDirectionError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise BehaviorAxisDirectionError(f"{repo_relative(path)} did not load to a YAML object")
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
    return hashlib.sha256(np.ascontiguousarray(vector.astype(np.float32)).tobytes()).hexdigest()


def safe_label(text: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")
    if not safe:
        raise BehaviorAxisDirectionError("label did not contain any safe path characters")
    return safe


def load_scan_config(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    config = load_config(path)
    extractions = config.get("extractions")
    analysis = config.get("analysis", {})
    if not isinstance(extractions, list) or not extractions:
        raise BehaviorAxisDirectionError("source scan config must define non-empty extractions")
    if not isinstance(analysis, dict):
        analysis = {}
    extraction_by_label: dict[str, dict[str, Any]] = {}
    contrast_by_name: dict[str, dict[str, Any]] = {}
    for extraction in extractions:
        label = extraction.get("label")
        if not isinstance(label, str) or not label:
            raise BehaviorAxisDirectionError("source scan extraction missing label")
        extraction_by_label[label] = extraction
        for contrast in extraction.get("contrasts", analysis.get("contrasts", [])):
            name = contrast.get("name") if isinstance(contrast, dict) else None
            if isinstance(name, str) and name:
                contrast_by_name[name] = contrast
    return extraction_by_label, contrast_by_name


def transform_direction(raw_direction: np.ndarray, spec: dict[str, Any]) -> tuple[np.ndarray, dict[str, Any]]:
    raw_norm = float(np.linalg.norm(raw_direction.astype(np.float64)))
    if raw_norm <= 1e-12:
        raise BehaviorAxisDirectionError("cannot export zero-norm behavior axis")
    method = str(spec.get("transform_method", "unit_rescale_to_norm"))
    if method == "unit_rescale_to_norm":
        target_norm = float(spec["target_norm"])
        if target_norm <= 0.0:
            raise BehaviorAxisDirectionError("target_norm must be positive")
        vector = (raw_direction / raw_norm * target_norm).astype(np.float32)
        return vector, {
            "transform_method": method,
            "source_norm": raw_norm,
            "target_norm": target_norm,
            "scale_factor": target_norm / raw_norm,
        }
    if method == "identity":
        return raw_direction.astype(np.float32), {
            "transform_method": method,
            "source_norm": raw_norm,
            "target_norm": raw_norm,
            "scale_factor": 1.0,
        }
    raise BehaviorAxisDirectionError("transform_method must be unit_rescale_to_norm or identity")


def mean_difference_direction(matrix: np.ndarray, positive_mask: np.ndarray, negative_mask: np.ndarray) -> np.ndarray:
    positive_mean = np.mean(matrix[positive_mask], axis=0)
    negative_mean = np.mean(matrix[negative_mask], axis=0)
    return np.asarray(positive_mean - negative_mean, dtype=np.float32)


def build_axis_record(
    axis: dict[str, Any],
    *,
    extraction_by_label: dict[str, dict[str, Any]],
    contrast_by_name: dict[str, dict[str, Any]],
    output_root: Path,
    source_scan_config: Path,
) -> dict[str, Any]:
    label = axis.get("label")
    extraction_label = axis.get("extraction_label")
    contrast_name = axis.get("contrast")
    role = axis.get("role")
    if not isinstance(label, str) or not label:
        raise BehaviorAxisDirectionError("each axis must define non-empty label")
    if not isinstance(extraction_label, str) or extraction_label not in extraction_by_label:
        raise BehaviorAxisDirectionError(f"axis {label!r} has unknown extraction_label {extraction_label!r}")
    if not isinstance(contrast_name, str) or contrast_name not in contrast_by_name:
        raise BehaviorAxisDirectionError(f"axis {label!r} has unknown contrast {contrast_name!r}")
    if not isinstance(role, str) or not role:
        raise BehaviorAxisDirectionError(f"axis {label!r} must define role")
    layer = int(axis["layer"])
    extraction = extraction_by_label[extraction_label]
    contrast = contrast_by_name[contrast_name]
    behavior_arm = axis.get("behavior_arm", extraction.get("behavior_arm"))
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise BehaviorAxisDirectionError(f"axis {label!r} must define behavior_arm")

    extraction_dir = resolve_path(extraction["extraction_dir"])
    extraction_manifest = resolve_path(extraction.get("extraction_manifest", extraction_dir / "manifest.json"))
    manifest = validate_manifest(extraction_manifest, roles=[role])
    layer_count, hidden_dim = manifest["tensor_shapes"][role]
    if layer < 0 or layer >= layer_count:
        raise BehaviorAxisDirectionError(f"axis {label!r} layer {layer} outside layer count {layer_count}")
    override_rows_path = extraction.get("rows_path")
    rows_path = resolve_path(override_rows_path) if override_rows_path else None
    rows = load_extraction_rows(extraction_dir, rows_path=rows_path)
    positive_mask, negative_mask = contrast_masks(rows, arm=behavior_arm, contrast=contrast)
    min_rows = int(axis.get("min_rows_per_group", contrast.get("min_rows_per_group", 1)))
    positive_count = int(np.count_nonzero(positive_mask))
    negative_count = int(np.count_nonzero(negative_mask))
    if positive_count < min_rows or negative_count < min_rows:
        raise BehaviorAxisDirectionError(
            f"axis {label!r} insufficient rows for {contrast_name}: "
            f"positive={positive_count}, negative={negative_count}, min={min_rows}"
        )

    cube = load_role_cube(extraction_dir, rows, role=role, layer_count=layer_count, hidden_dim=hidden_dim)
    matrix = cube[:, layer, :]
    raw_direction = mean_difference_direction(matrix, positive_mask, negative_mask)
    metrics, _unit_direction = scan_layer(matrix, positive_mask=positive_mask, negative_mask=negative_mask)
    vector, transform_metadata = transform_direction(raw_direction, axis)
    sha = vector_sha256(vector)
    direction_id = f"behavior_axis__{safe_label(label)}__{sha[:12]}"
    vector_path = output_root / safe_label(label) / "directions" / f"{direction_id}.safetensors"
    vector_path.parent.mkdir(parents=True, exist_ok=True)
    if save_safetensors is None:
        raise BehaviorAxisDirectionError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    save_safetensors({TENSOR_KEY: vector}, str(vector_path))

    record = {
        "direction_id": direction_id,
        "candidate_label": label,
        "status": "ok",
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "source_analysis_type": SCAN_ANALYSIS_TYPE,
        "source_scan_config": repo_relative(source_scan_config),
        "extraction_label": extraction_label,
        "behavior_arm": behavior_arm,
        "arm": axis.get("arm", behavior_arm),
        "role": role,
        "layer": layer,
        "hidden_dim": int(vector.shape[0]),
        "method": "behavior_axis_mean_difference",
        "contrast": contrast_name,
        "positive_label": contrast.get("positive_label", "positive"),
        "negative_label": contrast.get("negative_label", "negative"),
        "positive_count": positive_count,
        "negative_count": negative_count,
        "n_total": len(rows),
        "tensor_key": TENSOR_KEY,
        "vector_file": repo_relative(vector_path),
        "vector_sha256": sha,
        "norm": float(np.linalg.norm(vector.astype(np.float64))),
        "source_extraction_dir": repo_relative(extraction_dir),
        "source_extraction_manifest": repo_relative(extraction_manifest),
        "source_rows_path": repo_relative(rows_path) if rows_path is not None else repo_relative(extraction_dir / "rows.jsonl"),
        **transform_metadata,
        **metrics,
    }
    metadata = axis.get("metadata", {})
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise BehaviorAxisDirectionError(f"axis {label!r} metadata must be a mapping")
        record.update(metadata)
    return record


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    source_scan_config = config.get("source_scan_config")
    axes = config.get("axes")
    output = config.get("output")
    if not isinstance(source_scan_config, str) or not source_scan_config:
        raise BehaviorAxisDirectionError("config must define source_scan_config")
    if not isinstance(axes, list) or not axes:
        raise BehaviorAxisDirectionError("config must define non-empty axes")
    if not isinstance(output, dict) or not output.get("root"):
        raise BehaviorAxisDirectionError("config must define output.root")

    source_scan_config_path = resolve_path(source_scan_config)
    output_root = resolve_path(output["root"])
    extraction_by_label, contrast_by_name = load_scan_config(source_scan_config_path)
    extraction_dirs = [
        resolve_path(extraction["extraction_dir"])
        for extraction in extraction_by_label.values()
    ]
    validate_output_root(output_root, extraction_dirs)

    records = [
        build_axis_record(
            axis,
            extraction_by_label=extraction_by_label,
            contrast_by_name=contrast_by_name,
            output_root=output_root,
            source_scan_config=source_scan_config_path,
        )
        for axis in axes
    ]
    csv_path = output_root / "behavior_axis_directions.csv"
    manifest_path = output_root / "behavior_axis_directions.manifest.json"
    write_csv(csv_path, records)
    write_json(
        manifest_path,
        {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "config": repo_relative(config_path),
            "source_scan_config": repo_relative(source_scan_config_path),
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
        "csv": repo_relative(csv_path),
        "manifest": repo_relative(manifest_path),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (BehaviorAxisDirectionError, BehaviorAxisScanError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
