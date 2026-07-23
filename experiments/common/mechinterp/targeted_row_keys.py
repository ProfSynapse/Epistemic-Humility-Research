#!/usr/bin/env python3
"""Build exact row-key panels for targeted mechinterp hidden-state extraction.

The script reads the frozen probe pool and probe_results.jsonl, assigns rows to
simple heuristic buckets, and writes one exact row-key file plus a provenance
manifest. It does not run model inference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"

REFUSAL_PATTERNS = [
    r"\bi don't know\b",
    r"\bi do not know\b",
    r"\bnot sure\b",
    r"\bnot enough information\b",
    r"\bcannot determine\b",
    r"\bcan't determine\b",
    r"\bnot widely recognized\b",
    r"\bno definitive\b",
    r"\bunknown\b",
    r"\bno record\b",
    r"\bnot available\b",
    r"\bunclear\b",
    r"\bi can't answer\b",
    r"\bi cannot answer\b",
    r"\bit is difficult to\b",
    r"\bthere is no\b",
    r"\bdoes not appear\b",
]
REFUSAL_RE = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
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
        raise ValueError("config must be a mapping")
    return config


def load_frozen_labels(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    labels: dict[str, str] = {}
    for key in payload.get("known_question_keys", []):
        labels[str(key)] = "known"
    for key in payload.get("unknown_question_keys", []):
        labels[str(key)] = "unknown"
    return labels


def read_excluded_keys(paths: list[str]) -> set[str]:
    excluded: set[str] = set()
    for raw in paths:
        path = resolve_path(raw)
        if not path.exists():
            raise FileNotFoundError(f"exclude row-key source missing: {rel(path)}")
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("{"):
                row = json.loads(line)
                key = row.get("probe_pool_row_key") or row.get("row_key")
                if key:
                    excluded.add(str(key))
            else:
                excluded.add(line)
    return excluded


def is_refusal_like(answer: str) -> bool:
    return bool(REFUSAL_RE.search(answer or ""))


def stable_tiebreak(seed: int, key: str) -> str:
    return hashlib.sha256(f"{seed}|{key}".encode("utf-8")).hexdigest()


def row_float(row: dict[str, Any], field: str, default: float = 0.0) -> float:
    value = row.get(field, default)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def classify_row(row: dict[str, Any]) -> str | None:
    label = row.get("frozen_label") or row.get("label")
    answer = str(row.get("greedy_answer") or "")
    refusal_like = is_refusal_like(answer)
    p_correct = row_float(row, "p_correct")
    greedy_correct = bool(row.get("greedy_correct"))
    if label == "known":
        if refusal_like or p_correct < 1.0 or not greedy_correct:
            return "known_low_confidence_or_refusal"
        return "known_high_confidence_correct"
    if label == "unknown":
        if refusal_like:
            return "unknown_refusal_like"
        return "unknown_answered_wrong_like"
    return None


def sort_key_for_bucket(bucket: str, row: dict[str, Any], seed: int) -> tuple:
    key = str(row["probe_pool_row_key"])
    p_correct = row_float(row, "p_correct")
    greedy_correct = bool(row.get("greedy_correct"))
    answer = str(row.get("greedy_answer") or "")
    refusal_like = is_refusal_like(answer)
    tie = stable_tiebreak(seed, key)
    if bucket == "known_low_confidence_or_refusal":
        return (not refusal_like, p_correct, greedy_correct, tie)
    if bucket == "known_high_confidence_correct":
        return (-p_correct, refusal_like, tie)
    if bucket == "unknown_refusal_like":
        return (p_correct, -len(answer), tie)
    if bucket == "unknown_answered_wrong_like":
        return (p_correct, len(answer) == 0, tie)
    return (tie,)


def load_probe_rows(
    *,
    results_path: Path,
    frozen_labels: dict[str, str],
    expected_probe_config_sha: str | None,
    excluded: set[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with results_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if not key or key not in frozen_labels or key in excluded:
                continue
            if expected_probe_config_sha and row.get("probe_config_sha") != expected_probe_config_sha:
                raise ValueError(
                    f"{rel(results_path)}:{line_no} probe_config_sha "
                    f"{row.get('probe_config_sha')!r} did not match "
                    f"{expected_probe_config_sha!r}"
                )
            if row.get("label") == "discard":
                continue
            rows.append({**row, "frozen_label": frozen_labels[key]})
    return rows


def select_rows(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inputs = config["inputs"]
    sampling = config.get("sampling", {})
    seed = int(sampling.get("seed", 20260620))
    frozen_path = resolve_path(inputs["questions_frozen"])
    results_path = resolve_path(inputs["probe_results"])
    excluded = read_excluded_keys(inputs.get("exclude_row_keys_sources", []))
    frozen_labels = load_frozen_labels(frozen_path)
    rows = load_probe_rows(
        results_path=results_path,
        frozen_labels=frozen_labels,
        expected_probe_config_sha=inputs.get("expected_probe_config_sha"),
        excluded=excluded,
    )
    buckets: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        bucket = classify_row(row)
        if bucket:
            buckets.setdefault(bucket, []).append(row)
    for bucket, bucket_rows in buckets.items():
        bucket_rows.sort(key=lambda row: sort_key_for_bucket(bucket, row, seed))

    selected: list[dict[str, Any]] = []
    bucket_summaries: dict[str, dict[str, Any]] = {}
    for bucket, quota in config.get("quotas", {}).items():
        if not isinstance(quota, int) or isinstance(quota, bool) or quota < 0:
            raise ValueError(f"quota for {bucket!r} must be a non-negative integer")
        available = buckets.get(bucket, [])
        take = available[:quota]
        selected.extend({**row, "target_bucket": bucket} for row in take)
        bucket_summaries[bucket] = {
            "available": len(available),
            "selected": len(take),
            "quota": quota,
        }

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in selected:
        key = row["probe_pool_row_key"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    manifest = {
        "schema_version": "mechinterp-targeted-row-keys/v1",
        "purpose": config.get("purpose"),
        "seed": seed,
        "inputs": {
            "questions_frozen": rel(frozen_path),
            "questions_frozen_sha256": file_sha256(frozen_path),
            "probe_results": rel(results_path),
            "probe_results_sha256": file_sha256(results_path),
            "expected_probe_config_sha": inputs.get("expected_probe_config_sha"),
            "excluded_source_count": len(excluded),
        },
        "heuristics": {
            "refusal_patterns": REFUSAL_PATTERNS,
            "buckets": {
                "known_low_confidence_or_refusal": (
                    "known rows with refusal-like greedy answer, p_correct < 1.0, "
                    "or greedy_correct false"
                ),
                "known_high_confidence_correct": (
                    "known rows without refusal-like greedy answer and no low-confidence flag"
                ),
                "unknown_refusal_like": "unknown rows with refusal-like greedy answer",
                "unknown_answered_wrong_like": (
                    "unknown rows without refusal-like greedy answer"
                ),
            },
        },
        "bucket_summaries": bucket_summaries,
        "total_selected": len(deduped),
        "selected_label_counts": {
            label: sum(1 for row in deduped if row["frozen_label"] == label)
            for label in ("known", "unknown")
        },
    }
    return deduped, manifest


def write_outputs(config: dict[str, Any], rows: list[dict[str, Any]], manifest: dict[str, Any]) -> tuple[Path, Path, Path]:
    output = config["output"]
    row_keys_path = resolve_path(output["row_keys_file"])
    manifest_path = resolve_path(output["manifest"])
    rows_path = resolve_path(output["rows_jsonl"])
    row_keys_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    rows_path.parent.mkdir(parents=True, exist_ok=True)

    row_keys_path.write_text(
        "\n".join(row["probe_pool_row_key"] for row in rows) + "\n",
        encoding="utf-8",
    )
    rows_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return row_keys_path, rows_path, manifest_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args(argv)

    config = load_config(args.config)
    rows, manifest = select_rows(config)
    row_keys_path, rows_path, manifest_path = write_outputs(config, rows, manifest)
    print(f"selected {len(rows)} row keys")
    print(f"wrote {rel(row_keys_path)}")
    print(f"wrote {rel(rows_path)}")
    print(f"wrote {rel(manifest_path)}")


if __name__ == "__main__":
    main()
