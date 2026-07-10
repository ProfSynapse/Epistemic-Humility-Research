#!/usr/bin/env python3
"""Build a mechinterp answer-sycophancy row manifest for hidden-state extraction.

This consumes local answer-sycophancy scored rows from the eval runner and emits
the extraction-compatible frozen manifest schema already supported by
hidden_state_probe.py. The output is a row panel for mechanistic follow-up, not
a behavioral headline result.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "archive/experiment/phase1/probe"
EVAL_DIR = REPO_ROOT / "experiment" / "phase1" / "eval"
ANALYSIS_DIR = EVAL_DIR / "analysis"
if str(ANALYSIS_DIR) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_DIR))

import sycophancy_answer_analysis as saa  # noqa: E402


DEFAULT_RESULTS_DIR = EVAL_DIR / "results_sycophancy_answer_seed1_all_arms_4b"
DEFAULT_OUT = (
    REPO_ROOT
    / "experiments"
    / "common"
    / "artifacts"
    / "row_manifests"
    / "sycophancy_answer"
    / "mechinterp_sycophancy_answer_seed1_row_manifest.json"
)
REQUIRED_ARMS = ("base_seed1", "sft_seed1", "dpo_seed1", "kto_seed1")
CONDITIONS = ("neutral", "incorrect_hint")
SCHEMA_VERSION = "mechinterp-sycophancy-answer-row-manifest/v1"


class SycophancyManifestError(RuntimeError):
    pass


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_rows(results_dir: Path) -> list[dict[str, Any]]:
    paths = saa.scored_row_paths(results_dir, "sycophancy_answer")
    rows = saa.load_rows(paths)
    arms = {str(row.get("arm")) for row in rows}
    missing = sorted(set(REQUIRED_ARMS) - arms)
    if missing:
        raise SycophancyManifestError(f"missing required arms: {missing}")
    return rows


def group_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, dict[str, Any]]]]:
    grouped: dict[str, dict[str, dict[str, dict[str, Any]]]] = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        arm = str(row.get("arm", ""))
        if arm not in REQUIRED_ARMS:
            continue
        group_id = str(row.get("base_question_id", ""))
        condition = str(row.get("prompt_condition", ""))
        if not group_id or condition not in CONDITIONS:
            continue
        if condition in grouped[group_id][arm]:
            raise SycophancyManifestError(
                f"duplicate {condition} row for arm {arm} base_question_id {group_id}"
            )
        grouped[group_id][arm][condition] = row
    complete = {
        group_id: arm_rows
        for group_id, arm_rows in grouped.items()
        if all(arm in arm_rows and all(c in arm_rows[arm] for c in CONDITIONS) for arm in REQUIRED_ARMS)
    }
    if not complete:
        raise SycophancyManifestError("no complete neutral/incorrect_hint groups found")
    return complete


def wrong_hint_match(row: dict[str, Any]) -> bool:
    return saa.matches_incorrect_answer(row)


def source_arm_evidence(grouped: dict[str, dict[str, Any]], condition: str) -> dict[str, dict[str, Any]]:
    evidence: dict[str, dict[str, Any]] = {}
    for arm in REQUIRED_ARMS:
        row = grouped[arm][condition]
        evidence[arm] = {
            "condition": condition,
            "refused": bool(row.get("refused")),
            "correct": bool(row.get("correct")),
            "truthful": bool(row.get("truthful")),
            "wrong_hint_match": wrong_hint_match(row) if condition == "incorrect_hint" else False,
            "answer_text": row.get("answer_text"),
            "generated_answer": row.get("generated_answer"),
            "stated_confidence": row.get("stated_confidence"),
            "config_sha": row.get("config_sha"),
            "method": row.get("method"),
            "model": row.get("model"),
            "row_id": row.get("id"),
            "row_index": row.get("row_index"),
            "generation_attempts": row.get("generation_attempts"),
            "stated_confidence_retry_count": row.get("stated_confidence_retry_count"),
            "stated_confidence_retry_exhausted": row.get("stated_confidence_retry_exhausted"),
        }
    return evidence


def stratum_memberships(grouped: dict[str, dict[str, Any]], condition: str) -> list[str]:
    wrong = {arm: grouped[arm]["incorrect_hint"] for arm in REQUIRED_ARMS}
    neutral = {arm: grouped[arm]["neutral"] for arm in REQUIRED_ARMS}
    memberships: list[str] = []

    all_non_sft_wrong = all(wrong_hint_match(wrong[arm]) for arm in ("base_seed1", "dpo_seed1", "kto_seed1"))
    if wrong_hint_match(wrong["kto_seed1"]):
        memberships.append("kto_wrong_hint_followed")
    else:
        memberships.append("kto_wrong_hint_not_followed")
    if wrong_hint_match(wrong["sft_seed1"]):
        memberships.append("sft_wrong_hint_followed")
    if bool(wrong["sft_seed1"].get("refused")):
        memberships.append("sft_wrong_hint_refused")
    if all_non_sft_wrong:
        memberships.append("wrong_hint_followed_by_base_dpo_kto")
    if bool(wrong["sft_seed1"].get("refused")) and wrong_hint_match(wrong["kto_seed1"]):
        memberships.append("sft_refuses_wrong_hint_kto_follows")
    for arm in REQUIRED_ARMS:
        if bool(neutral[arm].get("correct")) and not bool(wrong[arm].get("correct")):
            memberships.append(f"neutral_correct_lost_under_wrong_hint__{arm}")

    if not memberships:
        return []
    if condition == "neutral":
        return [f"neutral_counterpart__{name}" for name in memberships]
    return memberships


def row_key(base_question_id: str, condition: str, row: dict[str, Any]) -> str:
    raw_id = str(row.get("id", ""))
    if not raw_id:
        raise SycophancyManifestError(f"row for {base_question_id}/{condition} missing id")
    return f"sycophancy_answer::{condition}::{base_question_id}::{raw_id}"


def manifest_row(base_question_id: str, grouped: dict[str, dict[str, Any]], condition: str) -> dict[str, Any]:
    base_row = grouped["base_seed1"][condition]
    memberships = stratum_memberships(grouped, condition)
    if not memberships:
        raise SycophancyManifestError("manifest_row called for row with no memberships")
    aliases = base_row.get("aliases") or []
    if not isinstance(aliases, list):
        raise SycophancyManifestError(f"{base_question_id}/{condition} aliases must be a list")
    key = row_key(base_question_id, condition, base_row)
    return {
        "row_key": key,
        "stable_identity": {
            "eval_set": base_row.get("eval_set"),
            "row_index": base_row.get("row_index"),
            "id": base_row.get("id"),
            "source": base_row.get("source"),
            "base_question_id": base_question_id,
            "prompt_condition": condition,
        },
        "question": base_row["question"],
        "prompt": base_row["question"],
        "label": "known",
        "answer_value": base_row.get("correct_answer"),
        "aliases": aliases,
        "strata": memberships,
        "source_arms": source_arm_evidence(grouped, condition),
        "sycophancy": {
            "base_question": base_row.get("base_question"),
            "base_dataset": base_row.get("base_dataset"),
            "correct_answer": base_row.get("correct_answer"),
            "incorrect_answer": base_row.get("incorrect_answer"),
            "condition": condition,
        },
    }


def build_manifest(results_dir: Path) -> dict[str, Any]:
    rows = load_rows(results_dir)
    grouped = group_rows(rows)
    rows_out: list[dict[str, Any]] = []
    stratum_index: dict[str, list[str]] = defaultdict(list)
    for base_question_id in sorted(grouped):
        for condition in CONDITIONS:
            memberships = stratum_memberships(grouped[base_question_id], condition)
            if not memberships:
                continue
            row = manifest_row(base_question_id, grouped[base_question_id], condition)
            rows_out.append(row)
            for membership in row["strata"]:
                stratum_index[membership].append(row["row_key"])
    return {
        "schema_version": "mechinterp-selfaware-frozen-row-manifest/v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": {
            "program": "mechinterp",
            "source": "answer-sycophancy scored_rows",
            "source_schema_version": SCHEMA_VERSION,
            "no_gpu": True,
            "no_docker": True,
            "not_probe_pool_runner_ready": True,
            "intended_next_step": "dedicated answer-sycophancy hidden-state extraction using these frozen row identities",
        },
        "identity": {
            "row_key_format": "sycophancy_answer::<prompt_condition>::<base_question_id>::<raw_id>",
            "required_conditions": list(CONDITIONS),
        },
        "sources": {
            "results_dir": repo_relative(results_dir),
        },
        "required_arms": list(REQUIRED_ARMS),
        "strata": {
            name: {"count": len(keys), "row_keys": keys}
            for name, keys in sorted(stratum_index.items())
        },
        "row_count": len(rows_out),
        "rows": rows_out,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_manifest(args.results_dir)
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
    except SycophancyManifestError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
