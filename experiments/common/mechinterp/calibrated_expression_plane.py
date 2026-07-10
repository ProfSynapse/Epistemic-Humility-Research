#!/usr/bin/env python3
"""Project Phase 3 hidden states onto calibrated-expression behavior planes."""

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
    from safetensors.numpy import load_file as load_numpy_safetensors
except ImportError as exc:  # pragma: no cover
    load_numpy_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None

ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = ROOT / "experiment/phase1/probe"
if str(PROBE_DIR) not in sys.path:
    sys.path.insert(0, str(PROBE_DIR))

from phase3_behavior_axis_scan import (
    BehaviorAxisScanError,
    load_role_cube,
    validate_manifest,
)
from phase3_direction_geometry import resolve_vector_file
from phase3_sae_behavior_feature_analysis import (
    SaeBehaviorFeatureAnalysisError,
    row_matches_filter,
)
from phase3_sae_smoke import (
    SaeSmokeError,
    load_json,
    load_rows,
    repo_relative,
    resolve_path,
    validate_output_root,
)


ANALYSIS_TYPE = "phase3_calibrated_expression_plane"
NOTICE = "CALIBRATED_EXPRESSION_PLANE_ANALYSIS_ONLY"


class CalibratedExpressionPlaneError(RuntimeError):
    pass


