#!/usr/bin/env python3
"""Analyze trained mechinterp SAE features against behavior labels.

This is an exploratory feature screen. It ranks learned SAE features by their
separation between behavior-defined row groups, such as unknown rows where a
target arm refused versus unknown rows where it answered.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from sae_feature_analysis import (
    compute_codes,
    hidden_dim_from_manifest,
    load_selected_rows,
)
from sae_smoke import (
    SaeSmokeError,
    load_hidden_matrix,
    repo_relative,
    resolve_path,
)


NOTICE = "SAE_BEHAVIOR_FEATURE_ANALYSIS_ONLY"
ANALYSIS_TYPE = "mechinterp_sae_behavior_feature_analysis"


class SaeBehaviorFeatureAnalysisError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise SaeBehaviorFeatureAnalysisError(f"{path} did not load to a JSON object")
    return payload


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        payload = yaml.safe_load(fh)
    if not isinstance(payload, dict):
        raise SaeBehaviorFeatureAnalysisError(f"{path} did not load to a YAML object")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def row_arm(row: dict[str, Any], arm: str) -> dict[str, Any]:
    source_arms = row.get("source_arms")
    if not isinstance(source_arms, dict):
        raise SaeBehaviorFeatureAnalysisError(f"row {row.get('row_key')} missing source_arms")
    payload = source_arms.get(arm)
    if not isinstance(payload, dict):
        raise SaeBehaviorFeatureAnalysisError(f"row {row.get('row_key')} missing source arm {arm!r}")
    return payload


def _matches_value(actual: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def row_matches_filter(row: dict[str, Any], arm: str, row_filter: dict[str, Any]) -> bool:
    if "label" in row_filter and not _matches_value(row.get("label"), row_filter["label"]):
        return False
    strata = row.get("strata", [])
    if not isinstance(strata, list):
        strata = []
    strata_any = row_filter.get("strata_any")
    if strata_any is not None and not any(value in strata for value in strata_any):
        return False
    strata_all = row_filter.get("strata_all")
    if strata_all is not None and not all(value in strata for value in strata_all):
        return False

    arm_payload = row_arm(row, arm)
    for key in ("refused", "correct", "truthful", "wrong_hint_match"):
        if key in row_filter and not _matches_value(bool(arm_payload.get(key)), row_filter[key]):
            return False
    confidence = arm_payload.get("stated_confidence")
    if "confidence_min" in row_filter:
        if confidence is None or float(confidence) < float(row_filter["confidence_min"]):
            return False
    if "confidence_max" in row_filter:
        if confidence is None or float(confidence) > float(row_filter["confidence_max"]):
            return False
    return True


def contrast_masks(
    rows: list[dict[str, Any]],
    *,
    arm: str,
    contrast: dict[str, Any],
) -> tuple[np.ndarray, np.ndarray]:
    positive = contrast.get("positive")
    negative = contrast.get("negative")
    if not isinstance(positive, dict) or not isinstance(negative, dict):
        raise SaeBehaviorFeatureAnalysisError(f"contrast {contrast.get('name')} must define filters")
    positive_mask = np.array([row_matches_filter(row, arm, positive) for row in rows], dtype=bool)
    negative_mask = np.array([row_matches_filter(row, arm, negative) for row in rows], dtype=bool)
    overlap = positive_mask & negative_mask
    if bool(np.any(overlap)):
        raise SaeBehaviorFeatureAnalysisError(f"contrast {contrast.get('name')} filters overlap")
    return positive_mask, negative_mask


def effect_rows(
    codes: np.ndarray,
    rows: list[dict[str, Any]],
    *,
    arm: str,
    feature_index: int,
    mask: np.ndarray,
    limit: int,
) -> list[dict[str, Any]]:
    selected_indices = np.flatnonzero(mask)
    order = selected_indices[np.argsort(-codes[selected_indices, feature_index])[:limit]]
    examples: list[dict[str, Any]] = []
    for row_index in order:
        row = rows[int(row_index)]
        arm_payload = row_arm(row, arm)
        examples.append(
            {
                "row_key": row["row_key"],
                "label": row["label"],
                "activation": float(codes[int(row_index), feature_index]),
                "question": row.get("question"),
                "strata": row.get("strata", []),
                "answer_text": arm_payload.get("answer_text"),
                "refused": bool(arm_payload.get("refused")),
                "correct": bool(arm_payload.get("correct")),
                "truthful": bool(arm_payload.get("truthful")),
                "stated_confidence": arm_payload.get("stated_confidence"),
            }
        )
    return examples


def rank_features_for_contrast(
    codes: np.ndarray,
    rows: list[dict[str, Any]],
    *,
    arm: str,
    contrast: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any], np.ndarray, np.ndarray]:
    name = contrast.get("name")
    if not isinstance(name, str) or not name:
        raise SaeBehaviorFeatureAnalysisError("each contrast must define non-empty name")
    positive_mask, negative_mask = contrast_masks(rows, arm=arm, contrast=contrast)
    positive_count = int(np.count_nonzero(positive_mask))
    negative_count = int(np.count_nonzero(negative_mask))
    min_rows = int(contrast.get("min_rows_per_group", 1))
    group_counts = {
        "contrast": name,
        "arm": arm,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "min_rows_per_group": min_rows,
    }
    if positive_count < min_rows or negative_count < min_rows:
        return [], {**group_counts, "skipped": True, "reason": "insufficient_rows"}, positive_mask, negative_mask

    ranked: list[dict[str, Any]] = []
    for feature in range(codes.shape[1]):
        values = codes[:, feature]
        positive_values = values[positive_mask]
        negative_values = values[negative_mask]
        positive_mean = float(np.mean(positive_values))
        negative_mean = float(np.mean(negative_values))
        positive_std = float(np.std(positive_values))
        negative_std = float(np.std(negative_values))
        pooled = float(np.sqrt((positive_std**2 + negative_std**2) / 2.0))
        mean_diff = positive_mean - negative_mean
        effect = float(mean_diff / pooled) if pooled > 1e-12 else 0.0
        positive_freq = float(np.mean(positive_values > 0.0))
        negative_freq = float(np.mean(negative_values > 0.0))
        ranked.append(
            {
                "contrast": name,
                "arm": arm,
                "feature": feature,
                "positive_label": contrast.get("positive_label", "positive"),
                "negative_label": contrast.get("negative_label", "negative"),
                "positive_count": positive_count,
                "negative_count": negative_count,
                "positive_mean": positive_mean,
                "negative_mean": negative_mean,
                "mean_diff_positive_minus_negative": float(mean_diff),
                "abs_mean_diff": float(abs(mean_diff)),
                "cohen_d_positive_minus_negative": effect,
                "abs_cohen_d": float(abs(effect)),
                "positive_activation_frequency": positive_freq,
                "negative_activation_frequency": negative_freq,
                "frequency_diff_positive_minus_negative": float(positive_freq - negative_freq),
                "active_count": int(np.count_nonzero(values > 0.0)),
                "max_activation": float(np.max(values)),
            }
        )
    ranked = sorted(ranked, key=lambda item: (item["abs_cohen_d"], item["abs_mean_diff"]), reverse=True)
    return ranked, {**group_counts, "skipped": False}, positive_mask, negative_mask


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def run_candidate(candidate: dict[str, Any], *, output_root: Path, analysis: dict[str, Any]) -> dict[str, Any]:
    run_dir = resolve_path(candidate["run_dir"])
    manifest = load_json(run_dir / "run_manifest.json")
    source = manifest["candidate"]
    training = manifest["training"]
    extraction_dir = resolve_path(source["extraction_dir"])
    extraction_manifest = resolve_path(source["extraction_manifest"])
    rows = load_selected_rows(run_dir, extraction_dir)
    hidden_dim = hidden_dim_from_manifest(extraction_manifest, str(source["role"]))
    x = load_hidden_matrix(
        {
            "extraction_dir": source["extraction_dir"],
            "role": source["role"],
            "layer": source["layer"],
            "hidden_dim": hidden_dim,
        },
        rows,
    )
    codes = compute_codes(x, run_dir / "sae_weights.safetensors", training)
    label = candidate.get("label") or source["label"]
    arm = candidate.get("behavior_arm")
    if not isinstance(arm, str) or not arm:
        raise SaeBehaviorFeatureAnalysisError(f"candidate {label!r} must define behavior_arm")
    contrasts = candidate.get("contrasts", analysis.get("contrasts"))
    if not isinstance(contrasts, list) or not contrasts:
        raise SaeBehaviorFeatureAnalysisError(f"candidate {label!r} must define non-empty contrasts")

    candidate_out = output_root / label
    top_n = int(analysis.get("top_features", 20))
    top_rows_per_group = int(analysis.get("top_rows_per_group", 5))
    all_ranked: list[dict[str, Any]] = []
    contrast_summaries: list[dict[str, Any]] = []
    examples: dict[str, Any] = {}

    for contrast in contrasts:
        ranked, contrast_summary, positive_mask, negative_mask = rank_features_for_contrast(
            codes, rows, arm=arm, contrast=contrast
        )
        contrast_summaries.append(contrast_summary)
        all_ranked.extend(ranked)
        if not ranked:
            continue
        name = str(contrast["name"])
        examples[name] = {}
        for item in ranked[:top_n]:
            feature = int(item["feature"])
            examples[name][str(feature)] = {
                "positive": effect_rows(
                    codes,
                    rows,
                    arm=arm,
                    feature_index=feature,
                    mask=positive_mask,
                    limit=top_rows_per_group,
                ),
                "negative": effect_rows(
                    codes,
                    rows,
                    arm=arm,
                    feature_index=feature,
                    mask=negative_mask,
                    limit=top_rows_per_group,
                ),
            }

    ranked_path = candidate_out / "behavior_feature_rankings.csv"
    examples_path = candidate_out / "top_behavior_feature_examples.json"
    summary_path = candidate_out / "summary.json"
    write_csv(ranked_path, all_ranked)
    write_json(examples_path, {"notice": NOTICE, "top_behavior_feature_examples": examples})
    top_by_contrast = {
        summary["contrast"]: [
            row for row in all_ranked if row["contrast"] == summary["contrast"]
        ][:top_n]
        for summary in contrast_summaries
        if not summary.get("skipped")
    }
    summary = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "candidate_label": label,
        "behavior_arm": arm,
        "source_run_manifest": repo_relative(run_dir / "run_manifest.json"),
        "row_count": len(rows),
        "dictionary_size": int(codes.shape[1]),
        "activation": training.get("activation"),
        "top_k": training.get("top_k"),
        "mean_active_features": float(np.mean(np.count_nonzero(codes > 0.0, axis=1))),
        "contrast_summaries": contrast_summaries,
        "top_by_contrast": top_by_contrast,
        "outputs": {
            "behavior_feature_rankings": repo_relative(ranked_path),
            "top_behavior_feature_examples": repo_relative(examples_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return summary


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    candidates = config.get("candidate_runs")
    analysis = config.get("analysis", {})
    if not isinstance(output, dict) or "root" not in output:
        raise SaeBehaviorFeatureAnalysisError("config must define output.root")
    if not isinstance(candidates, list) or not candidates:
        raise SaeBehaviorFeatureAnalysisError("config must define non-empty candidate_runs")
    if not isinstance(analysis, dict):
        raise SaeBehaviorFeatureAnalysisError("analysis must be a mapping when provided")
    output_root = resolve_path(output["root"])
    summaries = [run_candidate(candidate, output_root=output_root, analysis=analysis) for candidate in candidates]
    return {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "output_root": repo_relative(output_root),
        "candidate_count": len(summaries),
        "summaries": [summary["outputs"]["summary"] for summary in summaries],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_config(resolve_path(args.config))
    except (SaeBehaviorFeatureAnalysisError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
