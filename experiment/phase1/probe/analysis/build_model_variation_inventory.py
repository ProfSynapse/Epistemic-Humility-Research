#!/usr/bin/env python3
"""Build the Phase 3 model-variation inventory table.

The inventory joins behavior eval metrics, training exhaust, and existing
hidden-state extraction manifests for the JSON-output response-confidence model
panel. It intentionally distinguishes exact current extraction coverage from
legacy pre-schema candidates.
"""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
EVAL_CSV = ROOT / "experiment" / "phase1" / "eval" / "analysis" / "selfaware_full_run_comparison.csv"
TRAINING_CSV = ROOT / "experiment" / "phase1" / "analysis" / "training_exhaust_summary.csv"
PROBE_ROOT = ROOT / "experiment" / "phase1" / "probe"
OUT_CSV = ROOT / "docs" / "research" / "phase3-model-variation-inventory.csv"
OUT_MD = ROOT / "docs" / "research" / "phase3-model-variation-inventory.md"


MODEL_ROWS = [
    {
        "model_row": "base",
        "panel_group": "baseline",
        "preferred_family": "Amendment B answer-confidence cold-start",
        "exact_terms": ['"active_adapter_name": "base"', "adapterless_baseline"],
        "exact_active_adapters": ["base"],
        "exact_run_record_ids": [],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Use as adapterless baseline only after runner support is explicit; otherwise keep as eval-only contrast.",
    },
    {
        "model_row": "clean_sft_merged",
        "panel_group": "two_stage_or_less",
        "preferred_family": "Amendment E clean response-confidence",
        "exact_terms": ["clean_sft_merged", "clean_schema_sft_merged", "sft_schema_clean_seed1_full"],
        "exact_active_adapters": ["clean_sft_merged_seed1"],
        "exact_run_record_ids": ["sft_schema_clean_seed1_full"],
        "legacy_terms": ["sft_merged"],
        "legacy_active_adapters": ["sft_merged_seed1"],
        "next_action": "Materialize clean SFT hidden states first; this is the schema/control baseline for stack comparisons.",
    },
    {
        "model_row": "clean_sft_dpo",
        "panel_group": "two_stage_or_less",
        "preferred_family": "Amendment E clean response-confidence",
        "exact_terms": ["clean_sft_dpo", "clean_schema_sft_dpo", "schema_clean_sft_dpo_seed1_full"],
        "exact_active_adapters": ["clean_sft_dpo_seed1"],
        "exact_run_record_ids": ["schema_clean_sft_dpo_seed1_full"],
        "legacy_terms": ["sft_dpo"],
        "legacy_active_adapters": ["sft_dpo_seed1"],
        "next_action": "Materialize current clean SFT->DPO hidden states before interpreting old SFT-DPO axes.",
    },
    {
        "model_row": "clean_sft_kto",
        "panel_group": "two_stage_or_less",
        "preferred_family": "Amendment E clean response-confidence",
        "exact_terms": ["clean_sft_kto", "clean_schema_sft_kto", "schema_clean_sft_kto_seed1_full"],
        "exact_active_adapters": ["clean_sft_kto_seed1"],
        "exact_run_record_ids": ["schema_clean_sft_kto_seed1_full"],
        "legacy_terms": ["sft_kto"],
        "legacy_active_adapters": ["sft_kto_seed1"],
        "next_action": "Materialize current clean SFT->KTO hidden states; old KTO axes are priors only.",
    },
    {
        "model_row": "clean_sft_grpo_v1",
        "panel_group": "two_stage_or_less",
        "preferred_family": "Amendment E clean response-confidence",
        "exact_terms": ["clean_sft_grpo_v1", "clean_schema_sft_grpo", "schema_clean_sft_grpo_seed1_full"],
        "exact_active_adapters": ["clean_sft_grpo_v1_seed1", "clean_schema_sft_grpo_seed1"],
        "exact_run_record_ids": ["schema_clean_sft_grpo_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Keep as GRPO v1 comparator; prioritize v2 unless a v1/v2 delta becomes central.",
    },
    {
        "model_row": "clean_sft_grpo_v2",
        "panel_group": "two_stage_or_less",
        "preferred_family": "Amendment E clean response-confidence",
        "exact_terms": ["clean_sft_grpo_v2", "clean_schema_sft_grpo_v2", "schema_clean_sft_grpo_v2_seed1_full"],
        "exact_active_adapters": ["clean_sft_grpo_v2_seed1"],
        "exact_run_record_ids": ["schema_clean_sft_grpo_v2_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Materialize hidden states early; this is the strongest two-stage reward-shaped comparator.",
    },
    {
        "model_row": "clean_sft_grpo_dpo",
        "panel_group": "three_stage",
        "preferred_family": "Amendment F GRPO-centered stacking",
        "exact_terms": ["clean_sft_grpo_dpo", "clean_sft_grpo_dpo_seed1_full"],
        "exact_active_adapters": ["clean_sft_grpo_dpo_seed1"],
        "exact_run_record_ids": ["clean_sft_grpo_dpo_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Materialize hidden states; current best stack and likely first causal-readout target.",
    },
    {
        "model_row": "clean_sft_dpo_grpo",
        "panel_group": "three_stage",
        "preferred_family": "Amendment F GRPO-centered stacking",
        "exact_terms": ["clean_sft_dpo_grpo", "clean_sft_dpo_grpo_seed1_full"],
        "exact_active_adapters": ["clean_sft_dpo_grpo_seed1"],
        "exact_run_record_ids": ["clean_sft_dpo_grpo_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Materialize hidden states after GRPO-DPO to isolate preference->RL order effects.",
    },
    {
        "model_row": "clean_sft_grpo_kto",
        "panel_group": "three_stage",
        "preferred_family": "Amendment F GRPO-centered stacking",
        "exact_terms": ["clean_sft_grpo_kto", "clean_sft_grpo_kto_seed1_full"],
        "exact_active_adapters": ["clean_sft_grpo_kto_seed1"],
        "exact_run_record_ids": ["clean_sft_grpo_kto_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Materialize hidden states for RL->unpaired-preference contrast.",
    },
    {
        "model_row": "clean_sft_kto_grpo",
        "panel_group": "three_stage",
        "preferred_family": "Amendment F GRPO-centered stacking",
        "exact_terms": ["clean_sft_kto_grpo", "clean_sft_kto_grpo_seed1_full"],
        "exact_active_adapters": ["clean_sft_kto_grpo_seed1"],
        "exact_run_record_ids": ["clean_sft_kto_grpo_seed1_full"],
        "legacy_terms": [],
        "legacy_active_adapters": [],
        "next_action": "Materialize hidden states for unpaired-preference->RL contrast.",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_int(value: str) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_float(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: str | float | None, digits: int = 2) -> str:
    if value in (None, ""):
        return ""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{number:.{digits}f}".rstrip("0").rstrip(".")


def pick_eval(rows: list[dict[str, str]], model_row: str, preferred_family: str) -> dict[str, str]:
    candidates = [row for row in rows if row.get("normalized_arm") == model_row]
    preferred = [row for row in candidates if row.get("family") == preferred_family]
    candidates = preferred or candidates
    if not candidates:
        return {}

    def score(row: dict[str, str]) -> tuple[int, float]:
        seed_bonus = 1 if row.get("seed") in {"", "1"} else 0
        return seed_bonus, as_float(row.get("balanced_behavior_score", "")) or -1.0

    return sorted(candidates, key=score, reverse=True)[0]


def pick_training(rows: list[dict[str, str]], model_row: str) -> dict[str, str]:
    candidates = [row for row in rows if row.get("normalized_arm_guess") == model_row]
    completed = [row for row in candidates if row.get("status_completed") == "1"]
    candidates = completed or candidates
    if not candidates:
        return {}
    return sorted(candidates, key=lambda row: row.get("timestamp_dir", ""), reverse=True)[0]


def iter_manifests(root: Path) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    skip_dirs = {".pytest_cache", "__pycache__", ".git"}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if name not in skip_dirs]
        if "manifest.json" not in filenames:
            continue
        path = Path(dirpath) / "manifest.json"
        try:
            text = path.read_text(encoding="utf-8")
            payload = json.loads(text)
        except (OSError, json.JSONDecodeError):
            continue
        manifests.append({"path": path, "text": text.casefold(), "json": payload})
    return manifests


def classify_manifests(
    manifests: list[dict[str, Any]],
    exact_terms: list[str],
    legacy_terms: list[str],
    exact_active_adapters: list[str] | None = None,
    exact_run_record_ids: list[str] | None = None,
    legacy_active_adapters: list[str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    exact_active_adapters = exact_active_adapters or []
    exact_run_record_ids = exact_run_record_ids or []
    legacy_active_adapters = legacy_active_adapters or []
    exact = [
        item
        for item in manifests
        if item["json"].get("active_adapter_name") in exact_active_adapters
        or item["json"].get("aligned_run_record_id") in exact_run_record_ids
    ]
    if exact:
        return "exact_current", exact
    legacy = [
        item
        for item in manifests
        if item["json"].get("active_adapter_name") in legacy_active_adapters
        or (
            legacy_terms
            and not exact_active_adapters
            and any(term.casefold() in item["text"] or term.casefold() in str(item["path"]).casefold() for term in legacy_terms)
        )
    ]
    if legacy:
        return "legacy_candidate_only", legacy
    return "missing", []


def rel(path: Path | str) -> str:
    if not path:
        return ""
    p = Path(path)
    try:
        return str(p.resolve().relative_to(ROOT)).replace("\\", "/")
    except (OSError, ValueError):
        return str(path).replace("\\", "/")


def inventory_rows() -> list[dict[str, str]]:
    eval_rows = read_csv(EVAL_CSV)
    training_rows = read_csv(TRAINING_CSV)
    manifests = iter_manifests(PROBE_ROOT)
    rows: list[dict[str, str]] = []
    for spec in MODEL_ROWS:
        eval_row = pick_eval(eval_rows, spec["model_row"], spec["preferred_family"])
        training_row = pick_training(training_rows, spec["model_row"])
        extraction_status, matched = classify_manifests(
            manifests,
            spec["exact_terms"],
            spec["legacy_terms"],
            exact_active_adapters=spec.get("exact_active_adapters", []),
            exact_run_record_ids=spec.get("exact_run_record_ids", []),
            legacy_active_adapters=spec.get("legacy_active_adapters", []),
        )

        answered_known = as_int(eval_row.get("answered_known", ""))
        correct_known = as_int(eval_row.get("correct_known", ""))
        known_wrong_answered = max(answered_known - correct_known, 0)
        verified = sum(1 for item in matched if item["json"].get("verified") is True)
        examples = "; ".join(rel(item["path"]) for item in matched[:3])
        confidence_kind = ""
        family = eval_row.get("family", "")
        if "response-confidence" in family:
            confidence_kind = "response_confidence"
        elif "answer-confidence" in family:
            confidence_kind = "answer_confidence"

        run_set = training_row.get("run_set", "")
        timestamp = training_row.get("timestamp_dir", "")
        run_dir = ""
        if run_set and timestamp:
            run_dir = f"scratch/schema_response_confidence/runs/{run_set}/{timestamp}"

        rows.append(
            {
                "model_row": spec["model_row"],
                "panel_group": spec["panel_group"],
                "eval_family": family,
                "eval_seed": eval_row.get("seed", ""),
                "eval_n": eval_row.get("n", ""),
                "balanced_behavior_score": fmt(eval_row.get("balanced_behavior_score", "")),
                "truthful_pct": fmt(eval_row.get("truthful_pct", "")),
                "refusal_recall_pct": fmt(eval_row.get("refusal_recall_pct", "")),
                "answer_on_unknown_pct": fmt(eval_row.get("answer_on_unknown_pct", "")),
                "over_refusal_pct": fmt(eval_row.get("over_refusal_pct", "")),
                "correct_on_known_pct": fmt(eval_row.get("correct_on_known_pct", "")),
                "known_correct_answered": str(correct_known) if eval_row else "",
                "known_refused": eval_row.get("refuse_on_known", ""),
                "known_wrong_answered": str(known_wrong_answered) if eval_row else "",
                "unknown_refused": eval_row.get("refuse_on_unknown", ""),
                "unknown_answered_wrong_approx": eval_row.get("answered_unknown", ""),
                "confidence_kind": confidence_kind,
                "mean_confidence": fmt(eval_row.get("mean_confidence", ""), 3),
                "confidence_coverage_pct": fmt(eval_row.get("confidence_coverage_pct", "")),
                "brier_vs_response_appropriateness": fmt(eval_row.get("brier_vs_response_appropriateness", ""), 3),
                "source_metrics": rel(eval_row.get("source_metrics", "")),
                "training_type": training_row.get("training_type", ""),
                "training_run_dir": run_dir,
                "dataset_tail": training_row.get("dataset_tail", ""),
                "lora_rank": training_row.get("lora_rank", ""),
                "lora_alpha": training_row.get("lora_alpha", ""),
                "effective_batch": training_row.get("effective_batch", ""),
                "learning_rate_config": training_row.get("learning_rate_config", ""),
                "beta": training_row.get("beta", ""),
                "final_loss": fmt(training_row.get("final_loss", ""), 4),
                "training_time_min": fmt(training_row.get("training_time_min", ""), 1),
                "training_flags": training_row.get("flags", ""),
                "extraction_status": extraction_status,
                "extraction_manifest_count": str(len(matched)),
                "extraction_verified_count": str(verified),
                "extraction_manifest_examples": examples,
                "recommended_next_action": spec["next_action"],
            }
        )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    missing = [row["model_row"] for row in rows if row["extraction_status"] == "missing"]
    legacy = [row["model_row"] for row in rows if row["extraction_status"] == "legacy_candidate_only"]
    exact = [row["model_row"] for row in rows if row["extraction_status"] == "exact_current"]
    first_pass_targets = {"clean_sft_merged", "clean_sft_grpo_v2", "clean_sft_grpo_dpo"}
    first_pass_complete = first_pass_targets.issubset(set(exact))
    lines = [
        "# Phase 3 Model Variation Inventory",
        "",
        "Generated by `experiment/phase1/probe/analysis/build_model_variation_inventory.py`.",
        "",
        "This is an inventory, not a mechanism result. `legacy_candidate_only` means the",
        "manifest matched an earlier pre-schema or non-current row and should be used only",
        "as a template/prior.",
        "",
        "## Coverage Summary",
        "",
        f"- Exact current extraction coverage: {', '.join(exact) if exact else 'none'}",
        f"- Legacy candidate extraction only: {', '.join(legacy) if legacy else 'none'}",
        f"- Missing extraction coverage: {', '.join(missing) if missing else 'none'}",
        "",
        "## Behavior And Extraction Table",
        "",
        "| Model row | Family | Score | Known correct | Known refused | Unknown refused | Unknown answered wrong approx | Mean conf | Extraction | Next action |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {model_row} | {eval_family} | {balanced_behavior_score} | "
            "{known_correct_answered} | {known_refused} | {unknown_refused} | "
            "{unknown_answered_wrong_approx} | {mean_confidence} | {extraction_status} | "
            "{recommended_next_action} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Eval source: `{rel(EVAL_CSV)}`",
            f"- Training exhaust source: `{rel(TRAINING_CSV)}`",
            f"- CSV output: `{rel(OUT_CSV)}`",
            "",
            "## Immediate Worklist",
            "",
        ]
    )
    if first_pass_complete:
        lines.extend(
            [
                "1. Use current behavior-row overlays, not stale embedded legacy `source_arms`, for scans on extracted rows.",
                "2. Run or inspect offline behavior-axis/readout screens for the exact-current rows.",
                "3. Gate causal/logit diagnostics on paired behavior-cell support; unknown-wrong rows are currently rare in the first-pass panel.",
            ]
        )
    else:
        lines.extend(
            [
                "1. Materialize hidden-state extraction for `clean_sft_merged`, `clean_sft_grpo_v2`, and `clean_sft_grpo_dpo` first.",
                "2. Use legacy SFT-DPO/KTO manifests only to copy config structure and sanity-check expected layer roles.",
                "3. Delay causal replay until at least one current extraction has enough behavior-cell rows for paired sign gates.",
            ]
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows = inventory_rows()
    if not rows:
        raise SystemExit("no inventory rows produced")
    write_csv(rows)
    write_markdown(rows)
    print(json.dumps({"csv": rel(OUT_CSV), "markdown": rel(OUT_MD), "rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
