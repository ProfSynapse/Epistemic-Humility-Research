#!/usr/bin/env python3
"""Per-head behavior-axis localization scan over attention_head extractions.

Step A.3 of the ITI-grounded mechanism response (see
archive/notes/experiments/mech-interp-model-variation-panel.md). This is an offline CPU
analysis. It reads an ``attention_head``-granularity hidden-state extraction
(one concatenated o_proj-input vector per decoder block, width
``num_attention_heads * head_dim``) and measures how separable configured
behavior contrasts are at each INDIVIDUAL attention head, then ranks heads by
separability.

Where the residual-stream scan (phase3_behavior_axis_scan.py) reports one
mean-diff axis per block, this scan splits each block's vector into its per-head
slices in the natural concatenation order (head h occupies columns
``h*head_dim : (h+1)*head_dim``) and reports one axis per (block, head). The
top-ranked heads are the sparse localization/steering targets that ITI
(paper:2306.03341) intervenes on token-by-token during generation (Step A.4).

The metric primitives (mean-diff direction, projection, rank-AUC, Cohen's d,
balanced accuracy) and row/manifest loaders are imported from
phase3_behavior_axis_scan so the per-head numbers are computed identically to
the per-block numbers — only the matrix that goes into scan_layer differs.
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
    DEFAULT_ROLES,
    contrast_masks,
    load_config,
    load_extraction_rows,
    load_role_cube,
    scan_layer,
    write_csv,
    write_json,
)
from sae_smoke import (
    SaeSmokeError,
    load_json,
    repo_relative,
    resolve_path,
    validate_output_root,
)

ANALYSIS_TYPE = "phase3_head_localization_scan"
NOTICE = "HEAD_LOCALIZATION_SCAN_ONLY"


class HeadLocalizationScanError(RuntimeError):
    pass


def validate_head_manifest(path: Path, *, roles: list[str]) -> dict[str, Any]:
    """Same gates as the residual scan plus the attention_head head-layout fields.

    The role tensor_shapes width MUST equal num_attention_heads * head_dim (the
    o_proj input width, which differs from hidden_size under GQA); a mismatch
    means the extraction was not actually per-head and is rejected loudly.
    """
    if not path.is_file():
        raise HeadLocalizationScanError(f"missing extraction manifest: {repo_relative(path)}")
    manifest = load_json(path)
    if manifest.get("status") != "ok":
        raise HeadLocalizationScanError(f"{repo_relative(path)} status is not ok")
    if manifest.get("verified") is not True:
        raise HeadLocalizationScanError(f"{repo_relative(path)} verified is not true")
    if manifest.get("persistence_format") != "safetensors":
        raise HeadLocalizationScanError(f"{repo_relative(path)} persistence_format is not safetensors")
    if manifest.get("granularity") != "attention_head":
        raise HeadLocalizationScanError(
            f"{repo_relative(path)} granularity is {manifest.get('granularity')!r}, "
            "expected 'attention_head'"
        )
    num_heads = manifest.get("num_attention_heads")
    head_dim = manifest.get("head_dim")
    if not isinstance(num_heads, int) or num_heads <= 0:
        raise HeadLocalizationScanError(f"{repo_relative(path)} invalid num_attention_heads {num_heads!r}")
    if not isinstance(head_dim, int) or head_dim <= 0:
        raise HeadLocalizationScanError(f"{repo_relative(path)} invalid head_dim {head_dim!r}")
    tensor_shapes = manifest.get("tensor_shapes")
    if not isinstance(tensor_shapes, dict):
        raise HeadLocalizationScanError(f"{repo_relative(path)} missing tensor_shapes")
    expected_width = num_heads * head_dim
    for role in roles:
        shape = tensor_shapes.get(role)
        if not isinstance(shape, list) or len(shape) != 2 or not all(isinstance(v, int) for v in shape):
            raise HeadLocalizationScanError(f"{repo_relative(path)} missing valid tensor shape for role {role!r}")
        if shape[1] != expected_width:
            raise HeadLocalizationScanError(
                f"{repo_relative(path)} role {role!r} width {shape[1]} != "
                f"num_attention_heads * head_dim = {num_heads} * {head_dim} = {expected_width}; "
                "extraction is not per-head"
            )
    return manifest


def run_extraction(
    extraction: dict[str, Any],
    *,
    output_root: Path,
    analysis: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    label = extraction.get("label")
    if not isinstance(label, str) or not label:
        raise HeadLocalizationScanError("each extraction must define a non-empty label")
    behavior_arm = extraction.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise HeadLocalizationScanError(f"extraction {label!r} must define behavior_arm")
    extraction_dir = resolve_path(extraction["extraction_dir"])
    manifest_path = resolve_path(extraction.get("extraction_manifest", extraction_dir / "manifest.json"))
    roles = extraction.get("roles", analysis.get("roles", list(DEFAULT_ROLES)))
    if not isinstance(roles, list) or not roles:
        raise HeadLocalizationScanError(f"extraction {label!r} must define non-empty roles")
    roles = [str(role) for role in roles]
    contrasts = extraction.get("contrasts", analysis.get("contrasts"))
    if not isinstance(contrasts, list) or not contrasts:
        raise HeadLocalizationScanError(f"extraction {label!r} must define non-empty contrasts")

    manifest = validate_head_manifest(manifest_path, roles=roles)
    num_heads = int(manifest["num_attention_heads"])
    head_dim = int(manifest["head_dim"])

    override_rows_path = extraction.get("rows_path")
    rows_path = resolve_path(override_rows_path) if override_rows_path else None
    rows = load_extraction_rows(extraction_dir, rows_path=rows_path)

    all_rows: list[dict[str, Any]] = []
    contrast_summaries: list[dict[str, Any]] = []
    for role in roles:
        layer_count, width = manifest["tensor_shapes"][role]
        cube = load_role_cube(extraction_dir, rows, role=role, layer_count=layer_count, hidden_dim=width)
        for contrast in contrasts:
            name = contrast.get("name")
            if not isinstance(name, str) or not name:
                raise HeadLocalizationScanError("each contrast must define non-empty name")
            positive_mask, negative_mask = contrast_masks(rows, arm=behavior_arm, contrast=contrast)
            positive_count = int(np.count_nonzero(positive_mask))
            negative_count = int(np.count_nonzero(negative_mask))
            min_rows = int(contrast.get("min_rows_per_group", 1))
            summary = {
                "extraction_label": label,
                "behavior_arm": behavior_arm,
                "role": role,
                "contrast": name,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "min_rows_per_group": min_rows,
                "skipped": positive_count < min_rows or negative_count < min_rows,
            }
            if summary["skipped"]:
                summary["reason"] = "insufficient_rows"
                contrast_summaries.append(summary)
                continue
            for layer in range(layer_count):
                for head in range(num_heads):
                    lo = head * head_dim
                    hi = lo + head_dim
                    head_matrix = cube[:, layer, lo:hi]
                    metrics, _direction = scan_layer(
                        head_matrix, positive_mask=positive_mask, negative_mask=negative_mask
                    )
                    all_rows.append(
                        {
                            "analysis_type": ANALYSIS_TYPE,
                            "notice": NOTICE,
                            "extraction_label": label,
                            "behavior_arm": behavior_arm,
                            "role": role,
                            "layer": layer,
                            "head": head,
                            "contrast": name,
                            "positive_label": contrast.get("positive_label", "positive"),
                            "negative_label": contrast.get("negative_label", "negative"),
                            "positive_count": positive_count,
                            "negative_count": negative_count,
                            "head_dim": head_dim,
                            **metrics,
                        }
                    )
            contrast_summaries.append(summary)

    output_dir = output_root / label
    head_scan_path = output_dir / "head_scan.csv"
    summary_path = output_dir / "summary.json"
    top_path = output_dir / "top_heads.csv"
    top_rows = top_heads(all_rows)
    write_csv(head_scan_path, all_rows)
    write_csv(top_path, top_rows)
    summary = {
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "extraction_label": label,
        "behavior_arm": behavior_arm,
        "extraction_dir": repo_relative(extraction_dir),
        "extraction_manifest": repo_relative(manifest_path),
        "rows_path": repo_relative(rows_path) if rows_path is not None else repo_relative(extraction_dir / "rows.jsonl"),
        "row_count": len(rows),
        "roles": roles,
        "num_attention_heads": num_heads,
        "head_dim": head_dim,
        "contrast_summaries": contrast_summaries,
        "outputs": {
            "head_scan": repo_relative(head_scan_path),
            "top_heads": repo_relative(top_path),
            "summary": repo_relative(summary_path),
        },
    }
    write_json(summary_path, summary)
    return all_rows, summary


def top_heads(rows: list[dict[str, Any]], *, per_group: int = 20) -> list[dict[str, Any]]:
    """Rank (layer, head) axes within each (extraction, role, contrast) group.

    Sort key matches the residual scan's: |Cohen's d| first (effect size of the
    per-head projection separation), then AUC, then mean-diff norm. The top heads
    are the sparse steering targets for Step A.4.
    """
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["extraction_label"]), str(row["role"]), str(row["contrast"]))
        grouped.setdefault(key, []).append(row)
    top: list[dict[str, Any]] = []
    for key_rows in grouped.values():
        ranked = sorted(
            key_rows,
            key=lambda row: (abs(float(row["projection_cohen_d"])), float(row["auc"]), float(row["mean_diff_norm"])),
            reverse=True,
        )
        top.extend(ranked[:per_group])
    return top


def run_config(config_path: Path) -> dict[str, Any]:
    config = load_config(config_path)
    output = config.get("output")
    analysis = config.get("analysis", {})
    extractions = config.get("extractions")
    if not isinstance(output, dict) or "root" not in output:
        raise HeadLocalizationScanError("config must define output.root")
    if not isinstance(analysis, dict):
        raise HeadLocalizationScanError("analysis must be a mapping when provided")
    if not isinstance(extractions, list) or not extractions:
        raise HeadLocalizationScanError("config must define non-empty extractions")
    output_root = resolve_path(output["root"])
    extraction_dirs = [resolve_path(extraction["extraction_dir"]) for extraction in extractions]
    validate_output_root(output_root, extraction_dirs)

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for extraction in extractions:
        rows, summary = run_extraction(extraction, output_root=output_root, analysis=analysis)
        all_rows.extend(rows)
        summaries.append(summary)

    combined_path = output_root / "head_scan_all.csv"
    top_path = output_root / "top_heads_all.csv"
    summary_path = output_root / "summary.json"
    write_csv(combined_path, all_rows)
    write_csv(top_path, top_heads(all_rows))
    summary = {
        "ok": True,
        "analysis_type": ANALYSIS_TYPE,
        "notice": NOTICE,
        "config": repo_relative(config_path),
        "output_root": repo_relative(output_root),
        "extraction_count": len(summaries),
        "row_count": len(all_rows),
        "outputs": {
            "head_scan_all": repo_relative(combined_path),
            "top_heads_all": repo_relative(top_path),
            "summary": repo_relative(summary_path),
        },
        "extraction_summaries": [summary["outputs"]["summary"] for summary in summaries],
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
    except (HeadLocalizationScanError, BehaviorAxisScanError, SaeSmokeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
