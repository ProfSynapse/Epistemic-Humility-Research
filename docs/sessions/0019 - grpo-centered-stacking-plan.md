---
schema_version: research-session/v1
session_id: grpo-centered-stacking-plan
title: GRPO-Centered Stacking Plan
status: active
created_at: "2026-06-24T18:30:52Z"
updated_at: "2026-06-24T19:46:33Z"
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
  - id: 003-signoff-and-launch-scope
    at: "2026-06-24T19:24:35Z"
    kind: decision
    title: Amendment F Seed-1 Local Scope Signed
    summary: "Joseph approved moving into the next experiment set after HF publication; Amendment F is signed for the four seed-1 local GRPO-centered three-stage arms only."
    evidence:
      - experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md
      - experiment/notes/clean-sft-dpo-grpo.md
      - experiment/notes/clean-sft-kto-grpo.md
      - experiment/notes/clean-sft-grpo-dpo.md
      - experiment/notes/clean-sft-grpo-kto.md
    run_ids:
      - clean_sft_dpo_grpo_seed1
      - clean_sft_kto_grpo_seed1
      - clean_sft_grpo_dpo_seed1
      - clean_sft_grpo_kto_seed1
    commands:
      - docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
      - nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
    decisions:
      - "Launch order starts with `clean_sft_dpo_grpo` after merging the clean SFT->DPO seed-1 adapter onto the clean SFT merged base and running a bounded sanity eval."
      - "Adapters and merged models remain unpublished until each cell passes run/eval provenance gates."
    next_steps:
      - "Merge the clean SFT->DPO seed-1 adapter into a local `merged-16bit` source for `clean_sft_dpo_grpo`."
      - "Create or verify the GRPO config points at the merged SFT->DPO source model."
      - "Run bounded SelfAware sanity eval before the full GRPO launch."
    signals:
      gpu: "RTX 3090 idle at 1 MiB used before launch prep"
      docker: "no active containers before launch prep"
  - id: 004-clean-sft-dpo-grpo-launch
    at: "2026-06-24T19:46:33Z"
    kind: launch
    title: Clean SFT -> DPO -> GRPO Seed 1 Launched
    summary: "Merged the clean SFT->DPO seed-1 adapter onto the clean SFT merged base, ran the bounded merged-source sanity eval, and launched the full Amendment F `clean_sft_dpo_grpo` GRPO run."
    evidence:
      - experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_local_4b.yaml
      - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_4b/clean_sft_dpo_merged_seed1_sanity__selfaware/metrics.json
      - experiment/phase1/grpo/configs/grpo_clean_sft_dpo_grpo_seed1_full.yaml
      - scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/Qwen3-4B-clean-sft-dpo/merged-16bit
      - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/logs/training_20260624_194041.jsonl
    run_ids:
      - clean_sft_dpo_grpo_seed1
    commands:
      - docker run --rm --gpus all --ipc=host --entrypoint python3 ... shared.model_loading.merge.merge_lora_checkpoint(...)
      - docker run -d --name eh-amend-f-dpo-merged-sanity-20260624a ... experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_local_4b.yaml --live-vllm
      - docker run -d --name eh-clean-sft-dpo-grpo-seed1-full-20260624a ... synaptic-tuner/Trainers/grpo/train_grpo.py --config experiment/phase1/grpo/configs/grpo_clean_sft_dpo_grpo_seed1_full.yaml
    decisions:
      - "The source sanity eval passed the launch gate with exit 0, 192/192 response-confidence coverage, and in-family DPO-source behavior."
      - "The full GRPO run is permitted to continue because step-25 telemetry shows low OOM risk and active non-degenerate reward variance."
    next_steps:
      - "Monitor the full GRPO run through completion."
      - "After completion, inspect final artifacts and reward logs, then run the full SelfAware eval before moving to the next Amendment F arm."
    signals:
      sanity_truthful_pct: 50.0
      sanity_refusal_recall_pct: 87.37
      sanity_answer_on_unknown_pct: 12.63
      sanity_over_refusal_pct: 61.86
      sanity_confidence_coverage_pct: 100.0
      training_container: eh-clean-sft-dpo-grpo-seed1-full-20260624a
      training_run_dir: scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929
      step_25_oom_risk: low
      step_25_gpu_vram_used_gb: 11.256
      step_25_reward_mean: 0.4759260141849518
      step_25_reward_std: 1.278914223909378
      step_25_frac_reward_zero_std: 0.02
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

### 003-signoff-and-launch-scope - Amendment F Seed-1 Local Scope Signed

- at: `2026-06-24T19:24:35Z`
- kind: `decision`
- summary: Joseph approved moving into the next experiment set after HF
  publication; Amendment F is signed for the four seed-1 local GRPO-centered
  three-stage arms only.
- evidence:
  - `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`
  - `experiment/notes/clean-sft-dpo-grpo.md`
  - `experiment/notes/clean-sft-kto-grpo.md`
  - `experiment/notes/clean-sft-grpo-dpo.md`
  - `experiment/notes/clean-sft-grpo-kto.md`
- decision: Launch order starts with `clean_sft_dpo_grpo` after merging the
  clean SFT->DPO seed-1 adapter onto the clean SFT merged base and running a
  bounded sanity eval.
- gate: Docker had no active containers and the RTX 3090 was idle at 1 MiB used
  before launch prep.
- next: Merge the DPO source, create or verify the GRPO config, run the bounded
  sanity eval, and only then launch the full GRPO cell.

### 004-clean-sft-dpo-grpo-launch - Clean SFT -> DPO -> GRPO Seed 1 Launched

- at: `2026-06-24T19:46:33Z`
- kind: `launch`
- summary: Merged the clean SFT->DPO seed-1 adapter onto the clean SFT merged
  base, ran the bounded merged-source sanity eval, and launched the full
  Amendment F `clean_sft_dpo_grpo` GRPO run.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_4b/clean_sft_dpo_merged_seed1_sanity__selfaware/metrics.json`
  - `experiment/phase1/grpo/configs/grpo_clean_sft_dpo_grpo_seed1_full.yaml`
  - `scratch/schema_response_confidence/runs/schema_clean_sft_dpo_seed1_full/20260623_132930/Qwen3-4B-clean-sft-dpo/merged-16bit`
  - `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/logs/training_20260624_194041.jsonl`
- sanity eval: exit 0; `n=192`; response-confidence coverage `100%`;
  truthful `50.0%`; unknown refusal recall `87.37%`; unknown answer rate
  `12.63%`; known over-refusal `61.86%`.
- launch: container `eh-clean-sft-dpo-grpo-seed1-full-20260624a`, run dir
  `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929`.
- first telemetry: step 25/1861, OOM risk `low`, live VRAM about `11.256 GB`,
  reward mean `0.4759`, reward std `1.2789`, fraction zero reward std `0.02`.
- next: monitor to completion, inspect final artifacts/reward logs, then run the
  full SelfAware eval before starting the next Amendment F arm.
