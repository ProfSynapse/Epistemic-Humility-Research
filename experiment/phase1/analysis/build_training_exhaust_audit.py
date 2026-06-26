#!/usr/bin/env python3
"""Summarize local Phase 1 training exhaust into reviewable audit tables.

The source run products under ``scratch/`` are intentionally not committed.
This script extracts durable, lightweight summaries from capacity profiles,
timestamped training JSONL logs, and the checked-in self-aware eval rollup.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SCRATCH_RUNS = ROOT / "scratch" / "schema_response_confidence" / "runs"
EVAL_GROUPED = (
    ROOT
    / "experiment"
    / "phase1"
    / "eval"
    / "analysis"
    / "selfaware_full_run_comparison_grouped.csv"
)
OUT_DIR = ROOT / "experiment" / "phase1" / "analysis"


SUMMARY_FIELDS = [
    "run_set",
    "timestamp_dir",
    "normalized_arm_guess",
    "training_type",
    "status_completed",
    "base_model_tail",
    "dataset_tail",
    "dataset_train_examples",
    "lora_rank",
    "lora_alpha",
    "lora_dropout",
    "batch_size",
    "grad_accum",
    "effective_batch",
    "learning_rate_config",
    "warmup_ratio",
    "lr_scheduler",
    "beta",
    "num_epochs",
    "max_steps",
    "final_step",
    "total_steps_logged",
    "log_rows",
    "training_time_min",
    "peak_reserved_pct",
    "log_peak_reserved_pct",
    "min_reserved_headroom_gb",
    "peak_samples_per_sec",
    "peak_steps_per_sec",
    "final_loss",
    "loss_first",
    "loss_last",
    "loss_min",
    "loss_max",
    "grad_norm_mean",
    "grad_norm_max",
    "lr_observed_max",
    "lr_observed_last",
    "dpo_reward_accuracy_mean",
    "dpo_reward_accuracy_last",
    "reward_margin_mean",
    "reward_margin_last",
    "grpo_reward_mean",
    "grpo_reward_last",
    "grpo_reward_std_mean",
    "kl_mean",
    "kl_last",
    "kl_max",
    "completion_length_mean",
    "flags",
    "eval_family",
    "eval_balanced_behavior_score",
    "eval_truthful_pct",
    "eval_refusal_recall_pct",
    "eval_answer_on_unknown_pct",
    "eval_over_refusal_pct",
    "eval_correct_on_known_pct",
    "eval_mean_confidence",
    "eval_brier_vs_response_appropriateness",
]


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(result) or math.isinf(result):
        return None
    return result


def fmt(value: Any, places: int = 6) -> Any:
    number = as_float(value)
    if number is None:
        return value if value is not None else ""
    text = f"{number:.{places}f}".rstrip("0").rstrip(".")
    return text if text else "0"


def mean(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    if not clean:
        return None
    return statistics.fmean(clean)


def max_or_none(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return max(clean) if clean else None


def min_or_none(values: list[float | None]) -> float | None:
    clean = [v for v in values if v is not None]
    return min(clean) if clean else None


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def concrete_training_log(log_dir: Path) -> Path | None:
    if not log_dir.exists():
        return None
    # On Windows the "training_latest.jsonl" entry can be an inaccessible link.
    candidates = [
        p
        for p in sorted(log_dir.glob("training_*.jsonl"))
        if p.name != "training_latest.jsonl" and p.is_file()
    ]
    if not candidates:
        return None
    return candidates[-1]


def tail(value: Any, parts: int = 4) -> str:
    if not value:
        return ""
    normalized = str(value).replace("\\", "/").rstrip("/")
    return "/".join(normalized.split("/")[-parts:])


def normalized_arm_guess(run_set: str) -> str:
    name = run_set
    replacements = [
        ("schema_clean_sft_grpo_v2_seed1_full", "clean_sft_grpo_v2"),
        ("schema_clean_sft_grpo_seed1_full", "clean_sft_grpo_v1"),
        ("schema_clean_sft_dpo_seed1_full", "clean_sft_dpo"),
        ("schema_clean_sft_kto_seed1_full", "clean_sft_kto"),
        ("sft_schema_clean_seed1_full", "clean_sft_merged"),
        ("clean_sft_dpo_grpo_seed1_full", "clean_sft_dpo_grpo"),
        ("clean_sft_kto_grpo_seed1_full", "clean_sft_kto_grpo"),
        ("clean_sft_grpo_dpo_seed1_full", "clean_sft_grpo_dpo"),
        ("clean_sft_grpo_kto_seed1_full", "clean_sft_grpo_kto"),
        ("schema_sft_grpo_seed1_full", "schema_sft_grpo"),
        ("schema_sft_dpo_seed1_full", "schema_sft_dpo"),
        ("schema_sft_kto_seed1_full", "schema_sft_kto"),
        ("sft_schema_seed1_full", "schema_sft_merged"),
    ]
    for source, target in replacements:
        if name == source:
            return target
    return name.replace("_seed1_full", "").replace("_full", "")


def load_eval_rollup() -> dict[str, dict[str, str]]:
    if not EVAL_GROUPED.exists():
        return {}
    out: dict[str, dict[str, str]] = {}
    with EVAL_GROUPED.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            family = row.get("family", "")
            arm = row.get("normalized_arm", "")
            # Prefer the response-confidence clean/stacking families over older
            # same-name Amendment A/B rows when joining by normalized arm.
            if arm and (
                arm not in out
                or family.startswith("Amendment E")
                or family.startswith("Amendment F")
                or family.startswith("Amendment D")
            ):
                out[arm] = row
    return out


def summarize_run(run_dir: Path, eval_rows: dict[str, dict[str, str]]) -> dict[str, Any]:
    capacity = load_json(run_dir / "capacity_features.json")
    log_path = concrete_training_log(run_dir / "logs")
    log_rows = load_jsonl(log_path) if log_path else []
    first = log_rows[0] if log_rows else {}
    last = log_rows[-1] if log_rows else {}
    metric_rows = [row for row in log_rows if "loss" in row]
    first_metric = metric_rows[0] if metric_rows else first
    last_metric = metric_rows[-1] if metric_rows else last
    losses = [as_float(row.get("loss")) for row in log_rows]
    grad_norms = [as_float(row.get("grad_norm")) for row in log_rows]
    lrs = [as_float(row.get("learning_rate")) for row in log_rows]
    reward_acc = [as_float(row.get("rewards/accuracies")) for row in log_rows]
    margins = [as_float(row.get("rewards/margins")) for row in log_rows]
    grpo_rewards = [as_float(row.get("reward")) for row in log_rows]
    grpo_reward_std = [as_float(row.get("reward_std")) for row in log_rows]
    kls = [as_float(row.get("kl")) for row in log_rows]
    completion_lengths = [as_float(row.get("completion_length")) for row in log_rows]
    log_peak_reserved_pct = max_or_none(
        [as_float(row.get("max_gpu_memory_reserved_pct")) for row in log_rows]
    )

    run_set = run_dir.parent.name
    arm = normalized_arm_guess(run_set)
    eval_row = eval_rows.get(arm, {})
    flags: list[str] = []

    peak_reserved = as_float(capacity.get("capacity_peak_gpu_memory_reserved_pct"))
    headroom = as_float(capacity.get("capacity_min_gpu_memory_reserved_headroom_gb"))
    if peak_reserved is not None and peak_reserved > 100:
        flags.append("capacity_pct_over_100")
    if peak_reserved is not None and peak_reserved >= 85:
        flags.append("vram_high")
    if headroom is not None and headroom < 3:
        flags.append("low_vram_headroom")
    if capacity.get("oom_risk_level") and capacity.get("oom_risk_level") != "low":
        flags.append(f"oom_risk_{capacity.get('oom_risk_level')}")
    if mean(reward_acc) is not None and mean(reward_acc) < 0.5:
        flags.append("preference_accuracy_below_coinflip")
    if mean(margins) is not None and mean(margins) <= 0:
        flags.append("nonpositive_reward_margin")
    if mean(kls) is not None and mean(kls) > 1.0:
        flags.append("grpo_kl_high_mean")

    runtime_seconds = (
        as_float(capacity.get("result_training_time_seconds"))
        or as_float(last.get("train_runtime"))
        or as_float(last.get("elapsed_seconds"))
    )

    return {
        "run_set": run_set,
        "timestamp_dir": run_dir.name,
        "normalized_arm_guess": arm,
        "training_type": capacity.get("training_type", ""),
        "status_completed": capacity.get("status_completed", ""),
        "base_model_tail": tail(capacity.get("model_base_model")),
        "dataset_tail": tail(capacity.get("dataset_source")),
        "dataset_train_examples": capacity.get("dataset_train_examples", ""),
        "lora_rank": capacity.get("lora_rank", ""),
        "lora_alpha": capacity.get("lora_alpha", ""),
        "lora_dropout": capacity.get("lora_dropout", ""),
        "batch_size": capacity.get("training_batch_size", ""),
        "grad_accum": capacity.get("training_gradient_accumulation_steps", ""),
        "effective_batch": capacity.get("training_effective_batch_size", ""),
        "learning_rate_config": capacity.get("training_learning_rate", ""),
        "warmup_ratio": capacity.get("training_warmup_ratio", ""),
        "lr_scheduler": capacity.get("training_lr_scheduler", ""),
        "beta": capacity.get("training_beta", ""),
        "num_epochs": capacity.get("training_num_epochs", ""),
        "max_steps": capacity.get("training_max_steps", ""),
        "final_step": capacity.get("result_final_step", ""),
        "total_steps_logged": last.get("total_steps", ""),
        "log_rows": len(log_rows),
        "training_time_min": fmt(runtime_seconds / 60 if runtime_seconds else None, 2),
        "peak_reserved_pct": fmt(peak_reserved, 2),
        "log_peak_reserved_pct": fmt(log_peak_reserved_pct, 2),
        "min_reserved_headroom_gb": fmt(headroom, 2),
        "peak_samples_per_sec": fmt(capacity.get("capacity_peak_samples_per_sec"), 3),
        "peak_steps_per_sec": fmt(capacity.get("capacity_peak_steps_per_second"), 3),
        "final_loss": fmt(capacity.get("result_final_loss")),
        "loss_first": fmt(first_metric.get("loss")),
        "loss_last": fmt(last_metric.get("loss")),
        "loss_min": fmt(min_or_none(losses)),
        "loss_max": fmt(max_or_none(losses)),
        "grad_norm_mean": fmt(mean(grad_norms)),
        "grad_norm_max": fmt(max_or_none(grad_norms)),
        "lr_observed_max": fmt(max_or_none(lrs)),
        "lr_observed_last": fmt(last_metric.get("learning_rate")),
        "dpo_reward_accuracy_mean": fmt(mean(reward_acc)),
        "dpo_reward_accuracy_last": fmt(last_metric.get("rewards/accuracies")),
        "reward_margin_mean": fmt(mean(margins)),
        "reward_margin_last": fmt(last_metric.get("rewards/margins")),
        "grpo_reward_mean": fmt(mean(grpo_rewards)),
        "grpo_reward_last": fmt(last_metric.get("reward")),
        "grpo_reward_std_mean": fmt(mean(grpo_reward_std)),
        "kl_mean": fmt(mean(kls)),
        "kl_last": fmt(last_metric.get("kl")),
        "kl_max": fmt(max_or_none(kls)),
        "completion_length_mean": fmt(mean(completion_lengths)),
        "flags": ";".join(flags),
        "eval_family": eval_row.get("family", ""),
        "eval_balanced_behavior_score": fmt(eval_row.get("mean_balanced_behavior_score")),
        "eval_truthful_pct": fmt(eval_row.get("mean_truthful_pct")),
        "eval_refusal_recall_pct": fmt(eval_row.get("mean_refusal_recall_pct")),
        "eval_answer_on_unknown_pct": fmt(eval_row.get("mean_answer_on_unknown_pct")),
        "eval_over_refusal_pct": fmt(eval_row.get("mean_over_refusal_pct")),
        "eval_correct_on_known_pct": fmt(eval_row.get("mean_correct_on_known_pct")),
        "eval_mean_confidence": fmt(eval_row.get("mean_mean_confidence")),
        "eval_brier_vs_response_appropriateness": fmt(
            eval_row.get("mean_brier_vs_response_appropriateness")
        ),
    }


def discover_runs() -> list[Path]:
    if not SCRATCH_RUNS.exists():
        return []
    return sorted(SCRATCH_RUNS.glob("*/*/capacity_features.json"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def report_rows(rows: list[dict[str, Any]]) -> str:
    full_rows = [r for r in rows if str(r["run_set"]).endswith("_full")]
    clean_rows = [
        r
        for r in full_rows
        if str(r["normalized_arm_guess"]).startswith("clean_")
        or str(r["normalized_arm_guess"]) == "clean_sft_merged"
    ]
    preference_flags = [
        r
        for r in clean_rows
        if "preference_accuracy_below_coinflip" in str(r.get("flags"))
        or "nonpositive_reward_margin" in str(r.get("flags"))
    ]
    vram_flags = [
        r
        for r in clean_rows
        if "vram_high" in str(r.get("flags")) or "low_vram_headroom" in str(r.get("flags"))
    ]
    best_by_balanced = sorted(
        [r for r in clean_rows if as_float(r.get("eval_balanced_behavior_score")) is not None],
        key=lambda row: as_float(row.get("eval_balanced_behavior_score")) or -1,
        reverse=True,
    )[:8]

    lines = [
        "# Training Exhaust Hyperparameter Audit",
        "",
        "Generated from local scratch capacity profiles, timestamped trainer JSONL logs, "
        "and the checked-in self-aware eval rollup. Raw scratch artifacts remain uncommitted.",
        "",
        "## Scope",
        "",
        f"- Parsed capacity/log artifacts: {len(rows)} runs.",
        f"- Full-run rows: {len(full_rows)}.",
        f"- Clean response-confidence rows with eval joins: {len(clean_rows)}.",
        "",
        "## Main Read",
        "",
        "- LoRA shape was constant across the clean runs inspected here: rank 32, alpha 64, dropout 0.05. Current results therefore do not identify a LoRA-rank effect.",
        "- Effective batch and VRAM limits are arm-specific. GRPO v2 full used batch 32 with low OOM risk; clean KTO used batch 12 and reached the high-VRAM/moderate-risk zone.",
        "- Clean DPO/KTO rows generally optimized their trainer objective, but downstream behavior moved only modestly. That points first to preference/reward target design and beta/LR fit, not simply to needing more epochs.",
        "- GRPO produces the strongest behavioral pushes in this matrix, but it also tends to push refusal recall and over-refusal together; the best seed-1 stack so far is still a compromise, not an aligned confidence solution.",
        "",
        "## Best Clean Rows By Balanced Behavior",
        "",
        "| arm | method | batch | lr | beta | peak VRAM % | log peak % | balanced | refusal recall | answer unknown | over-refusal | confidence | flags |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in best_by_balanced:
        lines.append(
            "| {normalized_arm_guess} | {training_type} | {effective_batch} | {learning_rate_config} | {beta} | {peak_reserved_pct} | {log_peak_reserved_pct} | {eval_balanced_behavior_score} | {eval_refusal_recall_pct} | {eval_answer_on_unknown_pct} | {eval_over_refusal_pct} | {eval_mean_confidence} | {flags} |".format(
                **row
            )
        )

    lines.extend(
        [
            "",
            "## Preference-Signal Flags",
            "",
        ]
    )
    if preference_flags:
        lines.extend(
            [
                "| arm | method | reward accuracy mean | margin mean | margin last | eval balanced | flags |",
                "|---|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in preference_flags:
            lines.append(
                "| {normalized_arm_guess} | {training_type} | {dpo_reward_accuracy_mean} | {reward_margin_mean} | {reward_margin_last} | {eval_balanced_behavior_score} | {flags} |".format(
                    **row
                )
            )
    else:
        lines.append("- No preference-margin flags in the clean rows.")

    lines.extend(
        [
            "",
            "## Capacity Flags",
            "",
        ]
    )
    if vram_flags:
        lines.extend(
            [
                "| arm | method | batch | peak VRAM % | log peak % | min headroom GB | samples/sec | flags |",
                "|---|---:|---:|---:|---:|---:|---:|---|",
            ]
        )
        for row in vram_flags:
            lines.append(
                "| {normalized_arm_guess} | {training_type} | {effective_batch} | {peak_reserved_pct} | {log_peak_reserved_pct} | {min_reserved_headroom_gb} | {peak_samples_per_sec} | {flags} |".format(
                    **row
                )
            )
    else:
        lines.append("- No high-VRAM flags in the clean rows.")
    lines.append("")
    lines.append(
        "Note: `capacity_pct_over_100` marks a capacity signal that exceeded "
        "the card's nominal VRAM. On this Windows/Docker/Unsloth stack that may "
        "reflect offload/shared-memory behavior, allocator-history accounting, "
        "or a telemetry/unit anomaly. Treat that row as unsafe for batch-size "
        "increases, but do not treat the exact percentage as physically "
        "meaningful without an independent live rerun."
    )

    lines.extend(
        [
            "",
            "## Literature-Backed Hyperparameter Guidance",
            "",
            "- LoRA rank: `2602.06204` supports a coupled rank/LR view. If we test ranks beyond r32, do not change rank alone; pair each rank with either a justified LR scaling rule or a small LR panel.",
            "- DPO beta: `2407.08639` supports beta sensitivity as a function of preference-pair quality. Before a beta panel, audit chosen/rejected pair gaps or stratify known/unknown/ambiguous pair types.",
            "- GRPO beta/KL: current GRPO rows are behaviorally strongest but flagged with high mean KL. A GRPO beta/KL panel is plausible only if it tests the over-refusal tradeoff, not just final reward.",
            "- Batch size: use capacity evidence only after objective choice. DPO has room to probe higher effective batch; KTO is near the local ceiling; GRPO batch 32 is already the practical starting point.",
            "",
            "## Decision Implications",
            "",
            "- Do not blanket-increase batch size. SFT/DPO may have room; KTO is already near the ceiling; GRPO batch 32 is plausible but should keep a 6 GB minimum-headroom guard.",
            "- Before LR/beta sensitivity runs, decide whether the underlying objective is worth rerunning; if yes, use the ingested LoRA-LR and DPO-beta papers to choose a small theory-backed panel.",
            "- For 8B, start with the Tier 1 seed-1 response-confidence screen after the source-label/thinking gates, not the full matrix.",
            "- For small-model tuning, prioritize reward/data design and confidence calibration over simply adding DPO/KTO epochs.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    eval_rows = load_eval_rollup()
    rows = [
        summarize_run(capacity_path.parent, eval_rows) for capacity_path in discover_runs()
    ]
    rows.sort(key=lambda row: (row["run_set"], row["timestamp_dir"]))
    write_csv(OUT_DIR / "training_exhaust_summary.csv", rows)
    (OUT_DIR / "training_exhaust_hyperparameter_report.md").write_text(
        report_rows(rows), encoding="utf-8"
    )
    print(f"Wrote {len(rows)} rows to {OUT_DIR / 'training_exhaust_summary.csv'}")
    print(f"Wrote report to {OUT_DIR / 'training_exhaust_hyperparameter_report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
