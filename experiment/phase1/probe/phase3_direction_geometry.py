#!/usr/bin/env python3
"""Map cosine geometry across Phase 3 direction candidate sets."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from phase3_sae_smoke import repo_relative, resolve_path

try:
    from safetensors.numpy import load_file as load_numpy_safetensors
except ImportError as exc:  # pragma: no cover
    load_numpy_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None


NOTICE = "DIRECTION_GEOMETRY_ANALYSIS_ONLY"
ANALYSIS_TYPE = "phase3_direction_geometry"


class DirectionGeometryError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise DirectionGeometryError(f"{repo_relative(path)} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise DirectionGeometryError(f"{repo_relative(path)} did not load to a YAML object")
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


def as_allowed_set(spec: dict[str, Any], singular: str, plural: str) -> set[Any] | None:
    if plural in spec:
        raw = spec[plural]
    elif singular in spec:
        raw = [spec[singular]]
    else:
        return None
    if not isinstance(raw, list):
        raw = [raw]
    return set(raw)


def row_matches_spec(row: dict[str, Any], spec: dict[str, Any]) -> bool:
    direction_ids = as_allowed_set(spec, "direction_id", "include_direction_ids")
    if direction_ids is not None and row.get("direction_id") not in direction_ids:
        return False

    filters = spec.get("filters", {})
    if filters is None:
        filters = {}
    if not isinstance(filters, dict):
        raise DirectionGeometryError("direction set filters must be a mapping")

    fields = {
        "role": ("role", "roles"),
        "layer": ("layer", "layers"),
        "feature": ("feature", "features"),
        "candidate_label": ("candidate_label", "candidate_labels"),
        "feature_skew_label": ("feature_skew_label", "feature_skew_labels"),
        "method": ("method", "methods"),
        "contrast": ("contrast", "contrasts"),
    }
    for row_key, (singular, plural) in fields.items():
        allowed = as_allowed_set(filters, singular, plural)
        if allowed is not None and row.get(row_key) not in allowed:
            return False
    return True


def resolve_vector_file(raw_path: str, manifest_path: Path) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    repo_candidate = resolve_path(raw_path)
    if repo_candidate.exists():
        return repo_candidate
    return manifest_path.parent / candidate


def load_vector(row: dict[str, Any], manifest_path: Path) -> np.ndarray:
    if load_numpy_safetensors is None:
        raise DirectionGeometryError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    vector_file = row.get("vector_file")
    tensor_key = row.get("tensor_key", "direction")
    if not isinstance(vector_file, str) or not vector_file:
        raise DirectionGeometryError(f"direction {row.get('direction_id')} missing vector_file")
    if not isinstance(tensor_key, str) or not tensor_key:
        raise DirectionGeometryError(f"direction {row.get('direction_id')} missing tensor_key")
    vector_path = resolve_vector_file(vector_file, manifest_path)
    tensors = load_numpy_safetensors(str(vector_path))
    if tensor_key not in tensors:
        raise DirectionGeometryError(f"{repo_relative(vector_path)} missing tensor key {tensor_key!r}")
    vector = np.asarray(tensors[tensor_key], dtype=np.float32)
    if vector.ndim != 1:
        raise DirectionGeometryError(f"{repo_relative(vector_path)}:{tensor_key} must be a 1D vector")
    return vector


def direction_label(row: dict[str, Any], set_label: str) -> str:
    pieces = [set_label]
    if row.get("candidate_label"):
        pieces.append(str(row["candidate_label"]))
    if row.get("role") is not None:
        pieces.append(f"role={row['role']}")
    if row.get("layer") is not None:
        pieces.append(f"l{row['layer']}")
    if row.get("feature") is not None:
        pieces.append(f"f{int(row['feature']):03d}")
    if row.get("contrast") is not None:
        pieces.append(str(row["contrast"]))
    return "::".join(pieces)


def load_direction_set(spec: dict[str, Any]) -> list[dict[str, Any]]:
    label = spec.get("label")
    manifest = spec.get("manifest")
    if not isinstance(label, str) or not label:
        raise DirectionGeometryError("each direction set must define label")
    if not isinstance(manifest, str) or not manifest:
        raise DirectionGeometryError(f"direction set {label!r} must define manifest")
    manifest_path = resolve_path(manifest)
    manifest_payload = load_json(manifest_path)
    rows = manifest_payload.get("directions")
    if not isinstance(rows, list) or not rows:
        raise DirectionGeometryError(f"{repo_relative(manifest_path)} must contain non-empty directions")

    loaded: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            raise DirectionGeometryError(f"{repo_relative(manifest_path)} directions must be objects")
        if not row_matches_spec(row, spec):
            continue
        vector = load_vector(row, manifest_path)
        norm = float(np.linalg.norm(vector))
        if norm <= 0.0:
            continue
        record = dict(row)
        record["_set_label"] = label
        record["_manifest"] = repo_relative(manifest_path)
        record["_resolved_vector_file"] = repo_relative(resolve_vector_file(str(row["vector_file"]), manifest_path))
        record["_vector"] = vector
        record["_norm"] = norm
        record["_unit_vector"] = (vector / norm).astype(np.float32)
        record["_display_label"] = direction_label(row, label)
        loaded.append(record)
    if not loaded:
        raise DirectionGeometryError(f"direction set {label!r} selected no non-zero vectors")
    return loaded


def inventory_row(index: int, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "index": index,
        "set_label": row["_set_label"],
        "direction_id": row.get("direction_id", ""),
        "display_label": row["_display_label"],
        "role": row.get("role", ""),
        "layer": row.get("layer", ""),
        "feature": row.get("feature", ""),
        "feature_skew_label": row.get("feature_skew_label", ""),
        "method": row.get("method", ""),
        "contrast": row.get("contrast", ""),
        "candidate_label": row.get("candidate_label", ""),
        "norm": row["_norm"],
        "manifest": row["_manifest"],
        "vector_file": row["_resolved_vector_file"],
    }


def pairwise_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for i, left in enumerate(rows):
        for j in range(i + 1, len(rows)):
            right = rows[j]
            if left["_unit_vector"].shape != right["_unit_vector"].shape:
                raise DirectionGeometryError(
                    f"hidden dim mismatch between {left.get('direction_id')} and {right.get('direction_id')}"
                )
            cosine = float(np.dot(left["_unit_vector"], right["_unit_vector"]))
            out.append(
                {
                    "left_index": i,
                    "right_index": j,
                    "left_set": left["_set_label"],
                    "right_set": right["_set_label"],
                    "left_direction_id": left.get("direction_id", ""),
                    "right_direction_id": right.get("direction_id", ""),
                    "left_label": left["_display_label"],
                    "right_label": right["_display_label"],
                    "left_layer": left.get("layer", ""),
                    "right_layer": right.get("layer", ""),
                    "cosine": cosine,
                    "abs_cosine": abs(cosine),
                }
            )
    return out


def nearest_neighbor_rows(pair_rows: list[dict[str, Any]], n_rows: int, k: int) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = {index: [] for index in range(n_rows)}
    for row in pair_rows:
        left_index = int(row["left_index"])
        right_index = int(row["right_index"])
        grouped[left_index].append({**row, "query_index": left_index, "neighbor_index": right_index})
        swapped = {
            "left_index": row["right_index"],
            "right_index": row["left_index"],
            "left_set": row["right_set"],
            "right_set": row["left_set"],
            "left_direction_id": row["right_direction_id"],
            "right_direction_id": row["left_direction_id"],
            "left_label": row["right_label"],
            "right_label": row["left_label"],
            "left_layer": row["right_layer"],
            "right_layer": row["left_layer"],
            "cosine": row["cosine"],
            "abs_cosine": row["abs_cosine"],
            "query_index": right_index,
            "neighbor_index": left_index,
        }
        grouped[right_index].append(swapped)

    out: list[dict[str, Any]] = []
    for query_index, neighbors in grouped.items():
        ordered = sorted(neighbors, key=lambda item: float(item["abs_cosine"]), reverse=True)
        for rank, row in enumerate(ordered[:k], start=1):
            out.append(
                {
                    "query_index": query_index,
                    "neighbor_rank": rank,
                    "neighbor_index": row["neighbor_index"],
                    "query_set": row["left_set"],
                    "neighbor_set": row["right_set"],
                    "query_direction_id": row["left_direction_id"],
                    "neighbor_direction_id": row["right_direction_id"],
                    "query_label": row["left_label"],
                    "neighbor_label": row["right_label"],
                    "query_layer": row["left_layer"],
                    "neighbor_layer": row["right_layer"],
                    "cosine": row["cosine"],
                    "abs_cosine": row["abs_cosine"],
                }
            )
    return out


def summarize(rows: list[dict[str, Any]], pair_rows: list[dict[str, Any]]) -> dict[str, Any]:
    set_counts: dict[str, int] = {}
    for row in rows:
        set_counts[row["_set_label"]] = set_counts.get(row["_set_label"], 0) + 1
    strongest = sorted(pair_rows, key=lambda row: float(row["abs_cosine"]), reverse=True)[:10]
    cross_set = [row for row in pair_rows if row["left_set"] != row["right_set"]]
    strongest_cross = sorted(cross_set, key=lambda row: float(row["abs_cosine"]), reverse=True)[:10]
    return {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "direction_count": len(rows),
        "pair_count": len(pair_rows),
        "set_counts": set_counts,
        "strongest_pairs": strongest,
        "strongest_cross_set_pairs": strongest_cross,
    }


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    direction_sets = config.get("direction_sets")
    output = config.get("output")
    if not isinstance(direction_sets, list) or not direction_sets:
        raise DirectionGeometryError("config must define non-empty direction_sets")
    if not isinstance(output, dict) or not output.get("root"):
        raise DirectionGeometryError("config must define output.root")

    rows: list[dict[str, Any]] = []
    for spec in direction_sets:
        if not isinstance(spec, dict):
            raise DirectionGeometryError("direction_sets entries must be mappings")
        rows.extend(load_direction_set(spec))
    pair_rows = pairwise_rows(rows)
    nearest_k = int(config.get("nearest_neighbors_per_direction", 5))
    nearest_rows = nearest_neighbor_rows(pair_rows, len(rows), nearest_k)

    output_root = resolve_path(output["root"])
    inventory_path = output_root / "direction_inventory.csv"
    pairwise_path = output_root / "pairwise_cosine.csv"
    nearest_path = output_root / "nearest_neighbors.csv"
    summary_path = output_root / "summary.json"
    write_csv(inventory_path, [inventory_row(index, row) for index, row in enumerate(rows)])
    write_csv(pairwise_path, pair_rows)
    write_csv(nearest_path, nearest_rows)
    summary_payload = summarize(rows, pair_rows)
    summary_payload.update(
        {
            "config": repo_relative(config_path),
            "output_root": repo_relative(output_root),
            "outputs": {
                "direction_inventory": repo_relative(inventory_path),
                "pairwise_cosine": repo_relative(pairwise_path),
                "nearest_neighbors": repo_relative(nearest_path),
                "summary": repo_relative(summary_path),
            },
        }
    )
    write_json(summary_path, summary_payload)
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "direction_count": len(rows),
        "pair_count": len(pair_rows),
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
    except DirectionGeometryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
