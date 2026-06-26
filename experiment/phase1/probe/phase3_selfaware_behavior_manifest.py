#!/usr/bin/env python3
"""Build focused SelfAware behavior manifests from scored eval rows.

This is the bridge from a full SelfAware eval result to an extraction-ready
Phase 3 manifest. It selects exact row quotas by generated behavior cell and
writes:

- a `phase3-selfaware-frozen-row-manifest/v1` manifest for hidden-state extraction
- a row-key text file for replay/sweep selection
- selected scored rows for audit
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


PROBE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]


class SelfAwareBehaviorManifestError(RuntimeError):
    pass


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    if path.is_absolute():
        return path
    return (PROBE_DIR / path).resolve()


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    if not isinstance(config, dict):
        raise SelfAwareBehaviorManifestError("config must be a YAML mapping")
    return config


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise SelfAwareBehaviorManifestError(f"missing JSONL file: {rel(path)}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise SelfAwareBehaviorManifestError(f"{rel(path)}:{line_no} row is not an object")
            rows.append(row)
    return rows


def stable_row_key(row: dict[str, Any]) -> str:
    existing = row.get("row_key") or row.get("probe_pool_row_key")
    if isinstance(existing, str) and existing:
        return existing
    required = ["eval_set", "row_index", "id"]
    missing = [field for field in required if field not in row]
    if missing:
        raise SelfAwareBehaviorManifestError(f"row missing identity field(s): {missing}")
    return f"selfaware::{row['eval_set']}::{int(row['row_index']):06d}::{row['id']}"


def behavior_cell(row: dict[str, Any]) -> str:
    label = row.get("label")
    refused = bool(row.get("refused"))
    correct = bool(row.get("correct"))
    if label == "known":
        if refused:
            return "known_refused"
        if correct:
            return "known_correct_answered"
        return "known_answered_wrong"
    if label == "unknown":
        if refused:
            return "unknown_refused"
        if correct:
            return "unknown_answered_correct"
        return "unknown_answered_wrong"
    raise SelfAwareBehaviorManifestError(f"unsupported row label {label!r}")


def stable_tiebreak(seed: int, key: str) -> str:
    return hashlib.sha256(f"{seed}|{key}".encode("utf-8")).hexdigest()


def sort_key(row: dict[str, Any], seed: int) -> tuple:
    key = stable_row_key(row)
    # Preserve broad dataset order first so the panel remains interpretable by
    # SelfAware row index, then use seed as a deterministic tie-break.
    return (
        str(row.get("source") or ""),
        str(row.get("eval_set") or ""),
        int(row.get("row_index", 0)),
        stable_tiebreak(seed, key),
    )


def source_arm_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer_text": row.get("answer_text"),
        "generated_answer": row.get("generated_answer"),
        "refused": bool(row.get("refused")),
        "correct": bool(row.get("correct")),
        "truthful": bool(row.get("truthful")),
        "stated_confidence": row.get("stated_confidence"),
        "behavior_cell": behavior_cell(row),
        "config_sha": row.get("config_sha"),
        "method": row.get("method"),
        "model": row.get("model"),
        "enable_thinking": row.get("enable_thinking"),
        "generation_attempts": row.get("generation_attempts"),
        "stated_confidence_retry_count": row.get("stated_confidence_retry_count"),
        "stated_confidence_retry_exhausted": row.get("stated_confidence_retry_exhausted"),
    }


def manifest_row(row: dict[str, Any], behavior_arm: str, strata_prefix: str | None) -> dict[str, Any]:
    key = stable_row_key(row)
    cell = behavior_cell(row)
    source = row.get("source") or "selfaware"
    eval_set = row.get("eval_set") or "selfaware"
    row_index = int(row["row_index"])
    row_id = row["id"]
    strata = [cell]
    if strata_prefix:
        strata.insert(0, f"{strata_prefix}_{cell}")
    return {
        "aliases": row.get("aliases") or [],
        "answer_value": row.get("answer_value"),
        "label": row["label"],
        "prompt": row["question"],
        "question": row["question"],
        "row_key": key,
        "source_arms": {behavior_arm: source_arm_payload(row)},
        "stable_identity": {
            "eval_set": eval_set,
            "id": row_id,
            "row_index": row_index,
            "source": source,
        },
        "strata": strata,
    }


def select_rows(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inputs = config.get("inputs", {})
    if not isinstance(inputs, dict) or not isinstance(inputs.get("scored_rows"), str):
        raise SelfAwareBehaviorManifestError("config must define inputs.scored_rows")
    behavior_arm = config.get("behavior_arm")
    if not isinstance(behavior_arm, str) or not behavior_arm:
        raise SelfAwareBehaviorManifestError("config must define behavior_arm")
    quotas = config.get("quotas")
    if not isinstance(quotas, dict) or not quotas:
        raise SelfAwareBehaviorManifestError("config must define quotas")
    require_quotas = bool(config.get("require_quotas", True))
    seed = int(config.get("sampling", {}).get("seed", 20260625))

    scored_path = resolve_path(inputs["scored_rows"])
    buckets: dict[str, list[dict[str, Any]]] = {str(cell): [] for cell in quotas}
    all_counts: Counter[str] = Counter()
    for row in load_jsonl(scored_path):
        cell = behavior_cell(row)
        all_counts[cell] += 1
        if cell in buckets:
            buckets[cell].append(row)
    for bucket_rows in buckets.values():
        bucket_rows.sort(key=lambda row: sort_key(row, seed))

    selected_scored: list[dict[str, Any]] = []
    bucket_summaries: dict[str, dict[str, int]] = {}
    for cell, quota_raw in quotas.items():
        if not isinstance(quota_raw, int) or isinstance(quota_raw, bool) or quota_raw < 0:
            raise SelfAwareBehaviorManifestError(f"quota for {cell!r} must be a non-negative integer")
        available = buckets.get(str(cell), [])
        if require_quotas and len(available) < quota_raw:
            raise SelfAwareBehaviorManifestError(
                f"cell {cell!r} has {len(available)} rows, quota is {quota_raw}"
            )
        take = available[:quota_raw]
        selected_scored.extend({**row, "target_behavior_cell": str(cell)} for row in take)
        bucket_summaries[str(cell)] = {
            "available": len(available),
            "selected": len(take),
            "quota": quota_raw,
        }

    seen: set[str] = set()
    selected_manifest_rows: list[dict[str, Any]] = []
    selected_behavior_counts: Counter[str] = Counter()
    selected_label_counts: Counter[str] = Counter()
    strata_prefix = config.get("strata_prefix")
    if strata_prefix is not None and not isinstance(strata_prefix, str):
        raise SelfAwareBehaviorManifestError("strata_prefix must be a string when set")
    for row in selected_scored:
        key = stable_row_key(row)
        if key in seen:
            raise SelfAwareBehaviorManifestError(f"duplicate selected row key: {key}")
        seen.add(key)
        selected_manifest_rows.append(manifest_row(row, behavior_arm, strata_prefix))
        selected_behavior_counts[behavior_cell(row)] += 1
        selected_label_counts[str(row.get("label"))] += 1

    manifest = {
        "schema_version": "phase3-selfaware-frozen-row-manifest/v1",
        "created_by": "experiment/phase1/probe/phase3_selfaware_behavior_manifest.py",
        "purpose": config.get("purpose"),
        "behavior_arm": behavior_arm,
        "scope": {"not_probe_pool_runner_ready": True},
        "identity": {
            "row_key_format": "selfaware::<eval_set>::<zero_padded_row_index>::<raw_id>",
            "required_identity_fields": ["eval_set", "row_index", "id", "question", "label", "source"],
        },
        "inputs": {
            "scored_rows": rel(scored_path),
            "scored_rows_sha256": file_sha256(scored_path),
        },
        "sampling": {"seed": seed},
        "quotas": quotas,
        "source_behavior_cell_counts": dict(sorted(all_counts.items())),
        "bucket_summaries": bucket_summaries,
        "selected_behavior_cell_counts": dict(sorted(selected_behavior_counts.items())),
        "selected_label_counts": dict(sorted(selected_label_counts.items())),
        "row_count": len(selected_manifest_rows),
        "rows": selected_manifest_rows,
    }
    return selected_scored, manifest


def write_outputs(
    config: dict[str, Any],
    selected_scored: list[dict[str, Any]],
    manifest: dict[str, Any],
) -> tuple[Path, Path, Path, Path]:
    output = config.get("output", {})
    for key in ("manifest", "row_keys_file", "selected_scored_rows", "summary"):
        if not isinstance(output.get(key), str):
            raise SelfAwareBehaviorManifestError(f"config must define output.{key}")
    manifest_path = resolve_path(output["manifest"])
    row_keys_path = resolve_path(output["row_keys_file"])
    selected_rows_path = resolve_path(output["selected_scored_rows"])
    summary_path = resolve_path(output["summary"])
    for path in (manifest_path, row_keys_path, selected_rows_path, summary_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    row_keys_path.write_text(
        "".join(f"{row['row_key']}\n" for row in manifest["rows"]),
        encoding="utf-8",
    )
    with selected_rows_path.open("w", encoding="utf-8") as fh:
        for row in selected_scored:
            enriched = {**row, "row_key": stable_row_key(row), "behavior_cell": behavior_cell(row)}
            fh.write(json.dumps(enriched, sort_keys=True) + "\n")
    summary = {
        key: value
        for key, value in manifest.items()
        if key != "rows"
    }
    summary["outputs"] = {
        "manifest": rel(manifest_path),
        "row_keys_file": rel(row_keys_path),
        "selected_scored_rows": rel(selected_rows_path),
        "summary": rel(summary_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path, row_keys_path, selected_rows_path, summary_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args(argv)
    config = load_config(args.config)
    selected_scored, manifest = select_rows(config)
    manifest_path, row_keys_path, rows_path, summary_path = write_outputs(config, selected_scored, manifest)
    print(f"selected {manifest['row_count']} SelfAware rows")
    print(f"wrote {rel(manifest_path)}")
    print(f"wrote {rel(row_keys_path)}")
    print(f"wrote {rel(rows_path)}")
    print(f"wrote {rel(summary_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