def load_config(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CalibratedExpressionPlaneError(f"missing config: {repo_relative(path)}")
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise CalibratedExpressionPlaneError(f"{repo_relative(path)} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def as_list(raw: Any, *, field: str) -> list[Any]:
    if not isinstance(raw, list) or not raw:
        raise CalibratedExpressionPlaneError(f"config must define non-empty {field}")
    return raw


def load_direction_manifest(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        raise CalibratedExpressionPlaneError(f"missing direction manifest: {repo_relative(path)}")
    manifest = load_json(path)
    rows = manifest.get("directions")
    if not isinstance(rows, list) or not rows:
        raise CalibratedExpressionPlaneError(f"{repo_relative(path)} must contain non-empty directions")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise CalibratedExpressionPlaneError(f"{repo_relative(path)} directions must be objects")
        direction_id = row.get("direction_id")
        if not isinstance(direction_id, str) or not direction_id:
            raise CalibratedExpressionPlaneError(f"{repo_relative(path)} direction missing direction_id")
        by_id[direction_id] = row
    return by_id


def load_unit_axis(row: dict[str, Any], *, manifest_path: Path, role: str, layer: int, hidden_dim: int) -> np.ndarray:
    if load_numpy_safetensors is None:
        raise CalibratedExpressionPlaneError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    direction_id = row.get("direction_id")
    axis_role = row.get("role")
    axis_layer = row.get("layer")
    if axis_role != role:
        raise CalibratedExpressionPlaneError(
            f"axis {direction_id!r} role mismatch: expected {role!r}, got {axis_role!r}"
        )
    if not isinstance(axis_layer, int):
        raise CalibratedExpressionPlaneError(f"axis {direction_id!r} missing integer layer")
    if axis_layer != layer:
        raise CalibratedExpressionPlaneError(
            f"axis {direction_id!r} layer mismatch: expected {layer}, got {axis_layer!r}"
        )
    vector_file = row.get("vector_file")
    tensor_key = row.get("tensor_key", "direction")
    if not isinstance(vector_file, str) or not vector_file:
        raise CalibratedExpressionPlaneError(f"axis {direction_id!r} missing vector_file")
    if not isinstance(tensor_key, str) or not tensor_key:
        raise CalibratedExpressionPlaneError(f"axis {direction_id!r} missing tensor_key")
    vector_path = resolve_vector_file(vector_file, manifest_path)
    tensors = load_numpy_safetensors(str(vector_path))
    if tensor_key not in tensors:
        raise CalibratedExpressionPlaneError(f"{repo_relative(vector_path)} missing tensor key {tensor_key!r}")
    vector = np.asarray(tensors[tensor_key], dtype=np.float32)
    if vector.ndim != 1 or vector.shape[0] != hidden_dim:
        raise CalibratedExpressionPlaneError(
            f"axis {direction_id!r} hidden dim mismatch: expected ({hidden_dim},), got {tuple(vector.shape)}"
        )
    norm = float(np.linalg.norm(vector.astype(np.float64)))
    if norm <= 1e-12:
        raise CalibratedExpressionPlaneError(f"axis {direction_id!r} has zero norm")
    return (vector / norm).astype(np.float32)


def row_passes_filter(row: dict[str, Any], *, arm: str, row_filter: dict[str, Any] | None) -> bool:
    if row_filter is None:
        return True
    return row_matches_filter(row, arm, row_filter)


def behavior_cell(row: dict[str, Any], *, arm: str, cells: list[dict[str, Any]], fallback: str) -> str:
    for cell in cells:
        label = cell.get("label")
        row_filter = cell.get("filter")
        if not isinstance(label, str) or not label:
            raise CalibratedExpressionPlaneError("each behavior cell must define label")
        if not isinstance(row_filter, dict):
            raise CalibratedExpressionPlaneError(f"behavior cell {label!r} must define filter")
        if row_matches_filter(row, arm, row_filter):
            return label
    return fallback


def parse_extraction(config: dict[str, Any]) -> dict[str, Any]:
    extraction = config.get("extraction")
    if not isinstance(extraction, dict):
        raise CalibratedExpressionPlaneError("config must define extraction")
    for field in ("extraction_dir", "role", "behavior_arm"):
        if not isinstance(extraction.get(field), str) or not extraction[field]:
            raise CalibratedExpressionPlaneError(f"config extraction must define {field}")
    return extraction


def parse_behavior_cells(config: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    grouping = config.get("behavior_cells")
    if not isinstance(grouping, dict):
        raise CalibratedExpressionPlaneError("config must define behavior_cells")
    cells = as_list(grouping.get("cells"), field="behavior_cells.cells")
    for cell in cells:
        if not isinstance(cell, dict):
            raise CalibratedExpressionPlaneError("behavior_cells.cells entries must be mappings")
    fallback = grouping.get("fallback_cell", "unmatched")
    if not isinstance(fallback, str) or not fallback:
        raise CalibratedExpressionPlaneError("behavior_cells.fallback_cell must be a non-empty string")
    return cells, fallback


def parse_planes(config: dict[str, Any]) -> list[dict[str, Any]]:
    raw_planes = as_list(config.get("planes"), field="planes")
    planes: list[dict[str, Any]] = []
    for plane in raw_planes:
        if not isinstance(plane, dict):
            raise CalibratedExpressionPlaneError("planes entries must be mappings")
        for field in ("layer", "x_direction_id", "y_direction_id"):
            if field not in plane:
                raise CalibratedExpressionPlaneError(f"plane missing {field}")
        if not isinstance(plane["layer"], int):
            raise CalibratedExpressionPlaneError("plane layer must be an integer")
        planes.append(plane)
    return planes


def selected_rows(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    row_filter: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    out = [row for row in rows if row_passes_filter(row, arm=arm, row_filter=row_filter)]
    if not out:
        raise CalibratedExpressionPlaneError("row selection matched no rows")
    return out


def arm_fields(row: dict[str, Any], arm: str) -> dict[str, Any]:
    source_arms = row.get("source_arms")
    payload = source_arms.get(arm) if isinstance(source_arms, dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    return {
        "refused": payload.get("refused", ""),
        "correct": payload.get("correct", ""),
        "truthful": payload.get("truthful", ""),
        "stated_confidence": payload.get("stated_confidence", ""),
    }


def projection_rows(
    *,
    rows: list[dict[str, Any]],
    cube: np.ndarray,
    planes: list[dict[str, Any]],
    axes_by_id: dict[str, dict[str, Any]],
    direction_manifest_path: Path,
    role: str,
    hidden_dim: int,
    behavior_arm: str,
    behavior_cells: list[dict[str, Any]],
    fallback_cell: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for plane in planes:
        layer = int(plane["layer"])
        if layer < 0 or layer >= cube.shape[1]:
            raise CalibratedExpressionPlaneError(f"plane layer {layer} outside layer count {cube.shape[1]}")
        x_id = str(plane["x_direction_id"])
        y_id = str(plane["y_direction_id"])
        if x_id not in axes_by_id:
            raise CalibratedExpressionPlaneError(f"missing x axis direction {x_id!r}")
        if y_id not in axes_by_id:
            raise CalibratedExpressionPlaneError(f"missing y axis direction {y_id!r}")
        x_axis = load_unit_axis(
            axes_by_id[x_id],
            manifest_path=direction_manifest_path,
            role=role,
            layer=layer,
            hidden_dim=hidden_dim,
        )
        y_axis = load_unit_axis(
            axes_by_id[y_id],
            manifest_path=direction_manifest_path,
            role=role,
            layer=layer,
            hidden_dim=hidden_dim,
        )
        axis_cosine = float(np.dot(x_axis, y_axis))
        for row_index, row in enumerate(rows):
            vector = cube[row_index, layer, :]
            out.append(
                {
                    "analysis_type": ANALYSIS_TYPE,
                    "notice": NOTICE,
                    "row_index": row_index,
                    "row_key": row["row_key"],
                    "label": row.get("label", ""),
                    "behavior_cell": behavior_cell(
                        row,
                        arm=behavior_arm,
                        cells=behavior_cells,
                        fallback=fallback_cell,
                    ),
                    "role": role,
                    "layer": layer,
                    "x_direction_id": x_id,
                    "y_direction_id": y_id,
                    "axis_cosine": axis_cosine,
                    "x_projection": float(np.dot(vector, x_axis)),
                    "y_projection": float(np.dot(vector, y_axis)),
                    "activation_norm": float(np.linalg.norm(vector.astype(np.float64))),
                    **arm_fields(row, behavior_arm),
                }
            )
    return out


def summarize_plane_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (int(row["layer"]), str(row["behavior_cell"]))
        grouped.setdefault(key, []).append(row)
    out: list[dict[str, Any]] = []
    for (layer, cell), cell_rows in sorted(grouped.items()):
        x = np.asarray([float(row["x_projection"]) for row in cell_rows], dtype=np.float64)
        y = np.asarray([float(row["y_projection"]) for row in cell_rows], dtype=np.float64)
        out.append(
            {
                "analysis_type": ANALYSIS_TYPE,
                "notice": NOTICE,
                "layer": layer,
                "behavior_cell": cell,
                "row_count": len(cell_rows),
                "x_projection_mean": float(np.mean(x)),
                "y_projection_mean": float(np.mean(y)),
                "x_projection_std": float(np.std(x)),
                "y_projection_std": float(np.std(y)),
                "x_projection_min": float(np.min(x)),
                "x_projection_max": float(np.max(x)),
                "y_projection_min": float(np.min(y)),
                "y_projection_max": float(np.max(y)),
            }
        )
    return out


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row[key])
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    extraction = parse_extraction(config)
    direction_manifest = config.get("direction_manifest")
    output = config.get("output")
    if not isinstance(direction_manifest, str) or not direction_manifest:
        raise CalibratedExpressionPlaneError("config must define direction_manifest")
    if not isinstance(output, dict) or not output.get("root"):
        raise CalibratedExpressionPlaneError("config must define output.root")

    role = extraction["role"]
    behavior_arm = extraction["behavior_arm"]
    extraction_dir = resolve_path(extraction["extraction_dir"])
    extraction_manifest = resolve_path(extraction.get("extraction_manifest", extraction_dir / "manifest.json"))
    direction_manifest_path = resolve_path(direction_manifest)
    output_root = resolve_path(output["root"])
    validate_output_root(output_root, [extraction_dir])

    planes = parse_planes(config)
    manifest = validate_manifest(extraction_manifest, roles=[role])
    layer_count, hidden_dim = manifest["tensor_shapes"][role]
    for plane in planes:
        layer = int(plane["layer"])
        if layer < 0 or layer >= layer_count:
            raise CalibratedExpressionPlaneError(f"plane layer {layer} outside layer count {layer_count}")

    rows = load_rows(extraction_dir)
    row_filter = config.get("row_filter")
    if row_filter is not None and not isinstance(row_filter, dict):
        raise CalibratedExpressionPlaneError("row_filter must be a mapping")
    rows = selected_rows(rows, arm=behavior_arm, row_filter=row_filter)
    cells, fallback_cell = parse_behavior_cells(config)
    axes_by_id = load_direction_manifest(direction_manifest_path)
    cube = load_role_cube(extraction_dir, rows, role=role, layer_count=layer_count, hidden_dim=hidden_dim)

    plane_rows = projection_rows(
        rows=rows,
        cube=cube,
        planes=planes,
        axes_by_id=axes_by_id,
        direction_manifest_path=direction_manifest_path,
        role=role,
        hidden_dim=hidden_dim,
        behavior_arm=behavior_arm,
        behavior_cells=cells,
        fallback_cell=fallback_cell,
    )
    summary_rows = summarize_plane_rows(plane_rows)

    plane_rows_path = output_root / "plane_rows.csv"
    plane_summary_path = output_root / "plane_summary.csv"
    summary_path = output_root / "summary.json"
    write_csv(plane_rows_path, plane_rows)
    write_csv(plane_summary_path, summary_rows)
    summary_payload = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "extraction_dir": repo_relative(extraction_dir),
        "extraction_manifest": repo_relative(extraction_manifest),
        "direction_manifest": repo_relative(direction_manifest_path),
        "output_root": repo_relative(output_root),
        "role": role,
        "behavior_arm": behavior_arm,
        "source_row_count": len(rows),
        "plane_count": len(planes),
        "projection_row_count": len(plane_rows),
        "counts_by_layer": count_by(plane_rows, "layer"),
        "counts_by_behavior_cell": count_by(plane_rows, "behavior_cell"),
        "outputs": {
            "plane_rows": repo_relative(plane_rows_path),
            "plane_summary": repo_relative(plane_summary_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary_payload)
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "projection_row_count": len(plane_rows),
        "output_root": repo_relative(output_root),
        "summary": repo_relative(summary_path),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (
        CalibratedExpressionPlaneError,
        BehaviorAxisScanError,
        SaeBehaviorFeatureAnalysisError,
        SaeSmokeError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
