#!/usr/bin/env python3
"""Build a frozen mechinterp SelfAware stratified row manifest.

This script consumes SelfAware row-level eval artifacts, not mechinterp probe-pool
or causal-pilot rows. The output is a frozen input for a later dedicated
SelfAware hidden-state extraction; it is not runner-ready for the current
`probe_pool_row_key` causal-pilot runner.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"
EVAL_DIR = REPO_ROOT / "archive" / "experiment" / "phase1" / "eval"
DEFAULT_OUT = (
    REPO_ROOT
    / "experiments"
    / "common"
    / "artifacts"
    / "row_manifests"
    / "selfaware"
    / "mechinterp_selfaware_frozen_row_manifest.json"
)

DEFAULT_SOURCES = {
    "sft_merged_seed1": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b" / "sft_merged_seed1__selfaware" / "scored_rows.jsonl",
    "sft_dpo_seed1": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b" / "sft_dpo_seed1__selfaware" / "scored_rows.jsonl",
    "sft_kto_seed1": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed1_4b" / "sft_kto_seed1__selfaware" / "scored_rows.jsonl",
    "sft_merged_seed2": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_merged_4b" / "sft_merged_seed2__selfaware" / "scored_rows.jsonl",
    "sft_dpo_seed2": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_dpo_4b" / "sft_dpo_seed2__selfaware" / "scored_rows.jsonl",
    "sft_kto_seed2": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed2_sft_kto_4b" / "sft_kto_seed2__selfaware" / "scored_rows.jsonl",
    "sft_merged_seed3": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_merged_4b" / "sft_merged_seed3__selfaware" / "scored_rows.jsonl",
    "sft_dpo_seed3": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_dpo_4b" / "sft_dpo_seed3__selfaware" / "scored_rows.jsonl",
    "sft_kto_seed3": EVAL_DIR / "results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed3_sft_kto_4b" / "sft_kto_seed3__selfaware" / "scored_rows.jsonl",
}
REQUIRED_ARMS = tuple(DEFAULT_SOURCES)
SFT_MERGED_ARMS = ("sft_merged_seed1", "sft_merged_seed2", "sft_merged_seed3")
DPO_ARMS = ("sft_dpo_seed1", "sft_dpo_seed2", "sft_dpo_seed3")
KTO_ARMS = ("sft_kto_seed1", "sft_kto_seed2", "sft_kto_seed3")

REQUIRED_ROW_FIELDS = (
    "arm",
    "eval_set",
    "row_index",
    "id",
    "question",
    "label",
    "refused",
    "correct",
    "truthful",
    "config_sha",
    "source",
)
IDENTITY_CONSISTENCY_FIELDS = ("eval_set", "row_index", "id", "question", "label", "source")


class SelfAwareManifestError(RuntimeError):
    pass


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def stable_row_key(row: dict[str, Any]) -> str:
    eval_set = row["eval_set"]
    row_index = row["row_index"]
    raw_id = row.get("id")
    if not isinstance(eval_set, str) or not eval_set:
        raise SelfAwareManifestError("eval_set must be a non-empty string")
    if not isinstance(row_index, int) or isinstance(row_index, bool) or row_index < 0:
        raise SelfAwareManifestError("row_index must be a non-negative integer")
    key = f"selfaware::{eval_set}::{row_index:06d}"
    if isinstance(raw_id, str) and raw_id:
        key = f"{key}::{raw_id}"
    return key


def validate_row(row: dict[str, Any], *, path: Path, line_number: int, source_arm: str) -> None:
    missing = [field for field in REQUIRED_ROW_FIELDS if field not in row]
    if missing:
        raise SelfAwareManifestError(f"{path}:{line_number} missing required fields: {missing}")
    if row["arm"] != source_arm:
        raise SelfAwareManifestError(
            f"{path}:{line_number} arm {row['arm']!r} does not match source {source_arm!r}"
        )
    if row["eval_set"] != "selfaware" or row["source"] != "selfaware":
        raise SelfAwareManifestError(f"{path}:{line_number} is not a SelfAware row")
    if row["label"] not in {"known", "unknown"}:
        raise SelfAwareManifestError(f"{path}:{line_number} invalid label {row['label']!r}")
    for field in ("refused", "correct", "truthful"):
        if not isinstance(row[field], bool):
            raise SelfAwareManifestError(f"{path}:{line_number} {field} must be boolean")
    if not isinstance(row["question"], str) or not row["question"]:
        raise SelfAwareManifestError(f"{path}:{line_number} question must be non-empty")
    stable_row_key(row)


def load_source_rows(sources: dict[str, Path]) -> dict[str, dict[str, dict[str, Any]]]:
    by_key: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    identity_rows: dict[str, dict[str, Any]] = {}
    for source_arm, path in sources.items():
        if source_arm not in REQUIRED_ARMS:
            raise SelfAwareManifestError(f"unexpected source arm {source_arm!r}")
        if not path.is_file():
            raise SelfAwareManifestError(f"missing source scored_rows file: {path}")
        seen_in_arm: set[str] = set()
        with path.open(encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                validate_row(row, path=path, line_number=line_number, source_arm=source_arm)
                key = stable_row_key(row)
                if key in seen_in_arm:
                    raise SelfAwareManifestError(f"duplicate SelfAware row identity in {path}: {key}")
                seen_in_arm.add(key)
                existing = identity_rows.get(key)
                if existing is not None:
                    mismatched = [
                        field for field in IDENTITY_CONSISTENCY_FIELDS
                        if existing.get(field) != row.get(field)
                    ]
                    if mismatched:
                        raise SelfAwareManifestError(
                            f"ambiguous SelfAware identity {key}: inconsistent {mismatched}"
                        )
                else:
                    identity_rows[key] = row
                by_key[key][source_arm] = row
    return {key: dict(rows) for key, rows in by_key.items()}


def require_complete_coverage(rows_by_key: dict[str, dict[str, dict[str, Any]]]) -> None:
    required = set(REQUIRED_ARMS)
    incomplete = {
        key: sorted(required - set(rows))
        for key, rows in rows_by_key.items()
        if set(rows) != required
    }
    if incomplete:
        first_key = sorted(incomplete)[0]
        raise SelfAwareManifestError(
            f"incomplete arm coverage for {len(incomplete)} row(s); "
            f"{first_key} missing {incomplete[first_key]}"
        )


def all_rows(rows: dict[str, dict[str, Any]], arms: tuple[str, ...], field: str, value: Any) -> bool:
    return all(rows[arm].get(field) == value for arm in arms)


def any_rows(rows: dict[str, dict[str, Any]], arms: tuple[str, ...], field: str, value: Any) -> bool:
    return any(rows[arm].get(field) == value for arm in arms)


def stratum_memberships(rows: dict[str, dict[str, Any]]) -> list[str]:
    label = rows[REQUIRED_ARMS[0]]["label"]
    memberships: list[str] = []
    if (
        label == "unknown"
        and all_rows(rows, REQUIRED_ARMS, "refused", True)
        and all_rows(rows, REQUIRED_ARMS, "truthful", True)
    ):
        memberships.append("stable_unknown_refusal")
    if (
        label == "known"
        and all_rows(rows, REQUIRED_ARMS, "refused", False)
        and all_rows(rows, REQUIRED_ARMS, "correct", True)
        and all_rows(rows, REQUIRED_ARMS, "truthful", True)
    ):
        memberships.append("stable_known_correct")
    if (
        label == "unknown"
        and all_rows(rows, SFT_MERGED_ARMS, "refused", True)
        and all_rows(rows, SFT_MERGED_ARMS, "truthful", True)
        and any_rows(rows, DPO_ARMS, "refused", False)
    ):
        memberships.append("dpo_unknown_refusal_loss_transition")
    if (
        label == "unknown"
        and all_rows(rows, SFT_MERGED_ARMS, "refused", True)
        and all_rows(rows, SFT_MERGED_ARMS, "truthful", True)
        and any_rows(rows, KTO_ARMS, "refused", False)
    ):
        memberships.append("kto_unknown_refusal_loss_transition")
    if (
        label == "known"
        and any_rows(rows, SFT_MERGED_ARMS, "refused", True)
        and any_rows(rows, DPO_ARMS + KTO_ARMS, "correct", True)
    ):
        memberships.append("known_recovery_transition")
    if (
        label == "known"
        and all_rows(rows, SFT_MERGED_ARMS, "correct", True)
        and any_rows(rows, DPO_ARMS + KTO_ARMS, "truthful", False)
    ):
        memberships.append("known_corruption_transition")
    return memberships


def evidence_for_rows(rows: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for arm in REQUIRED_ARMS:
        row = rows[arm]
        evidence[arm] = {
            "refused": row["refused"],
            "correct": row["correct"],
            "truthful": row["truthful"],
            "generated_answer": row.get("generated_answer"),
            "answer_text": row.get("answer_text"),
            "stated_confidence": row.get("stated_confidence"),
            "config_sha": row["config_sha"],
            "method": row.get("method"),
            "model": row.get("model"),
            "generation_attempts": row.get("generation_attempts"),
            "stated_confidence_retry_count": row.get("stated_confidence_retry_count"),
            "stated_confidence_retry_exhausted": row.get("stated_confidence_retry_exhausted"),
        }
    return evidence


def manifest_row(key: str, rows: dict[str, dict[str, Any]], memberships: list[str]) -> dict[str, Any]:
    base = rows[REQUIRED_ARMS[0]]
    answer_value = base.get("answer_value")
    aliases = base.get("aliases")
    if aliases is None:
        aliases = []
    if not isinstance(aliases, list):
        raise SelfAwareManifestError(f"{key} aliases must be a list when present")
    return {
        "row_key": key,
        "stable_identity": {
            "eval_set": base["eval_set"],
            "row_index": base["row_index"],
            "id": base.get("id"),
            "source": base["source"],
        },
        "question": base["question"],
        "prompt": base["question"],
        "label": base["label"],
        "answer_value": answer_value,
        "aliases": aliases,
        "strata": memberships,
        "source_arms": evidence_for_rows(rows),
    }


def build_manifest(sources: dict[str, Path]) -> dict[str, Any]:
    missing = sorted(set(REQUIRED_ARMS) - set(sources))
    if missing:
        raise SelfAwareManifestError(f"missing required source arms: {missing}")
    rows_by_key = load_source_rows(sources)
    require_complete_coverage(rows_by_key)
    stratum_index: dict[str, list[str]] = defaultdict(list)
    rows: list[dict[str, Any]] = []
    for key in sorted(rows_by_key):
        memberships = stratum_memberships(rows_by_key[key])
        if not memberships:
            continue
        rows.append(manifest_row(key, rows_by_key[key], memberships))
        for membership in memberships:
            stratum_index[membership].append(key)
    return {
        "schema_version": "mechinterp-selfaware-frozen-row-manifest/v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": {
            "program": "mechinterp",
            "source": "SelfAware row-level eval scored_rows only",
            "no_gpu": True,
            "no_docker": True,
            "not_probe_pool_runner_ready": True,
            "intended_next_step": "dedicated SelfAware hidden-state extraction using these frozen row identities",
        },
        "identity": {
            "row_key_format": "selfaware::<eval_set>::<zero_padded_row_index>::<raw_id>",
            "required_identity_fields": list(IDENTITY_CONSISTENCY_FIELDS),
        },
        "sources": {
            arm: repo_relative(path) for arm, path in sources.items()
        },
        "required_arms": list(REQUIRED_ARMS),
        "strata": {
            name: {"count": len(keys), "row_keys": keys}
            for name, keys in sorted(stratum_index.items())
        },
        "row_count": len(rows),
        "rows": rows,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_manifest(DEFAULT_SOURCES)
        if not args.no_write:
            write_manifest(args.out, manifest)
        print(json.dumps({
            "ok": True,
            "out": None if args.no_write else repo_relative(args.out),
            "row_count": manifest["row_count"],
            "strata_counts": {
                name: payload["count"] for name, payload in manifest["strata"].items()
            },
        }, indent=2, sort_keys=True))
        return 0
    except SelfAwareManifestError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
