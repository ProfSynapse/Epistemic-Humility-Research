#!/usr/bin/env python3
"""PROBE_DIR-free selection/alignment primitives for the hidden-state harness.

Split out of hidden_state_probe.py (SRP refactor). Holds the row-key picking,
row-keys file loading, probe_results.jsonl streaming, and SelfAware-manifest
loading/conversion logic. The two slice entry points (select_matched_slice,
select_selfaware_manifest_slice) stay in the facade because they read PROBE_DIR
(the monkeypatch seam); they delegate here for the path-agnostic work.
"""

from __future__ import annotations

import json
from pathlib import Path

from hs_paths import _rel
from hs_provenance import _file_sha256


def _select_keys(frozen: dict, pool_field: str, n: int, seed: int) -> list[str]:
    """Deterministically pick n keys from a frozen-split pool by stable hash."""
    import hashlib

    keys = list(frozen.get(pool_field, []))
    if n is None or n >= len(keys):
        return keys
    ordered = sorted(
        keys,
        key=lambda k: hashlib.sha256(f"{seed}|{k}".encode()).hexdigest(),
    )
    return ordered[:n]


def load_selection_row_keys_file(path: Path) -> list[str]:
    """Load exact extraction row keys from a small checked-in text file."""
    if not path.is_file():
        raise FileNotFoundError(f"selection.row_keys_file missing: {_rel(path)}")
    keys: list[str] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if not line:
            continue
        keys.append(line)
    if not keys:
        raise ValueError(f"selection.row_keys_file {_rel(path)} contained no row keys")
    seen: set[str] = set()
    duplicates: list[str] = []
    for key in keys:
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    if duplicates:
        raise ValueError(
            f"selection.row_keys_file {_rel(path)} contains duplicate row key(s): "
            f"{duplicates[:3]}"
        )
    return keys


def load_selfaware_manifest_rows(
    manifest_path: Path,
    *,
    wanted_strata: list[str] | None = None,
    max_rows: int | None = None,
) -> list[dict]:
    """Convert frozen SelfAware manifest rows into extraction slice rows."""
    if not manifest_path.is_file():
        raise FileNotFoundError(f"SelfAware manifest {_rel(manifest_path)} not found")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "mechinterp-selfaware-frozen-row-manifest/v1":
        raise ValueError("SelfAware manifest schema_version is not supported")
    if payload.get("scope", {}).get("not_probe_pool_runner_ready") is not True:
        raise ValueError("SelfAware manifest must declare not_probe_pool_runner_ready: true")
    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise ValueError("SelfAware manifest rows must be a list")
    aligned_probe_config_sha = selfaware_manifest_provenance_sha(manifest_path)
    strata_filter = set(wanted_strata or [])
    selected: list[dict] = []
    seen: set[str] = set()
    for index, row in enumerate(raw_rows):
        converted = convert_selfaware_manifest_row(
            row,
            index=index,
            aligned_probe_config_sha=aligned_probe_config_sha,
        )
        row_strata = set(converted["strata"])
        if strata_filter and not (row_strata & strata_filter):
            continue
        key = converted["row_key"]
        if key in seen:
            raise ValueError(f"duplicate SelfAware manifest row_key {key!r}")
        seen.add(key)
        selected.append(converted)
        if max_rows is not None and len(selected) >= max_rows:
            break
    return selected


def selfaware_manifest_provenance_sha(manifest_path: Path) -> str:
    """Tagged immutable identity for a frozen SelfAware row manifest."""
    digest = _file_sha256(manifest_path)
    if digest is None:
        raise FileNotFoundError(f"SelfAware manifest {_rel(manifest_path)} not found")
    return f"selfaware-manifest-sha256:{digest}"


def convert_selfaware_manifest_row(
    row: dict,
    *,
    index: int,
    aligned_probe_config_sha: str | None = None,
) -> dict:
    """Validate and convert one frozen SelfAware row for extraction."""
    required = ["row_key", "stable_identity", "strata", "label", "question", "prompt"]
    missing = [field for field in required if field not in row]
    if missing:
        raise ValueError(f"SelfAware manifest rows[{index}] missing {missing}")
    row_key = row["row_key"]
    if not isinstance(row_key, str) or not row_key:
        raise ValueError(f"SelfAware manifest rows[{index}].row_key must be non-empty")
    if not isinstance(row["stable_identity"], dict):
        raise ValueError(f"SelfAware manifest rows[{index}].stable_identity must be a mapping")
    if row["label"] not in {"known", "unknown"}:
        raise ValueError(f"SelfAware manifest rows[{index}].label must be known or unknown")
    if not isinstance(row["question"], str) or not row["question"]:
        raise ValueError(f"SelfAware manifest rows[{index}].question must be non-empty")
    prompt = row["prompt"]
    if not isinstance(prompt, str) or not prompt:
        raise ValueError(f"SelfAware manifest rows[{index}].prompt must be non-empty")
    strata = row["strata"]
    if not isinstance(strata, list) or not all(isinstance(item, str) and item for item in strata):
        raise ValueError(f"SelfAware manifest rows[{index}].strata must be non-empty strings")
    aliases = row.get("aliases", [])
    if aliases is None:
        aliases = []
    if not isinstance(aliases, list):
        raise ValueError(f"SelfAware manifest rows[{index}].aliases must be a list")
    return {
        "probe_pool_row_key": row_key,
        "row_key": row_key,
        "stable_identity": row["stable_identity"],
        "strata": list(strata),
        "question": row["question"],
        "prompt": prompt,
        "label": row["label"],
        "frozen_label": row["label"],
        "probe_label": None,
        "aligned_probe_config_sha": aligned_probe_config_sha,
        "answer_value": row.get("answer_value"),
        "aliases": aliases,
        "source_arms": row.get("source_arms", {}),
        "sycophancy": row.get("sycophancy"),
    }


def _stream_probe_rows(results_path: Path, wanted: set[str],
                       label_by_key: dict[str, str]) -> list[dict]:
    """Stream probe_results.jsonl, returning only the selected alignment rows."""
    found: list[dict] = []
    if not results_path.exists():
        raise FileNotFoundError(
            f"alignment source {_rel(results_path)} not found; run the probe "
            "tier first (it produces probe_results.jsonl)"
        )
    with results_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            key = row.get("probe_pool_row_key")
            if key in wanted:
                found.append({
                    "probe_pool_row_key": key,
                    "question": row["question"],
                    "label": label_by_key[key],
                    "frozen_label": label_by_key[key],
                    "probe_label": row.get("label"),
                    "aligned_probe_config_sha": row.get("probe_config_sha"),
                })
    return found
