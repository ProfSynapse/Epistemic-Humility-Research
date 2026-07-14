#!/usr/bin/env python3
"""Candidate directions from hidden-state extraction artifacts.

This is a reusable data layer for later causal intervention pilots. It reads
existing hidden-state extraction directories, derives simple candidate vectors,
and writes vector shards plus CSV/JSON provenance. It does not run generation or
apply steering.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from safetensors.numpy import load_file, save_file


ANALYSIS_TYPE = "hidden_state_candidate_directions"
NOTICE = (
    "EXPLORATORY_DIRECTION_CANDIDATES: data layer for later intervention "
    "pilots; not pre-registered headline evidence and not a steering run"
)
DEFAULT_ROLES = ("h_base", "h_lora", "delta")
DEFAULT_METHODS = ("known_unknown_diff", "arm_delta_mean")
LABELS = ("known", "unknown")


@dataclass(frozen=True)
class HiddenStateRow:
    row_key: str
    label: str
    safe_key: str


@dataclass(frozen=True)
class LayerVectors:
    role: str
    layer: int
    vectors: list[np.ndarray]
    labels: list[str]
    row_keys: list[str]


def read_rows(extraction_dir: Path) -> tuple[list[HiddenStateRow], dict[str, int]]:
    rows_path = extraction_dir / "rows.jsonl"
    if not rows_path.exists():
        raise FileNotFoundError(f"missing rows.jsonl at {rows_path}")

    rows: list[HiddenStateRow] = []
    skipped: dict[str, int] = {}
    with rows_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            label = str(record.get("label", "")).lower()
            if label not in LABELS:
                skipped[label or "<missing>"] = skipped.get(label or "<missing>", 0) + 1
                continue
            row_key = record.get("probe_pool_row_key")
            if not row_key:
                raise ValueError(f"{rows_path}:{line_no} missing probe_pool_row_key")
            rows.append(HiddenStateRow(
                row_key=str(row_key),
                label=label,
                safe_key=str(row_key).replace("|", "_"),
            ))
    return rows, skipped


def load_layer_vectors(
    extraction_dir: Path,
    rows: list[HiddenStateRow],
    role: str,
) -> dict[int, LayerVectors]:
    by_layer: dict[int, LayerVectors] = {}
    mutable: dict[int, tuple[list[np.ndarray], list[str], list[str]]] = {}
    for row in rows:
        shard = extraction_dir / f"{row.safe_key}__{role}.safetensors"
        if not shard.exists():
            continue
        tensors = load_file(str(shard))
        for name, vector in tensors.items():
            layer = parse_layer_name(name, shard)
            arr = np.asarray(vector, dtype=np.float64)
            if arr.ndim != 1:
                raise ValueError(f"{shard}:{name} expected 1-D vector, got {arr.shape}")
            vectors, labels, row_keys = mutable.setdefault(layer, ([], [], []))
            vectors.append(arr)
            labels.append(row.label)
            row_keys.append(row.row_key)

    for layer, (vectors, labels, row_keys) in mutable.items():
        by_layer[layer] = LayerVectors(
            role=role,
            layer=layer,
            vectors=vectors,
            labels=labels,
            row_keys=row_keys,
        )
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


def difference_in_means(layer: LayerVectors, *, positive_label: str,
                        negative_label: str) -> dict | None:
    labels = np.asarray(layer.labels)
    positive_mask = labels == positive_label
    negative_mask = labels == negative_label
    n_positive = int(np.sum(positive_mask))
    n_negative = int(np.sum(negative_mask))
    if n_positive == 0 or n_negative == 0:
        return None

    matrix = np.vstack(layer.vectors)
    positive_mean = matrix[positive_mask].mean(axis=0)
    negative_mean = matrix[negative_mask].mean(axis=0)
    vector = positive_mean - negative_mean
    return {
        "method": "known_unknown_diff",
        "contrast": f"{positive_label}_minus_{negative_label}",
        "positive_label": positive_label,
        "negative_label": negative_label,
        "n_positive": n_positive,
        "n_negative": n_negative,
        "n_total": n_positive + n_negative,
        "vector": vector,
    }


def mean_delta(layer: LayerVectors, *, label: str | None) -> dict | None:
    labels = np.asarray(layer.labels)
    if label is None:
        mask = np.ones(len(layer.labels), dtype=bool)
        label_name = "all"
    else:
        mask = labels == label
        label_name = label
    n = int(np.sum(mask))
    if n == 0:
        return None

    matrix = np.vstack(layer.vectors)
    vector = matrix[mask].mean(axis=0)
    return {
        "method": "arm_delta_mean",
        "contrast": f"{label_name}_mean_lora_minus_base",
        "positive_label": label_name,
        "negative_label": "",
        "n_positive": n,
        "n_negative": 0,
        "n_total": n,
        "vector": vector,
    }


def derive_directions(
    extraction_dir: Path,
    *,
    roles: tuple[str, ...] = DEFAULT_ROLES,
    methods: tuple[str, ...] = DEFAULT_METHODS,
) -> tuple[list[dict], dict]:
    rows, skipped_labels = read_rows(extraction_dir)
    if not rows:
        raise ValueError(f"{extraction_dir} contains no known/unknown labeled rows")

    direction_rows: list[dict] = []
    for role in roles:
        layer_vectors = load_layer_vectors(extraction_dir, rows, role)
        if not layer_vectors:
            direction_rows.append(skipped_direction(
                role=role,
                layer="",
                method="load_role",
                reason=f"no {role!r} safetensors shards found",
            ))
            continue
        for layer in sorted(layer_vectors):
            data = layer_vectors[layer]
            if "known_unknown_diff" in methods:
                candidate = difference_in_means(
                    data,
                    positive_label="unknown",
                    negative_label="known",
                )
                if candidate is None:
                    direction_rows.append(skipped_direction(
                        role=role,
                        layer=layer,
                        method="known_unknown_diff",
                        reason="requires at least one known and one unknown row",
                    ))
                else:
                    direction_rows.append(materialize_direction(role, layer, candidate))

            if "arm_delta_mean" in methods and role == "delta":
                for label in (None, "known", "unknown"):
                    candidate = mean_delta(data, label=label)
                    if candidate is not None:
                        direction_rows.append(materialize_direction(role, layer, candidate))

    metadata = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "extraction_dir": str(extraction_dir),
        "roles": list(roles),
        "methods": list(methods),
        "direction_conventions": {
            "known_unknown_diff": "unknown_mean_minus_known_mean",
            "arm_delta_mean": "mean(delta) where delta=h_lora-h_base",
        },
        "dependencies": ["numpy", "safetensors"],
        "n_labeled_rows": len(rows),
        "label_counts": {
            label: sum(1 for row in rows if row.label == label)
            for label in LABELS
        },
        "skipped_input_labels": skipped_labels,
        "source_hashes": source_hashes(extraction_dir),
        "directions": public_direction_rows(direction_rows),
    }
    return direction_rows, metadata


def materialize_direction(role: str, layer: int, candidate: dict) -> dict:
    vector = np.asarray(candidate.pop("vector"), dtype=np.float32)
    norm = float(np.linalg.norm(vector.astype(np.float64)))
    unit_vector = vector if norm == 0.0 else (vector / norm).astype(np.float32)
    direction_id = stable_direction_id(
        method=candidate["method"],
        role=role,
        layer=layer,
        contrast=candidate["contrast"],
        vector=unit_vector,
    )
    return {
        "direction_id": direction_id,
        "role": role,
        "layer": layer,
        "status": "ok",
        "hidden_dim": int(vector.shape[0]),
        "norm": norm,
        "unit_norm": float(np.linalg.norm(unit_vector.astype(np.float64))),
        "vector_sha256": vector_sha256(unit_vector),
        "tensor_key": "direction",
        "vector_file": f"directions/{direction_id}.safetensors",
        "notice": NOTICE,
        **candidate,
        "_vector": unit_vector,
    }


def skipped_direction(role: str, layer: int | str, method: str, reason: str) -> dict:
    return {
        "direction_id": "",
        "role": role,
        "layer": layer,
        "method": method,
        "contrast": "",
        "status": "skipped",
        "reason": reason,
        "positive_label": "",
        "negative_label": "",
        "n_positive": 0,
        "n_negative": 0,
        "n_total": 0,
        "hidden_dim": "",
        "norm": "",
        "unit_norm": "",
        "vector_sha256": "",
        "tensor_key": "",
        "vector_file": "",
        "notice": NOTICE,
    }


def public_direction_rows(rows: list[dict]) -> list[dict]:
    public_rows: list[dict] = []
    for row in rows:
        public = dict(row)
        public.pop("_vector", None)
        public_rows.append(public)
    return public_rows


def stable_direction_id(*, method: str, role: str, layer: int, contrast: str,
                        vector: np.ndarray) -> str:
    h = hashlib.sha256()
    h.update(method.encode("utf-8"))
    h.update(b"\0")
    h.update(role.encode("utf-8"))
    h.update(b"\0")
    h.update(str(layer).encode("ascii"))
    h.update(b"\0")
    h.update(contrast.encode("utf-8"))
    h.update(b"\0")
    h.update(np.asarray(vector, dtype=np.float32).tobytes())
    return f"direction__{h.hexdigest()[:16]}"


def vector_sha256(vector: np.ndarray) -> str:
    return hashlib.sha256(np.asarray(vector, dtype=np.float32).tobytes()).hexdigest()


def file_sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_hashes(extraction_dir: Path) -> dict:
    return {
        "manifest_json_sha256": file_sha256(extraction_dir / "manifest.json"),
        "rows_jsonl_sha256": file_sha256(extraction_dir / "rows.jsonl"),
    }


CSV_FIELDNAMES = [
    "direction_id", "method", "contrast", "role", "layer", "status", "reason",
    "positive_label", "negative_label", "n_positive", "n_negative", "n_total",
    "hidden_dim", "norm", "unit_norm", "vector_sha256", "tensor_key",
    "vector_file", "notice",
]


def write_outputs(output_dir: Path, prefix: str, rows: list[dict],
                  metadata: dict) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    vectors_dir = output_dir / "directions"
    vectors_dir.mkdir(parents=True, exist_ok=True)

    public_rows: list[dict] = []
    for row in rows:
        public = dict(row)
        vector = public.pop("_vector", None)
        if vector is not None:
            save_file(
                {"direction": np.asarray(vector, dtype=np.float32)},
                str(output_dir / public["vector_file"]),
                metadata={
                    "direction_id": public["direction_id"],
                    "analysis_type": ANALYSIS_TYPE,
                    "method": public["method"],
                    "role": public["role"],
                    "layer": str(public["layer"]),
                    "contrast": public["contrast"],
                },
            )
        public_rows.append(public)

    metadata = dict(metadata)
    metadata["directions"] = public_rows

    csv_path = output_dir / f"{prefix}.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in public_rows:
            writer.writerow(row)

    manifest_path = output_dir / f"{prefix}.manifest.json"
    manifest_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return csv_path, manifest_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extraction_dir", type=Path,
                        help="directory containing rows.jsonl and safetensors shards")
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="directory for outputs; defaults to extraction_dir")
    parser.add_argument("--prefix", default="hidden_state_candidate_directions",
                        help="output filename prefix")
    parser.add_argument("--roles", nargs="+", default=list(DEFAULT_ROLES),
                        choices=list(DEFAULT_ROLES),
                        help="tensor roles to derive directions from")
    parser.add_argument("--methods", nargs="+", default=list(DEFAULT_METHODS),
                        choices=list(DEFAULT_METHODS),
                        help="direction derivation methods")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    extraction_dir = args.extraction_dir.resolve()
    output_dir = (args.output_dir or extraction_dir).resolve()
    rows, metadata = derive_directions(
        extraction_dir,
        roles=tuple(args.roles),
        methods=tuple(args.methods),
    )
    csv_path, manifest_path = write_outputs(output_dir, args.prefix, rows, metadata)
    print(NOTICE)
    print(f"wrote {csv_path}")
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
