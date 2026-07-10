#!/usr/bin/env python3
"""Export selected SAE features as Phase 3 direction candidates.

The SAE was trained on standardized hidden states. This script converts selected
decoder columns back into raw hidden-state space so the existing causal/logit
diagnostic runner can test them as exploratory directions.
"""

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

from sae_smoke import repo_relative, resolve_path

try:
    from safetensors.torch import load_file as load_torch_safetensors
    from safetensors.numpy import save_file as save_numpy_safetensors
except ImportError as exc:  # pragma: no cover
    load_torch_safetensors = None
    save_numpy_safetensors = None
    SAFETENSORS_IMPORT_ERROR = exc
else:
    SAFETENSORS_IMPORT_ERROR = None


NOTICE = "SAE_FEATURE_DIRECTION_CANDIDATES_ONLY"
ANALYSIS_TYPE = "phase3_sae_feature_direction_export"
TENSOR_KEY = "direction"


class SaeFeatureDirectionError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureDirectionError(f"{path} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeFeatureDirectionError(f"{path} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_feature_rankings(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            parsed = dict(row)
            for key, value in list(parsed.items()):
                if value in (None, ""):
                    continue
                if key == "feature":
                    parsed[key] = int(parsed[key])
                elif key.endswith("_count") or key == "active_count":
                    parsed[key] = int(parsed[key])
                else:
                    try:
                        parsed[key] = float(parsed[key])
                    except ValueError:
                        pass
            if "feature" not in parsed:
                raise SaeFeatureDirectionError(f"{repo_relative(path)} row missing feature")
            if "mean_diff_unknown_minus_known" not in parsed and "mean_diff_positive_minus_negative" not in parsed:
                raise SaeFeatureDirectionError(
                    f"{repo_relative(path)} must include mean_diff_unknown_minus_known "
                    "or mean_diff_positive_minus_negative"
                )
            if "abs_cohen_d" in parsed:
                parsed["abs_cohen_d"] = float(parsed["abs_cohen_d"])
            elif "cohen_d_positive_minus_negative" in parsed:
                parsed["abs_cohen_d"] = abs(float(parsed["cohen_d_positive_minus_negative"]))
            else:
                raise SaeFeatureDirectionError(f"{repo_relative(path)} row missing effect-size field")
            for key in (
                "known_mean",
                "unknown_mean",
                "mean_diff_unknown_minus_known",
                "known_activation_frequency",
                "unknown_activation_frequency",
            ):
                if key in parsed:
                    parsed[key] = float(parsed[key])
            rows.append(parsed)
    return rows


def ranking_signed_diff(row: dict[str, Any]) -> float:
    if "mean_diff_unknown_minus_known" in row:
        return float(row["mean_diff_unknown_minus_known"])
    return float(row["mean_diff_positive_minus_negative"])


def ranking_skew_label(row: dict[str, Any]) -> str:
    signed = ranking_signed_diff(row)
    if "mean_diff_unknown_minus_known" in row:
        return "unknown" if signed > 0.0 else "known"
    if signed > 0.0:
        return str(row.get("positive_label", "positive"))
    return str(row.get("negative_label", "negative"))


def select_features(rankings: list[dict[str, Any]], selection: dict[str, Any]) -> list[dict[str, Any]]:
    explicit = selection.get("features")
    if explicit is not None:
        wanted = {int(value) for value in explicit}
        selected_by_feature: dict[int, dict[str, Any]] = {}
        for row in rankings:
            feature = int(row["feature"])
            if feature not in wanted:
                continue
            current = selected_by_feature.get(feature)
            if current is None or (
                float(row.get("abs_cohen_d", 0.0)),
                abs(ranking_signed_diff(row)),
            ) > (
                float(current.get("abs_cohen_d", 0.0)),
                abs(ranking_signed_diff(current)),
            ):
                selected_by_feature[feature] = row
        selected = [selected_by_feature[feature] for feature in sorted(selected_by_feature)]
        missing = sorted(wanted - {int(row["feature"]) for row in selected})
        if missing:
            raise SaeFeatureDirectionError(f"feature_rankings.csv missing requested features {missing}")
        return selected

    top_per_sign = int(selection.get("top_per_sign", 1))
    if top_per_sign <= 0:
        raise SaeFeatureDirectionError("selection.top_per_sign must be positive")
    unknown_skewed = [row for row in rankings if ranking_signed_diff(row) > 0.0]
    known_skewed = [row for row in rankings if ranking_signed_diff(row) < 0.0]
    return unknown_skewed[:top_per_sign] + known_skewed[:top_per_sign]


def vector_sha256(vector: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(vector.astype(np.float32))
    return hashlib.sha256(contiguous.tobytes()).hexdigest()


def load_raw_decoder_directions(weights_path: Path) -> np.ndarray:
    if load_torch_safetensors is None:
        raise SaeFeatureDirectionError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
    tensors = load_torch_safetensors(str(weights_path))
    required = ["decoder.weight", "normalization.scale"]
    missing = [key for key in required if key not in tensors]
    if missing:
        raise SaeFeatureDirectionError(f"{repo_relative(weights_path)} missing tensors {missing}")
    decoder_weight = tensors["decoder.weight"].detach().cpu().numpy().astype(np.float32)
    scale = tensors["normalization.scale"].detach().cpu().numpy().astype(np.float32)
    if decoder_weight.ndim != 2:
        raise SaeFeatureDirectionError("decoder.weight must be 2D")
    if scale.ndim != 1 or scale.shape[0] != decoder_weight.shape[0]:
        raise SaeFeatureDirectionError("normalization.scale shape does not match decoder hidden dimension")
    return (decoder_weight * scale[:, None]).astype(np.float32)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def direction_id(label: str, feature: int, sha: str) -> str:
    safe_label = "".join(ch if ch.isalnum() else "_" for ch in label).strip("_")
    return f"sae_feature__{safe_label}__f{feature:03d}__{sha[:12]}"


def run_candidate(
    candidate: dict[str, Any],
    *,
    output_root: Path,
    default_selection: dict[str, Any],
) -> list[dict[str, Any]]:
    summary_path = resolve_path(candidate["summary"])
    summary = load_json(summary_path)
    run_manifest_path = resolve_path(summary["source_run_manifest"])
    run_manifest = load_json(run_manifest_path)
    run_dir = run_manifest_path.parent
    weights_path = resolve_path(run_manifest["outputs"]["weights"])
    summary_outputs = summary["outputs"]
    rankings_text = summary_outputs.get("feature_rankings") or summary_outputs.get("behavior_feature_rankings")
    if not isinstance(rankings_text, str) or not rankings_text:
        raise SaeFeatureDirectionError(
            f"{repo_relative(summary_path)} outputs must include feature_rankings or behavior_feature_rankings"
        )
    rankings_path = resolve_path(rankings_text)
    rankings = load_feature_rankings(rankings_path)
    candidate_selection = candidate.get("selection", default_selection)
    if not isinstance(candidate_selection, dict):
        raise SaeFeatureDirectionError(f"candidate {candidate.get('label')} selection must be a mapping")
    selected = select_features(rankings, candidate_selection)
    raw_decoder = load_raw_decoder_directions(weights_path)

    label = str(candidate.get("label") or summary["candidate_label"])
    candidate_out = output_root / label
    directions_dir = candidate_out / "directions"
    records: list[dict[str, Any]] = []
    for feature_row in selected:
        feature = int(feature_row["feature"])
        if feature < 0 or feature >= raw_decoder.shape[1]:
            raise SaeFeatureDirectionError(f"feature {feature} outside dictionary size {raw_decoder.shape[1]}")
        vector = raw_decoder[:, feature].astype(np.float32)
        sha = vector_sha256(vector)
        did = direction_id(label, feature, sha)
        vector_path = directions_dir / f"{did}.safetensors"
        vector_path.parent.mkdir(parents=True, exist_ok=True)
        if save_numpy_safetensors is None:
            raise SaeFeatureDirectionError(f"safetensors is required: {SAFETENSORS_IMPORT_ERROR}")
        save_numpy_safetensors({TENSOR_KEY: vector}, str(vector_path))

        mean_diff = ranking_signed_diff(feature_row)
        skew_label = ranking_skew_label(feature_row)
        record = {
            "direction_id": did,
            "candidate_label": label,
            "feature": feature,
            "status": "ok",
            "role": run_manifest["candidate"]["role"],
            "layer": int(run_manifest["candidate"]["layer"]),
            "hidden_dim": int(vector.shape[0]),
            "norm": float(np.linalg.norm(vector)),
            "unit_norm": float(np.linalg.norm(vector / max(float(np.linalg.norm(vector)), 1e-12))),
            "vector_sha256": sha,
            "tensor_key": TENSOR_KEY,
            "vector_file": repo_relative(vector_path),
            "notice": NOTICE,
            "analysis_type": ANALYSIS_TYPE,
            "method": "sae_decoder_feature_raw_hidden_direction",
            "direction_space": "raw_hidden_decoder_column_times_training_scale",
            "source_run_manifest": repo_relative(run_manifest_path),
            "source_feature_summary": repo_relative(summary_path),
            "source_feature_rankings": repo_relative(rankings_path),
            "feature_skew_label": skew_label,
            "signed_mean_diff": mean_diff,
            "abs_cohen_d": float(feature_row["abs_cohen_d"]),
        }
        if "mean_diff_unknown_minus_known" in feature_row:
            record["mean_diff_unknown_minus_known"] = mean_diff
        for key in (
            "known_activation_frequency",
            "unknown_activation_frequency",
            "positive_activation_frequency",
            "negative_activation_frequency",
            "contrast",
            "arm",
            "positive_label",
            "negative_label",
            "positive_count",
            "negative_count",
            "mean_diff_positive_minus_negative",
            "cohen_d_positive_minus_negative",
        ):
            if key in feature_row:
                record[key] = feature_row[key]
        records.append(record)
    write_csv(candidate_out / "sae_feature_directions.csv", records)
    write_json(
        candidate_out / "sae_feature_directions.manifest.json",
        {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "candidate_label": label,
            "source_run_manifest": repo_relative(run_manifest_path),
            "source_feature_summary": repo_relative(summary_path),
            "direction_count": len(records),
            "directions": records,
        },
    )
    return records


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    candidates = config.get("candidate_analyses")
    selection = config.get("selection", {})
    if not isinstance(output, dict) or "root" not in output:
        raise SaeFeatureDirectionError("config must define output.root")
    if not isinstance(candidates, list) or not candidates:
        raise SaeFeatureDirectionError("config must define non-empty candidate_analyses")
    if not isinstance(selection, dict):
        raise SaeFeatureDirectionError("selection must be a mapping when provided")

    output_root = resolve_path(output["root"])
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        records.extend(run_candidate(candidate, output_root=output_root, default_selection=selection))
    manifest_path = output_root / "sae_feature_directions.manifest.json"
    csv_path = output_root / "sae_feature_directions.csv"
    write_csv(csv_path, records)
    write_json(
        manifest_path,
        {
            "analysis_type": ANALYSIS_TYPE,
            "notice": NOTICE,
            "config": repo_relative(config_path),
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
    except SaeFeatureDirectionError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
