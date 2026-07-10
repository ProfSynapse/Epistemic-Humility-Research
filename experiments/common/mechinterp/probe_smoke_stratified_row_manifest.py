#!/usr/bin/env python3
"""Build a no-GPU Phase 3 probe-key smoke stratified row manifest.

This derives runner-ready row strata only from existing Phase 3 causal-pilot
`scored_rows.jsonl` outputs that already carry `probe_pool_row_key`. Broader
SelfAware eval rows are intentionally not bridged here because they do not carry
the runner's probe-pool identity.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_DIR = REPO_ROOT / "experiment/phase1/probe"
DEFAULT_SWEEP_ROOT = (
    PROBE_DIR
    / "qwen3-4b-instruct"
    / "causal_pilots"
    / "phase3_local_mech_interp_sweep"
)
DEFAULT_OUT = (
    PROBE_DIR
    / "qwen3-4b-instruct"
    / "causal_pilots"
    / "phase3_probe_smoke_stratified_row_manifest"
    / "row_manifest.json"
)

SFT_FAMILY = ("sft_h_lora_l36", "sft_delta_l35")
SEQUENTIAL_FAMILY = (
    "sft_dpo_h_lora_l34",
    "sft_dpo_delta_l35",
    "sft_kto_h_lora_l35",
    "sft_kto_delta_l36",
)
FIRST_SMOKE_CANDIDATES = (
    "sft_h_lora_l36",
    "sft_delta_l35",
    "sft_dpo_delta_l35",
    "sft_kto_h_lora_l35",
)
BASELINE_CONSISTENCY_FIELDS = (
    "label",
    "question",
    "refused",
    "correct",
    "truthful",
    "answer_value",
)


class RowManifestError(RuntimeError):
    pass


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def load_baseline_rows(sweep_root: Path) -> dict[str, dict[str, dict[str, Any]]]:
    """Return candidate -> row_key -> baseline scored row."""
    by_candidate: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    scored_paths = sorted(sweep_root.glob("*/generation/*/scored_rows.jsonl"))
    if not scored_paths:
        raise RowManifestError(f"no scored_rows.jsonl files found under {sweep_root}")
    for path in scored_paths:
        with path.open(encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("control") != "no_vector_baseline":
                    continue
                candidate = row.get("candidate_label")
                row_key = row.get("probe_pool_row_key")
                if not isinstance(candidate, str) or not candidate:
                    raise RowManifestError(f"{path}:{line_number} missing candidate_label")
                if not isinstance(row_key, str) or not row_key:
                    raise RowManifestError(f"{path}:{line_number} missing probe_pool_row_key")
                if row_key in by_candidate[candidate]:
                    existing = by_candidate[candidate][row_key]
                    mismatched = [
                        field
                        for field in BASELINE_CONSISTENCY_FIELDS
                        if existing.get(field) != row.get(field)
                    ]
                    if mismatched:
                        raise RowManifestError(
                            f"inconsistent duplicate baseline row for candidate {candidate!r} "
                            f"key {row_key!r}: {mismatched}"
                        )
                    continue
                by_candidate[candidate][row_key] = row
    return {candidate: dict(rows) for candidate, rows in by_candidate.items()}


def require_candidates(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
    candidates: tuple[str, ...],
) -> None:
    missing = [candidate for candidate in candidates if candidate not in rows_by_candidate]
    if missing:
        raise RowManifestError(f"missing required candidate baselines: {missing}")


def common_row_keys(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
    candidates: tuple[str, ...],
) -> list[str]:
    require_candidates(rows_by_candidate, candidates)
    common = set(rows_by_candidate[candidates[0]])
    for candidate in candidates[1:]:
        common &= set(rows_by_candidate[candidate])
    return sorted(common)


def _all(rows_by_candidate: dict[str, dict[str, dict[str, Any]]], row_key: str, candidates: tuple[str, ...], field: str, value: Any) -> bool:
    return all(rows_by_candidate[candidate][row_key].get(field) == value for candidate in candidates)


def stable_unknown_refusal(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
    candidates: tuple[str, ...],
) -> list[str]:
    return [
        key
        for key in common_row_keys(rows_by_candidate, candidates)
        if _all(rows_by_candidate, key, candidates, "label", "unknown")
        and _all(rows_by_candidate, key, candidates, "refused", True)
        and _all(rows_by_candidate, key, candidates, "truthful", True)
    ]


def stable_known_correct(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
    candidates: tuple[str, ...],
) -> list[str]:
    return [
        key
        for key in common_row_keys(rows_by_candidate, candidates)
        if _all(rows_by_candidate, key, candidates, "label", "known")
        and _all(rows_by_candidate, key, candidates, "refused", False)
        and _all(rows_by_candidate, key, candidates, "correct", True)
        and _all(rows_by_candidate, key, candidates, "truthful", True)
    ]


def unknown_sft_refusal_to_sequential_answer(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    candidates = SFT_FAMILY + SEQUENTIAL_FAMILY
    return [
        key
        for key in common_row_keys(rows_by_candidate, candidates)
        if _all(rows_by_candidate, key, candidates, "label", "unknown")
        and all(rows_by_candidate[candidate][key].get("refused") is True for candidate in SFT_FAMILY)
        and any(rows_by_candidate[candidate][key].get("refused") is False for candidate in SEQUENTIAL_FAMILY)
    ]


def known_sft_refusal_to_sequential_correct(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    candidates = SFT_FAMILY + SEQUENTIAL_FAMILY
    return [
        key
        for key in common_row_keys(rows_by_candidate, candidates)
        if _all(rows_by_candidate, key, candidates, "label", "known")
        and all(rows_by_candidate[candidate][key].get("refused") is True for candidate in SFT_FAMILY)
        and any(rows_by_candidate[candidate][key].get("correct") is True for candidate in SEQUENTIAL_FAMILY)
    ]


def known_sft_correct_to_sequential_bad(
    rows_by_candidate: dict[str, dict[str, dict[str, Any]]],
) -> list[str]:
    candidates = SFT_FAMILY + SEQUENTIAL_FAMILY
    return [
        key
        for key in common_row_keys(rows_by_candidate, candidates)
        if _all(rows_by_candidate, key, candidates, "label", "known")
        and all(rows_by_candidate[candidate][key].get("correct") is True for candidate in SFT_FAMILY)
        and any(rows_by_candidate[candidate][key].get("truthful") is False for candidate in SEQUENTIAL_FAMILY)
    ]


def build_manifest(sweep_root: Path) -> dict[str, Any]:
    rows_by_candidate = load_baseline_rows(sweep_root)
    all_executable = tuple(sorted(rows_by_candidate))
    require_candidates(rows_by_candidate, SFT_FAMILY + SEQUENTIAL_FAMILY)
    strata = {
        "stable_unknown_refusal_sft_family": stable_unknown_refusal(rows_by_candidate, SFT_FAMILY),
        "stable_unknown_refusal_sequential_family": stable_unknown_refusal(rows_by_candidate, SEQUENTIAL_FAMILY),
        "stable_unknown_refusal_all_executable": stable_unknown_refusal(rows_by_candidate, all_executable),
        "stable_known_correct_sft_family": stable_known_correct(rows_by_candidate, SFT_FAMILY),
        "stable_known_correct_sequential_family": stable_known_correct(rows_by_candidate, SEQUENTIAL_FAMILY),
        "stable_known_correct_all_executable": stable_known_correct(rows_by_candidate, all_executable),
        "unknown_sft_refusal_to_sequential_answer": unknown_sft_refusal_to_sequential_answer(rows_by_candidate),
        "known_sft_refusal_to_sequential_correct": known_sft_refusal_to_sequential_correct(rows_by_candidate),
        "known_sft_correct_to_sequential_bad": known_sft_correct_to_sequential_bad(rows_by_candidate),
    }
    first_smoke_keys = sorted(set().union(
        strata["stable_unknown_refusal_sequential_family"],
        strata["stable_known_correct_all_executable"],
        strata["unknown_sft_refusal_to_sequential_answer"],
        strata["known_sft_refusal_to_sequential_correct"],
        strata["known_sft_correct_to_sequential_bad"],
    ))
    return {
        "schema_version": "phase3-probe-smoke-stratified-row-manifest/v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "scope": {
            "phase": "phase3",
            "evidence_tier": "tier2_exploratory_local_prep",
            "no_gpu": True,
            "no_docker": True,
            "source": "existing Phase 3 causal-pilot generation baseline scored_rows only",
        },
        "source_root": repo_relative(sweep_root),
        "candidate_families": {
            "sft_family": list(SFT_FAMILY),
            "sequential_family": list(SEQUENTIAL_FAMILY),
            "all_executable": list(all_executable),
        },
        "bridge_rationale": {
            "status": "not_runner_ready",
            "reason": (
                "Broader SelfAware eval rows use eval-local identity such as eval_set and row_index "
                "and do not carry probe_pool_row_key, while the Phase 3 runner selects hidden-state "
                "extraction rows by probe_pool_row_key."
            ),
            "safe_next_step": (
                "Use this smoke-slice manifest now; build a validated SelfAware-to-probe bridge or "
                "rerun extraction on frozen SelfAware strata before broad replay."
            ),
        },
        "strata": {
            name: {"count": len(keys), "row_keys": keys}
            for name, keys in strata.items()
        },
        "first_smoke": {
            "candidate_labels": list(FIRST_SMOKE_CANDIDATES),
            "row_keys": first_smoke_keys,
            "row_keys_by_candidate": {
                candidate: first_smoke_keys for candidate in FIRST_SMOKE_CANDIDATES
            },
        },
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sweep-root", type=Path, default=DEFAULT_SWEEP_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = build_manifest(args.sweep_root)
        if not args.no_write:
            write_manifest(args.out, manifest)
        print(json.dumps({
            "ok": True,
            "out": None if args.no_write else repo_relative(args.out),
            "strata_counts": {
                name: payload["count"] for name, payload in manifest["strata"].items()
            },
            "first_smoke_row_count": len(manifest["first_smoke"]["row_keys"]),
        }, indent=2, sort_keys=True))
        return 0
    except RowManifestError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
