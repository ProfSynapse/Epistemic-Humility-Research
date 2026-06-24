---
schema_version: research-session/v1
session_id: grpo-centered-stacking-plan
title: GRPO-Centered Stacking Plan
status: active
created_at: "2026-06-24T18:30:52Z"
updated_at: "2026-06-24T18:30:52Z"
phase: phase1
question: Which completed local SelfAware runs are strongest so far, and should the next training extension test GRPO as a third-stage stack with DPO/KTO?
tags:
  - experiment-runner
  - amendment-f
  - response-confidence
  - grpo
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: "After Amendment E clean response-confidence SFT, DPO, KTO, GRPO v1, and GRPO v2 seed-1 evals; before any GRPO-centered three-stage launches."
  changed_by_session: "Adds durable run comparison artifacts and drafts Amendment F for GRPO-centered stacking."
checkpoints:
  - id: 001-analysis
    at: "2026-06-24T18:30:52Z"
    kind: result
    title: Durable SelfAware Full-Run Comparison
    summary: "Materialized full SelfAware comparison CSVs from checked-in metrics.json artifacts so seed-level and grouped evidence are durable outside chat."
    evidence:
      - experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py
      - experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv
      - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
    run_ids: []
    commands:
      - python experiment\\phase1\\eval\\analysis\\build_selfaware_full_run_comparison.py
    decisions:
      - "Keep protocol families separate and treat the balanced behavior score as exploratory/unregistered."
    next_steps:
      - "Use grouped CSV as the quick comparison index and per-run CSV for seed-level provenance."
    signals: {}
  - id: 002-amendment
    at: "2026-06-24T18:30:52Z"
    kind: amendment
    title: GRPO-Centered Stacking Draft
    summary: "Drafted Amendment F for clean_sft_dpo_grpo, clean_sft_kto_grpo, clean_sft_grpo_dpo, and clean_sft_grpo_kto."
    evidence:
      - experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md
    run_ids: []
    commands: []
    decisions:
      - "Use the latest clean Amendment E response-confidence lineage by default, with GRPO v2 as the current GRPO source unless superseded."
    next_steps:
      - "Before launching, validate source lineage, merge immediate source models, run bounded merged-source sanity evals, and name exact paths/configs in launch records."
    signals: {}
---

# GRPO-Centered Stacking Plan

Question: Which completed local SelfAware runs are strongest so far, and should
the next training extension test GRPO as a third-stage stack with DPO/KTO?

## Checkpoints

### 001-analysis - Durable SelfAware Full-Run Comparison

- at: `2026-06-24T18:30:52Z`
- kind: `result`
- summary: Materialized full SelfAware comparison CSVs from checked-in
  `metrics.json` artifacts so seed-level and grouped evidence are durable
  outside chat.
- evidence:
  - `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
- interpretation: The grouped CSV keeps protocol families separate. It should
  be used as a comparison index, not as a pooled leaderboard. The balanced
  behavior score is exploratory and unregistered.

### 002-amendment - GRPO-Centered Stacking Draft

- at: `2026-06-24T18:30:52Z`
- kind: `amendment`
- summary: Drafted Amendment F for four three-stage arms:
  `clean_sft_dpo_grpo`, `clean_sft_kto_grpo`, `clean_sft_grpo_dpo`, and
  `clean_sft_grpo_kto`.
- evidence:
  - `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`
- decision: The draft treats the latest clean Amendment E response-confidence
  lineage as the default source lineage and uses GRPO v2 as the current GRPO
  source unless superseded before launch.
- next: Before launching any Amendment F cell, validate source lineage, merge
  the immediate source model when required, run a bounded merged-source sanity
  eval, and name exact paths/configs in the launch record.
