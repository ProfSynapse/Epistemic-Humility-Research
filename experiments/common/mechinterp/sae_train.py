#!/usr/bin/env python3
"""CPU/GPU agnostic Phase 3 sparse-autoencoder pilot.

This trains a small SAE over already-extracted hidden states. It is a bounded
exploratory pilot, not causal evidence and not Phase 1 headline evidence.
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
import torch
import torch.nn as nn
import yaml

from sae_smoke import (
    VALID_LABELS,
    SaeSmokeError,
    load_hidden_matrix,
    load_rows,
    repo_relative,
    resolve_path,
    validate_manifest,
    validate_output_root,
)

try:
    from safetensors.torch import save_file as save_torch_safetensors
except ImportError as exc:  # pragma: no cover - exercised only when dependency is absent
    save_torch_safetensors = None
    SAFETENSORS_TORCH_IMPORT_ERROR = exc
else:
    SAFETENSORS_TORCH_IMPORT_ERROR = None


NOTICE = "SAE_TRAINING_PILOT_ONLY"
ANALYSIS_TYPE = "phase3_sae_training_pilot"


class SaeTrainError(RuntimeError):
    pass


class SparseAutoencoder(nn.Module):
    def __init__(self, input_dim: int, dictionary_size: int, *, activation: str, top_k: int | None = None) -> None:
        super().__init__()
        self.encoder = nn.Linear(input_dim, dictionary_size)
        self.decoder = nn.Linear(dictionary_size, input_dim)
        self.activation = activation
        self.top_k = top_k

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        pre_code = self.encoder(x)
        if self.activation == "relu_l1":
            code = torch.relu(pre_code)
        elif self.activation == "topk_relu":
            if self.top_k is None:
                raise SaeTrainError("topk_relu activation requires top_k")
            relu_code = torch.relu(pre_code)
            if self.top_k <= 0 or self.top_k > relu_code.shape[1]:
                raise SaeTrainError(f"invalid top_k {self.top_k} for dictionary size {relu_code.shape[1]}")
            values, indices = torch.topk(relu_code, k=self.top_k, dim=1)
            code = torch.zeros_like(relu_code)
            code.scatter_(1, indices, values)
        else:
            raise SaeTrainError(f"unsupported activation {self.activation!r}")
        reconstruction = self.decoder(code)
        return reconstruction, code


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeTrainError(f"{path} did not load to a YAML object")
    return payload


def config_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def select_rows(rows: list[dict[str, Any]], *, max_rows_per_label: int | None, seed: int) -> list[dict[str, Any]]:
    if max_rows_per_label is None:
        return sorted(rows, key=lambda row: row["row_key"])
    if max_rows_per_label <= 0:
        raise SaeTrainError("max_rows_per_label must be positive when provided")
    by_label = {label: [] for label in sorted(VALID_LABELS)}
    for row in rows:
        by_label[row["label"]].append(row)
    missing = [label for label, label_rows in by_label.items() if len(label_rows) < max_rows_per_label]
    if missing:
        counts = {label: len(label_rows) for label, label_rows in by_label.items()}
        raise SaeTrainError(f"insufficient balance for labels {missing}; need {max_rows_per_label}, got {counts}")
    rng = np.random.default_rng(seed)
    selected: list[dict[str, Any]] = []
    for label in sorted(by_label):
        label_rows = sorted(by_label[label], key=lambda row: row["row_key"])
        indices = rng.permutation(len(label_rows))[:max_rows_per_label]
        selected.extend(label_rows[int(index)] for index in indices)
    return sorted(selected, key=lambda row: row["row_key"])


def split_indices(labels: list[str], *, validation_fraction: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    if not 0.0 < validation_fraction < 0.5:
        raise SaeTrainError("validation_fraction must be > 0 and < 0.5")
    rng = np.random.default_rng(seed)
    train_parts: list[int] = []
    val_parts: list[int] = []
    for label in sorted(VALID_LABELS):
        indices = np.array([index for index, value in enumerate(labels) if value == label], dtype=np.int64)
        if len(indices) < 2:
            raise SaeTrainError(f"need at least 2 rows for label {label!r} to split")
        rng.shuffle(indices)
        val_count = max(1, int(round(len(indices) * validation_fraction)))
        val_parts.extend(indices[:val_count].tolist())
        train_parts.extend(indices[val_count:].tolist())
    return np.array(sorted(train_parts), dtype=np.int64), np.array(sorted(val_parts), dtype=np.int64)


def choose_device(device_name: str) -> torch.device:
    if device_name == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device(device_name)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SaeTrainError("config requested cuda but torch.cuda.is_available() is false")
    return device


def standardize(train_x: np.ndarray, full_x: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    mean = train_x.mean(axis=0, keepdims=True).astype(np.float32)
    scale = train_x.std(axis=0, keepdims=True).astype(np.float32)
    scale = np.maximum(scale, 1e-6)
    return ((full_x - mean) / scale).astype(np.float32), mean.squeeze(0), scale.squeeze(0)


def evaluate(model: SparseAutoencoder, x: torch.Tensor, labels: list[str], l1_coefficient: float) -> dict[str, Any]:
    model.eval()
    with torch.no_grad():
        reconstruction, code = model(x)
        residual = x - reconstruction
        mse_by_row = torch.mean(residual.square(), dim=1)
        loss = mse_by_row.mean() + l1_coefficient * code.abs().mean()
        active = (code > 0).sum(dim=1).float()
        metrics: dict[str, Any] = {
            "loss": float(loss.item()),
            "mse": float(mse_by_row.mean().item()),
            "l1_mean_abs_code": float(code.abs().mean().item()),
            "mean_active_features": float(active.mean().item()),
            "median_active_features": float(active.median().item()),
            "max_active_features": int(active.max().item()),
            "code_density": float((code > 0).float().mean().item()),
        }
        for label in sorted(VALID_LABELS):
            label_indices = [index for index, value in enumerate(labels) if value == label]
            if label_indices:
                metrics[f"{label}_mse"] = float(mse_by_row[label_indices].mean().item())
                metrics[f"{label}_mean_active_features"] = float(active[label_indices].mean().item())
        return metrics


def train_sae(
    x_np: np.ndarray,
    labels: list[str],
    *,
    seed: int,
    dictionary_size: int,
    activation: str,
    top_k: int | None,
    learning_rate: float,
    l1_coefficient: float,
    epochs: int,
    batch_size: int,
    validation_fraction: float,
    device: torch.device,
) -> dict[str, Any]:
    if dictionary_size <= 0:
        raise SaeTrainError("dictionary_size must be positive")
    if activation not in {"relu_l1", "topk_relu"}:
        raise SaeTrainError(f"unsupported activation {activation!r}")
    if top_k is not None:
        top_k = int(top_k)
    if activation == "topk_relu" and top_k is None:
        raise SaeTrainError("topk_relu activation requires top_k")
    if top_k is not None and (top_k <= 0 or top_k > dictionary_size):
        raise SaeTrainError(f"top_k {top_k} must be between 1 and dictionary_size {dictionary_size}")
    if epochs <= 0:
        raise SaeTrainError("epochs must be positive")
    if batch_size <= 0:
        raise SaeTrainError("batch_size must be positive")

    torch.manual_seed(seed)
    np.random.seed(seed)
    train_idx, val_idx = split_indices(labels, validation_fraction=validation_fraction, seed=seed)
    x_std, mean, scale = standardize(x_np[train_idx], x_np)
    train_labels = [labels[int(index)] for index in train_idx]
    val_labels = [labels[int(index)] for index in val_idx]
    train_x = torch.tensor(x_std[train_idx], dtype=torch.float32, device=device)
    val_x = torch.tensor(x_std[val_idx], dtype=torch.float32, device=device)
    model = SparseAutoencoder(x_np.shape[1], dictionary_size, activation=activation, top_k=top_k).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    generator = torch.Generator(device="cpu").manual_seed(seed)

    history: list[dict[str, Any]] = []
    for epoch in range(1, epochs + 1):
        model.train()
        permutation = torch.randperm(train_x.shape[0], generator=generator, device=device)
        epoch_losses: list[float] = []
        for start in range(0, train_x.shape[0], batch_size):
            batch_indices = permutation[start : start + batch_size]
            batch = train_x[batch_indices]
            reconstruction, code = model(batch)
            mse = torch.mean((batch - reconstruction).square())
            l1 = code.abs().mean()
            loss = mse + l1_coefficient * l1
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            epoch_losses.append(float(loss.item()))
        if epoch == 1 or epoch == epochs or epoch % max(1, epochs // 5) == 0:
            train_metrics = evaluate(model, train_x, train_labels, l1_coefficient)
            val_metrics = evaluate(model, val_x, val_labels, l1_coefficient)
            history.append(
                {
                    "epoch": epoch,
                    "mean_batch_loss": float(np.mean(epoch_losses)),
                    "train_mse": train_metrics["mse"],
                    "validation_mse": val_metrics["mse"],
                    "validation_code_density": val_metrics["code_density"],
                    "validation_mean_active_features": val_metrics["mean_active_features"],
                }
            )

    train_metrics = evaluate(model, train_x, train_labels, l1_coefficient)
    val_metrics = evaluate(model, val_x, val_labels, l1_coefficient)
    return {
        "model": model,
        "normalization": {"mean": mean, "scale": scale},
        "split": {"train_indices": train_idx, "validation_indices": val_idx},
        "history": history,
        "metrics": {
            "train": train_metrics,
            "validation": val_metrics,
        },
    }


def run_candidate(
    candidate: dict[str, Any],
    *,
    training: dict[str, Any],
    output_root: Path,
    config_path: Path,
    config_sha: str,
) -> dict[str, Any]:
    extraction_dir = resolve_path(candidate["extraction_dir"])
    manifest_path = resolve_path(candidate.get("extraction_manifest", extraction_dir / "manifest.json"))
    source_manifest = validate_manifest(manifest_path, candidate)
    rows = load_rows(extraction_dir)
    selected_rows = select_rows(
        rows,
        max_rows_per_label=training.get("max_rows_per_label"),
        seed=int(training["seed"]),
    )
    x = load_hidden_matrix(candidate, selected_rows)
    labels = [row["label"] for row in selected_rows]
    device = choose_device(str(training.get("device", "auto")))
    result = train_sae(
        x,
        labels,
        seed=int(training["seed"]),
        dictionary_size=int(training["dictionary_size"]),
        activation=str(training.get("activation", "relu_l1")),
        top_k=training.get("top_k"),
        learning_rate=float(training["learning_rate"]),
        l1_coefficient=float(training["l1_coefficient"]),
        epochs=int(training["epochs"]),
        batch_size=int(training["batch_size"]),
        validation_fraction=float(training["validation_fraction"]),
        device=device,
    )

    candidate_out = output_root / candidate["label"]
    candidate_out.mkdir(parents=True, exist_ok=True)
    metrics_path = candidate_out / "metrics.json"
    manifest_path_out = candidate_out / "run_manifest.json"
    history_path = candidate_out / "training_history.json"
    selected_rows_path = candidate_out / "selected_rows.jsonl"
    weights_path = candidate_out / "sae_weights.safetensors"

    model: SparseAutoencoder = result["model"]
    normalization = result["normalization"]
    metrics = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "candidate_label": candidate["label"],
        "candidate_role": candidate["role"],
        "candidate_layer": int(candidate["layer"]),
        "row_count": len(selected_rows),
        "hidden_dim": int(x.shape[1]),
        "dictionary_size": int(training["dictionary_size"]),
        "activation": str(training.get("activation", "relu_l1")),
        "top_k": int(training["top_k"]) if training.get("top_k") is not None else None,
        "epochs": int(training["epochs"]),
        "batch_size": int(training["batch_size"]),
        "learning_rate": float(training["learning_rate"]),
        "l1_coefficient": float(training["l1_coefficient"]),
        "device": str(device),
        "train": result["metrics"]["train"],
        "validation": result["metrics"]["validation"],
    }
    manifest = {
        "schema_version": "phase3-sae-training-pilot/v1",
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "created_at": utc_now(),
        "config": repo_relative(config_path),
        "config_sha256": config_sha,
        "candidate": {
            "label": candidate["label"],
            "arm": candidate.get("arm"),
            "role": candidate["role"],
            "layer": int(candidate["layer"]),
            "extraction_dir": repo_relative(extraction_dir),
            "extraction_manifest": repo_relative(manifest_path),
            "source_manifest_status": source_manifest.get("status"),
            "source_manifest_verified": source_manifest.get("verified"),
        },
        "selection": {
            "seed": int(training["seed"]),
            "max_rows_per_label": training.get("max_rows_per_label"),
            "row_count": len(selected_rows),
            "label_counts": {label: labels.count(label) for label in sorted(VALID_LABELS)},
        },
        "training": {
            "dictionary_size": int(training["dictionary_size"]),
            "activation": str(training.get("activation", "relu_l1")),
            "top_k": int(training["top_k"]) if training.get("top_k") is not None else None,
            "epochs": int(training["epochs"]),
            "batch_size": int(training["batch_size"]),
            "learning_rate": float(training["learning_rate"]),
            "l1_coefficient": float(training["l1_coefficient"]),
            "validation_fraction": float(training["validation_fraction"]),
            "device": str(device),
            "trained_sae": True,
            "causal_evidence": False,
            "headline_evidence": False,
        },
        "outputs": {
            "metrics": repo_relative(metrics_path),
            "history": repo_relative(history_path),
            "selected_rows": repo_relative(selected_rows_path),
            "weights": repo_relative(weights_path),
        },
    }
    write_json(metrics_path, metrics)
    write_json(history_path, {"history": result["history"]})
    selected_rows_path.write_text(
        "".join(json.dumps({"row_key": row["row_key"], "label": row["label"]}, sort_keys=True) + "\n" for row in selected_rows),
        encoding="utf-8",
    )
    if save_torch_safetensors is None:
        raise SaeTrainError(f"safetensors.torch is required for weight output: {SAFETENSORS_TORCH_IMPORT_ERROR}")
    tensors = {
        "encoder.weight": model.encoder.weight.detach().cpu(),
        "encoder.bias": model.encoder.bias.detach().cpu(),
        "decoder.weight": model.decoder.weight.detach().cpu(),
        "decoder.bias": model.decoder.bias.detach().cpu(),
        "normalization.mean": torch.tensor(normalization["mean"], dtype=torch.float32),
        "normalization.scale": torch.tensor(normalization["scale"], dtype=torch.float32),
    }
    save_torch_safetensors(tensors, str(weights_path))
    write_json(manifest_path_out, manifest)
    return manifest


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    training = config.get("training")
    candidates = config.get("candidate_extractions")
    if not isinstance(output, dict) or "root" not in output:
        raise SaeTrainError("config must define output.root")
    if not isinstance(training, dict):
        raise SaeTrainError("config must define training settings")
    for required in (
        "seed",
        "dictionary_size",
        "epochs",
        "batch_size",
        "learning_rate",
        "l1_coefficient",
        "validation_fraction",
    ):
        if required not in training:
            raise SaeTrainError(f"config training missing {required}")
    if not isinstance(candidates, list) or not candidates:
        raise SaeTrainError("config must define non-empty candidate_extractions")
    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(candidate["extraction_dir"]) for candidate in candidates]
    validate_output_root(output_root, extraction_dirs)
    config_sha = config_sha256(config_path)
    manifests = [
        run_candidate(
            dict(candidate),
            training=training,
            output_root=output_root,
            config_path=config_path,
            config_sha=config_sha,
        )
        for candidate in candidates
    ]
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "output_root": repo_relative(output_root),
        "candidate_count": len(manifests),
        "manifests": [
            {
                "run_manifest": repo_relative(output_root / manifest["candidate"]["label"] / "run_manifest.json"),
                **manifest["outputs"],
            }
            for manifest in manifests
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (SaeSmokeError, SaeTrainError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
