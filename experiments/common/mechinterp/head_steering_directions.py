#!/usr/bin/env python3
"""Build per-head ITI steering directions from an attention_head extraction.

Step A.4 input (offline, GPU-free). Consumes an ``attention_head``-granularity
extraction (one concatenated o_proj-input vector per block) plus a chosen set of
(layer, head) targets, and emits the per-head **mass-mean** steering directions
that the during-generation intervention harness adds to those heads.

ITI (paper:2306.03341) intervenes by shifting a sparse set of attention heads
along a per-head direction, scaled by the std of that head's activations along
the direction:  h' = h + alpha * sigma * theta. This script produces, for each
target head:
  - theta: the UNIT mass-mean direction (mean(positive) - mean(negative)) over the
    intervened arm's per-head slice, where positive/negative are the contrast's
    behavior groups;
  - sigma: the std of the intervened arm's per-head activations projected onto
    theta (the ITI scale);
  - the rank-AUC / Cohen's d of the projection (carried for provenance / target
    triage), computed identically to the localization scan.

Sign convention: theta points from the NEGATIVE group toward the POSITIVE group
(positive_label). To steer activations toward the positive group, add +alpha; to
steer toward the negative group (e.g. toward `unknown_refused` when positive is
`unknown_answered_wrong`), use negative alpha. The harness sweeps alpha, so the
artifact does not bake in a steering sign — it records the contrast labels so the
consumer knows which direction is "good".

Directions are read from a configurable arm role (default ``h_lora`` — the
adapter-active activations whose forward pass the harness hooks during
generation), NOT the delta role.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

from behavior_axis_scan import (
    BehaviorAxisScanError,
    contrast_masks,
    load_config,
    load_extraction_rows,
    load_role_cube,
    write_json,
)
from head_localization_scan import HeadLocalizationScanError, validate_head_manifest
from sae_smoke import (
    SaeSmokeError,
    repo_relative,
    resolve_path,
    validate_output_root,
)

ARTIFACT_TYPE = "phase3_head_steering_directions"
NOTICE = "HEAD_STEERING_DIRECTIONS_ONLY"
DEFAULT_ARM_ROLE = "h_lora"


class HeadSteeringError(RuntimeError):
    pass


def _unit(vec: np.ndarray) -> tuple[np.ndarray, float]:
    norm = float(np.linalg.norm(vec.astype(np.float64)))
    if norm <= 1e-12:
        return np.zeros_like(vec, dtype=np.float32), 0.0
    return (vec / norm).astype(np.float32), norm


def head_direction(
    head_matrix: np.ndarray,
    *,
    positive_mask: np.ndarray,
    negative_mask: np.ndarray,
) -> dict[str, Any]:
    """Mass-mean unit direction + ITI sigma for one head's (n_rows, head_dim) slice.

    sigma is the std of ALL rows' projections onto theta (pooled), matching the
    ITI activation-scale; theta points negative->positive.
    """
    positive = head_matrix[positive_mask]
    negative = head_matrix[negative_mask]
    mean_diff = np.mean(positive, axis=0) - np.mean(negative, axis=0)
    theta, mean_diff_norm = _unit(mean_diff)
    projections = head_matrix @ theta
    sigma = float(np.std(projections.astype(np.float64)))
    pos_proj = positive @ theta
    neg_proj = negative @ theta
    return {
        "theta": theta.tolist(),
        "sigma": sigma,
        "mean_diff_norm": mean_diff_norm,
        "positive_projection_mean": float(np.mean(pos_proj)),
        "negative_projection_mean": float(np.mean(neg_proj)),
    }


def _parse_targets(raw: Any) -> list[tuple[int, int]]:
    if not isinstance(raw, list) or not raw:
        raise HeadSteeringError("targets must be a non-empty list of {layer, head}")
    targets: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for item in raw:
        if not isinstance(item, dict) or "layer" not in item or "head" not in item:
            raise HeadSteeringError(f"target {item!r} must define integer layer and head")
        layer = int(item["layer"])
        head = int(item["head"])
        if (layer, head) in seen:
            raise HeadSteeringError(f"duplicate target (layer={layer}, head={head})")
        seen.add((layer, head))
        targets.append((layer, head))
    return targets


def build_directions(
    spec: dict[str, Any],
    *,
    output_root: Path,
) -> dict[str, Any]:
    label = spec.get("label")
    if not isinstance(label, str) or not label:
        raise HeadSteeringError("spec must define a non-empty label")
    behavior_arm = spec.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise HeadSteeringError(f"spec {label!r} must define behavior_arm")
    arm_role = str(spec.get("arm_role", DEFAULT_ARM_ROLE))
    extraction_dir = resolve_path(spec["extraction_dir"])
    manifest_path = resolve_path(spec.get("extraction_manifest", extraction_dir / "manifest.json"))
    contrast = spec.get("contrast")
    if not isinstance(contrast, dict):
        raise HeadSteeringError(f"spec {label!r} must define a single contrast mapping")
    targets = _parse_targets(spec.get("targets"))

    manifest = validate_head_manifest(manifest_path, roles=[arm_role])
    num_heads = int(manifest["num_attention_heads"])
    head_dim = int(manifest["head_dim"])
    layer_count, width = manifest["tensor_shapes"][arm_role]

    override_rows_path = spec.get("rows_path")
    rows_path = resolve_path(override_rows_path) if override_rows_path else None
    rows = load_extraction_rows(extraction_dir, rows_path=rows_path)

    positive_mask, negative_mask = contrast_masks(rows, arm=behavior_arm, contrast=contrast)
    positive_count = int(np.count_nonzero(positive_mask))
    negative_count = int(np.count_nonzero(negative_mask))
    min_rows = int(contrast.get("min_rows_per_group", 1))
    if positive_count < min_rows or negative_count < min_rows:
        raise HeadSteeringError(
            f"contrast {contrast.get('name')!r} has insufficient rows: "
            f"positive={positive_count}, negative={negative_count}, min={min_rows}"
        )

    cube = load_role_cube(extraction_dir, rows, role=arm_role, layer_count=layer_count, hidden_dim=width)

    direction_entries: list[dict[str, Any]] = []
    for layer, head in targets:
        if not (0 <= layer < layer_count):
            raise HeadSteeringError(f"target layer {layer} out of range [0, {layer_count})")
        if not (0 <= head < num_heads):
            raise HeadSteeringError(f"target head {head} out of range [0, {num_heads})")
        lo = head * head_dim
        hi = lo + head_dim
        head_matrix = cube[:, layer, lo:hi]
        result = head_direction(head_matrix, positive_mask=positive_mask, negative_mask=negative_mask)
        direction_entries.append(
            {
                "layer": layer,
                "head": head,
                "head_dim": head_dim,
                **result,
            }
        )

    output_dir = output_root / label
    artifact_path = output_dir / "steering_directions.json"
    artifact = {
        "artifact_type": ARTIFACT_TYPE,
        "notice": NOTICE,
        "label": label,
        "behavior_arm": behavior_arm,
        "arm_role": arm_role,
        "extraction_dir": repo_relative(extraction_dir),
        "extraction_manifest": repo_relative(manifest_path),
        "rows_path": repo_relative(rows_path) if rows_path is not None else repo_relative(extraction_dir / "rows.jsonl"),
        "num_attention_heads": num_heads,
        "head_dim": head_dim,
        "contrast": {
            "name": contrast.get("name"),
            "positive_label": contrast.get("positive_label", "positive"),
            "negative_label": contrast.get("negative_label", "negative"),
            "positive_count": positive_count,
            "negative_count": negative_count,
        },
        "steer_toward_positive": "alpha>0",
        "steer_toward_negative": "alpha<0",
        "directions": direction_entries,
    }
    write_json(artifact_path, artifact)
    return artifact


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    specs = config.get("steering_specs")
    if not isinstance(output, dict) or "root" not in output:
        raise HeadSteeringError("config must define output.root")
    if not isinstance(specs, list) or not specs:
        raise HeadSteeringError("config must define non-empty steering_specs")
    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(spec["extraction_dir"]) for spec in specs]
    validate_output_root(output_root, extraction_dirs)

    artifacts: list[dict[str, Any]] = []
    for spec in specs:
        artifacts.append(build_directions(spec, output_root=output_root))

    summary_path = output_root / "summary.json"
    summary = {
        "ok": True,
        "artifact_type": ARTIFACT_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "output_root": repo_relative(output_root),
        "spec_count": len(artifacts),
        "directions": {
            artifact["label"]: repo_relative(output_root / artifact["label"] / "steering_directions.json")
            for artifact in artifacts
        },
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
    except (HeadSteeringError, HeadLocalizationScanError, BehaviorAxisScanError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
