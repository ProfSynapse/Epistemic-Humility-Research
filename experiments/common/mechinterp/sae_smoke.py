#!/usr/bin/env python3
"""CPU-only Phase 3 SAE-shaped plumbing smoke.

This validates hidden-state extraction plumbing for later SAE work. It does not
train an SAE and must not be interpreted as SAE evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import yaml

try:
    from safetensors.numpy import load_file as load_safetensors
    from safetensors.numpy import save_file as save_safetensors
except ImportError as exc:  # pragma: no cover - exercised only when dependency is absent
    load_safetensors = None
    save_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "experiment/phase1/probe"
NOTICE = "SAE_PLUMBING_SMOKE_ONLY"
ANALYSIS_TYPE = "phase3_sae_plumbing_smoke_only"
VALID_LABELS = {"known", "unknown"}


class SaeSmokeError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def resolve_path(path_text: str | Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise SaeSmokeError(f"{path} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeSmokeError(f"{path} did not load to a YAML object")
    return payload


def config_sha256(config_path: Path) -> str:
    return hashlib.sha256(config_path.read_bytes()).hexdigest()


def safe_row_key(row_key: str) -> str:
    if not isinstance(row_key, str) or not row_key:
        raise SaeSmokeError("row_key must be a non-empty string")
    return row_key.replace("::", "__")


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_output_root(output_root: Path, extraction_dirs: list[Path]) -> None:
    for extraction_dir in extraction_dirs:
        if is_relative_to(output_root, extraction_dir):
            raise SaeSmokeError(
                f"output root must not be inside extraction dir: {repo_relative(output_root)} "
                f"inside {repo_relative(extraction_dir)}"
            )


def validate_manifest(path: Path, candidate: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise SaeSmokeError(f"missing extraction manifest: {repo_relative(path)}")
    manifest = load_json(path)
    if manifest.get("status") != candidate.get("required_status", "ok"):
        raise SaeSmokeError(f"{repo_relative(path)} status is not ok")
    if manifest.get("verified") is not True:
        raise SaeSmokeError(f"{repo_relative(path)} verified is not true")
    if manifest.get("persistence_format") != "safetensors":
        raise SaeSmokeError(f"{repo_relative(path)} persistence_format is not safetensors")

    role = candidate["role"]
    layer = int(candidate["layer"])
    tensor_shapes = manifest.get("tensor_shapes")
    if not isinstance(tensor_shapes, dict) or role not in tensor_shapes:
        raise SaeSmokeError(f"{repo_relative(path)} missing tensor shape for role {role!r}")
    role_shape = tensor_shapes[role]
    if (
        not isinstance(role_shape, list)
        or len(role_shape) != 2
        or not all(isinstance(value, int) for value in role_shape)
    ):
        raise SaeSmokeError(f"{repo_relative(path)} invalid tensor shape for role {role!r}")
    layer_count, hidden_dim = role_shape
    if layer < 0 or layer >= layer_count:
        raise SaeSmokeError(f"candidate layer L{layer} is outside manifest layer count {layer_count}")
    candidate["hidden_dim"] = hidden_dim
    return manifest


def load_rows(extraction_dir: Path) -> list[dict[str, Any]]:
    rows_path = extraction_dir / "rows.jsonl"
    if not rows_path.is_file():
        raise SaeSmokeError(f"missing rows file: {repo_relative(rows_path)}")
    rows: list[dict[str, Any]] = []
    with rows_path.open(encoding="utf-8") as fh:
        for line_number, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise SaeSmokeError(f"{repo_relative(rows_path)}:{line_number} row is not an object")
            label = row.get("label")
            if label not in VALID_LABELS:
                raise SaeSmokeError(f"{repo_relative(rows_path)}:{line_number} invalid label {label!r}")
            row_key = row.get("row_key") or row.get("probe_pool_row_key")
            if not isinstance(row_key, str) or not row_key:
                raise SaeSmokeError(f"{repo_relative(rows_path)}:{line_number} missing row_key")
            row["row_key"] = row_key
            rows.append(row)
    return rows


def select_balanced_rows(rows: list[dict[str, Any]], *, max_rows_per_label: int, seed: int) -> list[dict[str, Any]]:
    if max_rows_per_label <= 0:
        raise SaeSmokeError("max_rows_per_label must be positive")
    by_label = {label: [] for label in sorted(VALID_LABELS)}
    for row in rows:
        by_label[row["label"]].append(row)
    missing = [label for label, label_rows in by_label.items() if len(label_rows) < max_rows_per_label]
    if missing:
        counts = {label: len(label_rows) for label, label_rows in by_label.items()}
        raise SaeSmokeError(
            f"insufficient balance for labels {missing}; need {max_rows_per_label} each, got {counts}"
        )

    rng = np.random.default_rng(seed)
    selected: list[dict[str, Any]] = []
    for label in sorted(by_label):
        label_rows = sorted(by_label[label], key=lambda row: row["row_key"])
        indices = rng.permutation(len(label_rows))[:max_rows_per_label]
        selected.extend(label_rows[int(index)] for index in indices)
    return selected


def load_hidden_matrix(candidate: dict[str, Any], rows: list[dict[str, Any]]) -> np.ndarray:
    if load_safetensors is None:
        raise SaeSmokeError(f"safetensors is required for this smoke: {SAFETENSORS_IMPORT_ERROR}")

    extraction_dir = resolve_path(candidate["extraction_dir"])
    role = candidate["role"]
    tensor_key = f"L{int(candidate['layer'])}"
    expected_dim = int(candidate["hidden_dim"])
    vectors: list[np.ndarray] = []
    for row in rows:
        shard = extraction_dir / f"{safe_row_key(row['row_key'])}__{role}.safetensors"
        if not shard.is_file():
            raise SaeSmokeError(f"missing role shard: {repo_relative(shard)}")
        tensors = load_safetensors(str(shard))
        if tensor_key not in tensors:
            raise SaeSmokeError(f"{repo_relative(shard)} missing tensor key {tensor_key}")
        vector = np.asarray(tensors[tensor_key], dtype=np.float32)
        if vector.ndim != 1 or vector.shape[0] != expected_dim:
            raise SaeSmokeError(
                f"{repo_relative(shard)} {tensor_key} shape mismatch: "
                f"expected ({expected_dim},), got {tuple(vector.shape)}"
            )
        vectors.append(vector)
    return np.stack(vectors, axis=0)


def top_k_sparse(code: np.ndarray, top_k: int) -> np.ndarray:
    if top_k <= 0:
        raise SaeSmokeError("top_k must be positive")
    if top_k > code.shape[1]:
        raise SaeSmokeError(f"top_k {top_k} exceeds bottleneck dimension {code.shape[1]}")
    sparse = np.zeros_like(code)
    indices = np.argpartition(np.abs(code), -top_k, axis=1)[:, -top_k:]
    row_indices = np.arange(code.shape[0])[:, None]
    sparse[row_indices, indices] = code[row_indices, indices]
    return sparse


def run_plumbing_sae(x: np.ndarray, *, seed: int, bottleneck_dim: int, top_k: int) -> dict[str, Any]:
    if x.ndim != 2:
        raise SaeSmokeError(f"hidden matrix must be 2D, got {x.ndim}D")
    if bottleneck_dim <= 0:
        raise SaeSmokeError("bottleneck_dim must be positive")
    rng = np.random.default_rng(seed)
    row_count, hidden_dim = x.shape
    encoder = rng.normal(0.0, 1.0 / np.sqrt(hidden_dim), size=(hidden_dim, bottleneck_dim)).astype(np.float32)
    decoder = rng.normal(0.0, 1.0 / np.sqrt(bottleneck_dim), size=(bottleneck_dim, hidden_dim)).astype(np.float32)
    code = x @ encoder
    sparse_code = top_k_sparse(code, top_k)
    reconstruction = sparse_code @ decoder
    residual = x - reconstruction
    mse_by_row = np.mean(np.square(residual), axis=1)
    x_norm = np.linalg.norm(x, axis=1)
    residual_norm = np.linalg.norm(residual, axis=1)
    relative_error = residual_norm / np.maximum(x_norm, 1e-12)
    activation_counts = np.count_nonzero(sparse_code, axis=1)
    return {
        "metrics": {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "row_count": int(row_count),
            "hidden_dim": int(hidden_dim),
            "bottleneck_dim": int(bottleneck_dim),
            "top_k": int(top_k),
            "mean_mse": float(np.mean(mse_by_row)),
            "median_mse": float(np.median(mse_by_row)),
            "max_mse": float(np.max(mse_by_row)),
            "mean_relative_reconstruction_error": float(np.mean(relative_error)),
            "median_relative_reconstruction_error": float(np.median(relative_error)),
            "mean_active_features": float(np.mean(activation_counts)),
            "code_density": float(np.count_nonzero(sparse_code) / sparse_code.size),
            "input_l2_mean": float(np.mean(x_norm)),
            "reconstruction_l2_mean": float(np.mean(np.linalg.norm(reconstruction, axis=1))),
        },
        "tensors": {
            "encoder": encoder.astype(np.float32),
            "decoder": decoder.astype(np.float32),
            "sparse_code": sparse_code.astype(np.float32),
            "reconstruction": reconstruction.astype(np.float32),
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_candidate(
    candidate: dict[str, Any],
    *,
    output_root: Path,
    smoke: dict[str, Any],
    config_path: Path,
    config_sha: str,
) -> dict[str, Any]:
    extraction_dir = resolve_path(candidate["extraction_dir"])
    manifest_path = resolve_path(candidate.get("extraction_manifest", extraction_dir / "manifest.json"))
    source_manifest = validate_manifest(manifest_path, candidate)
    rows = load_rows(extraction_dir)
    selected_rows = select_balanced_rows(
        rows,
        max_rows_per_label=int(smoke["max_rows_per_label"]),
        seed=int(smoke["seed"]),
    )
    x = load_hidden_matrix(candidate, selected_rows)
    result = run_plumbing_sae(
        x,
        seed=int(smoke["seed"]),
        bottleneck_dim=int(smoke["bottleneck_dim"]),
        top_k=int(smoke["top_k"]),
    )

    candidate_label = candidate["label"]
    candidate_out = output_root / candidate_label
    metrics_path = candidate_out / "metrics.json"
    manifest_out_path = candidate_out / "run_manifest.json"
    tensors_path = candidate_out / "plumbing_tensors.safetensors"
    selected_rows_path = candidate_out / "selected_rows.jsonl"

    metrics = {
        **result["metrics"],
        "candidate_label": candidate_label,
        "candidate_role": candidate["role"],
        "candidate_layer": int(candidate["layer"]),
    }
    manifest = {
        "schema_version": "phase3-sae-plumbing-smoke/v1",
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "created_at": utc_now(),
        "config": repo_relative(config_path),
        "config_sha256": config_sha,
        "candidate": {
            "label": candidate_label,
            "arm": candidate.get("arm"),
            "role": candidate["role"],
            "layer": int(candidate["layer"]),
            "extraction_dir": repo_relative(extraction_dir),
            "extraction_manifest": repo_relative(manifest_path),
            "source_manifest_status": source_manifest.get("status"),
            "source_manifest_verified": source_manifest.get("verified"),
        },
        "selection": {
            "seed": int(smoke["seed"]),
            "max_rows_per_label": int(smoke["max_rows_per_label"]),
            "labels": sorted(VALID_LABELS),
            "row_count": len(selected_rows),
            "row_keys": [row["row_key"] for row in selected_rows],
        },
        "smoke": {
            "bottleneck_dim": int(smoke["bottleneck_dim"]),
            "top_k": int(smoke["top_k"]),
            "numpy_only": True,
            "trained_sae": False,
            "external_sae_dependency": False,
        },
        "outputs": {
            "metrics": repo_relative(metrics_path),
            "selected_rows": repo_relative(selected_rows_path),
            "tensors": repo_relative(tensors_path) if smoke.get("write_tensors", True) else None,
        },
    }

    write_json(metrics_path, metrics)
    write_json(manifest_out_path, manifest)
    selected_rows_path.write_text(
        "".join(
            json.dumps(
                {
                    "row_key": row["row_key"],
                    "label": row["label"],
                    "question": row.get("question"),
                    "strata": row.get("strata", []),
                },
                sort_keys=True,
            )
            + "\n"
            for row in selected_rows
        ),
        encoding="utf-8",
    )
    if smoke.get("write_tensors", True):
        if save_safetensors is None:
            raise SaeSmokeError(f"safetensors is required for tensor output: {SAFETENSORS_IMPORT_ERROR}")
        save_safetensors(result["tensors"], str(tensors_path))
    return manifest


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    smoke = config.get("smoke")
    candidates = config.get("candidate_extractions")
    if not isinstance(output, dict) or "root" not in output:
        raise SaeSmokeError("config must define output.root")
    if not isinstance(smoke, dict):
        raise SaeSmokeError("config must define smoke settings")
    for required in ("seed", "max_rows_per_label", "bottleneck_dim", "top_k"):
        if required not in smoke:
            raise SaeSmokeError(f"config smoke missing {required}")
    if not isinstance(candidates, list) or not candidates:
        raise SaeSmokeError("config must define non-empty candidate_extractions")
    for candidate in candidates:
        for required in ("label", "extraction_dir", "role", "layer"):
            if required not in candidate:
                raise SaeSmokeError(f"candidate missing {required}")

    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(candidate["extraction_dir"]) for candidate in candidates]
    validate_output_root(output_root, extraction_dirs)
    config_sha = config_sha256(config_path)
    manifests = [
        run_candidate(
            dict(candidate),
            output_root=output_root,
            smoke=smoke,
            config_path=config_path,
            config_sha=config_sha,
        )
        for candidate in candidates
    ]
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "output_root": repo_relative(output_root),
        "candidate_count": len(manifests),
        "manifests": [manifest["outputs"] | {"run_manifest": repo_relative(output_root / manifest["candidate"]["label"] / "run_manifest.json")} for manifest in manifests],
    }
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except SaeSmokeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
