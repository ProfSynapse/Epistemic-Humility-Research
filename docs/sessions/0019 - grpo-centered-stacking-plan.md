---
schema_version: research-session/v1
session_id: grpo-centered-stacking-plan
title: GRPO-Centered Stacking Plan
status: active
created_at: "2026-06-24T18:30:52Z"
updated_at: "2026-06-25T01:29:50Z"
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
  - id: 005-clean-sft-dpo-grpo-train-complete-eval-launch
    at: "2026-06-25T00:42:45Z"
    kind: result
    title: Clean SFT -> DPO -> GRPO Seed 1 Training Complete And Full Eval Launched
    summary: "The Amendment F `clean_sft_dpo_grpo` seed-1 GRPO run exited 0 after 1861 steps, wrote final adapter artifacts, and the full 3369-row SelfAware eval was launched with the adapter on the merged SFT->DPO source model."
    evidence:
      - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/final_model
      - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/training_lineage.json
      - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/capacity_features.json
      - experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_local_4b.yaml
    run_ids:
      - clean_sft_dpo_grpo_seed1
    commands:
      - docker ps -a --filter "name=eh-clean-sft-dpo-grpo-seed1-full-20260624a" --format "{{.Names}}\t{{.Status}}"
      - docker run -d --name eh-clean-sft-dpo-grpo-full-eval-20260625a ... experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_local_4b.yaml --live-vllm
    decisions:
      - "Do not interpret the three-stage arm until the full SelfAware eval completes and row/sample sanity checks pass."
      - "Use the merged SFT->DPO model as `model_name` and the GRPO `final_model` as the eval adapter."
    next_steps:
      - "Monitor `eh-clean-sft-dpo-grpo-full-eval-20260625a` to completion."
      - "Inspect metrics, confidence distribution, and sample rows before moving to the next Amendment F arm."
      - "Update durable comparison CSVs after metrics land."
    signals:
      training_container_status: "Exited (0)"
      final_step: 1861
      total_epochs: 1.0
      final_loss: 0.1629
      peak_reserved_vram_pct: 57.99
      oom_risk: low
      eval_container: eh-clean-sft-dpo-grpo-full-eval-20260625a
  - id: 006-clean-sft-dpo-grpo-full-eval-result
    at: "2026-06-25T01:11:34Z"
    kind: result
    title: Clean SFT -> DPO -> GRPO Seed 1 Full Eval Complete
    summary: "The full SelfAware eval completed with 100% response-confidence coverage and no thinking contamination. Behavior moved toward the SFT->GRPO v2 profile: lower unknown answering than DPO, but high known over-refusal."
    evidence:
      - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b/clean_sft_dpo_grpo_seed1__selfaware/metrics.json
      - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b/clean_sft_dpo_grpo_seed1__selfaware/scored_rows.jsonl
      - experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv
      - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
    run_ids:
      - clean_sft_dpo_grpo_seed1
    commands:
      - docker ps -a --filter "name=eh-clean-sft-dpo-grpo-full-eval-20260625a" --format "{{.Names}}\t{{.Status}}"
      - python experiment\\phase1\\eval\\analysis\\build_selfaware_full_run_comparison.py
    decisions:
      - "Treat `clean_sft_dpo_grpo` as an interpretable tradeoff result, not as a solved humility/calibration cell."
      - "Continue to `clean_sft_kto_grpo` because it tests whether the gentler KTO-warmed source changes the GRPO tradeoff."
    next_steps:
      - "Merge the clean SFT->KTO seed-1 adapter onto the clean SFT merged base."
      - "Run the bounded merged-source sanity eval before launching KTO->GRPO."
    signals:
      n: 3369
      truthful_pct: 41.2
      refusal_recall_pct: 93.31
      answer_on_unknown_pct: 6.69
      over_refusal_pct: 65.3
      correct_on_known_pct: 52.4
      confidence_coverage_pct: 100.0
      unique_response_confidence_values: 70
      mean_response_confidence: 0.844615
      brier_vs_response_appropriateness: 0.428793
      mean_confidence_known_correct: 0.8437
      mean_confidence_known_refused: 0.8462
      mean_confidence_unknown_abstain: 0.8478
      mean_confidence_unknown_answer: 0.8284
  - id: 007-clean-sft-kto-grpo-launch
    at: "2026-06-25T01:29:50Z"
    kind: launch
    title: Clean SFT -> KTO -> GRPO Seed 1 Launched
    summary: "Merged the clean SFT->KTO seed-1 adapter onto the clean SFT merged base, ran the bounded merged-source sanity eval, and launched the full Amendment F `clean_sft_kto_grpo` GRPO run."
    evidence:
      - scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/Qwen3-4B-clean-sft-kto/merged-16bit
      - experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_local_4b.yaml
      - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_4b/clean_sft_kto_merged_seed1_sanity__selfaware/metrics.json
      - experiment/phase1/grpo/configs/grpo_clean_sft_kto_grpo_seed1_full.yaml
      - scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/logs/training_20260625_012419.jsonl
    run_ids:
      - clean_sft_kto_grpo_seed1
    commands:
      - docker run --rm --gpus all --ipc=host --entrypoint python3 ... shared.model_loading.merge.merge_lora_checkpoint(...)
      - docker run -d --name eh-amend-f-kto-merged-sanity-20260625a ... experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_local_4b.yaml --live-vllm
      - docker run -d --name eh-clean-sft-kto-grpo-seed1-full-20260625a ... synaptic-tuner/Trainers/grpo/train_grpo.py --config experiment/phase1/grpo/configs/grpo_clean_sft_kto_grpo_seed1_full.yaml
    decisions:
      - "The merged KTO source sanity eval passed the gate with in-family KTO behavior and no schema/thinking contamination."
      - "The full KTO->GRPO run is permitted to continue because step-25 telemetry shows low OOM risk and active reward variance."
    next_steps:
      - "Monitor the full KTO->GRPO run through checkpoints and completion."
      - "After completion, inspect final artifacts and run the full SelfAware eval."
    signals:
      sanity_n: 192
      sanity_truthful_pct: 49.48
      sanity_refusal_recall_pct: 84.21
      sanity_answer_on_unknown_pct: 15.79
      sanity_over_refusal_pct: 58.76
      sanity_confidence_coverage_pct: 100.0
      training_container: eh-clean-sft-kto-grpo-seed1-full-20260625a
      training_run_dir: scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319
      step_25_oom_risk: low
      step_25_gpu_vram_used_gb: 11.25
      step_25_reward_mean: 0.4271456325054169
      step_25_reward_std: 1.4526790952682496
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

### 005-clean-sft-dpo-grpo-train-complete-eval-launch - Clean SFT -> DPO -> GRPO Seed 1 Training Complete And Full Eval Launched

- at: `2026-06-25T00:42:45Z`
- kind: `result`
- summary: The Amendment F `clean_sft_dpo_grpo` seed-1 GRPO run exited `0`
  after `1861` steps, wrote final adapter artifacts, and the full 3369-row
  SelfAware eval was launched with the adapter on the merged SFT->DPO source
  model.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/final_model`
  - `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/training_lineage.json`
  - `scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_local_4b.yaml`
- training result: final step `1861`, total epochs `1.0`, final loss
  `0.1629`, peak reserved VRAM `57.99%`, OOM risk `low`.
- eval launch: container `eh-clean-sft-dpo-grpo-full-eval-20260625a`.
- decision: Do not interpret the three-stage arm until the full SelfAware eval
  completes and row/sample sanity checks pass.
- next: monitor eval completion, inspect metrics/confidence/sample rows, then
  update the durable comparison CSVs before deciding the next Amendment F arm.

### 006-clean-sft-dpo-grpo-full-eval-result - Clean SFT -> DPO -> GRPO Seed 1 Full Eval Complete

- at: `2026-06-25T01:11:34Z`
- kind: `result`
- summary: The full SelfAware eval completed with `100%` response-confidence
  coverage, no thinking contamination, and `70` distinct confidence values.
- metrics: `truthful_pct=41.2`, `refusal_recall_pct=93.31`,
  `answer_on_unknown_pct=6.69`, `over_refusal_pct=65.3`,
  `correct_on_known_pct=52.4`, mean response confidence `0.844615`, Brier vs
  response appropriateness `0.428793`.
- comparison: against immediate `clean_sft_dpo`, GRPO reduced unknown answering
  from `12.89%` to `6.69%`, but raised known over-refusal from `56.18%` to
  `65.3%`. The profile is close to `clean_sft_grpo_v2`
  (`answer_on_unknown_pct=6.59`, `over_refusal_pct=66.62`).
- confidence sanity: behavioral-cell means remain clustered
  (`known_correct=0.8437`, `known_refused=0.8462`,
  `unknown_abstain=0.8478`, `unknown_answer=0.8284`), so this is not yet
  calibrated response-confidence behavior.
- decision: Continue to `clean_sft_kto_grpo`; it directly tests whether the
  gentler KTO-warmed source changes the GRPO tradeoff.

### 007-clean-sft-kto-grpo-launch - Clean SFT -> KTO -> GRPO Seed 1 Launched

- at: `2026-06-25T01:29:50Z`
- kind: `launch`
- summary: Merged the clean SFT->KTO seed-1 adapter onto the clean SFT merged
  base, ran the bounded merged-source sanity eval, and launched the full
  Amendment F `clean_sft_kto_grpo` GRPO run.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_kto_seed1_full/20260623_200200/Qwen3-4B-clean-sft-kto/merged-16bit`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_4b/clean_sft_kto_merged_seed1_sanity__selfaware/metrics.json`
  - `experiment/phase1/grpo/configs/grpo_clean_sft_kto_grpo_seed1_full.yaml`
  - `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/logs/training_20260625_012419.jsonl`
- sanity eval: exit 0; `n=192`; response-confidence coverage `100%`;
  truthful `49.48%`; unknown refusal recall `84.21%`; unknown answer rate
  `15.79%`; known over-refusal `58.76%`.
- launch: container `eh-clean-sft-kto-grpo-seed1-full-20260625a`, run dir
  `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319`.
- first telemetry: step 25/1861, OOM risk `low`, live VRAM about `11.25 GB`,
  reward mean `0.4271`, reward std `1.4527`, fraction zero reward std `0.02`.
- next: monitor through checkpoints and completion; then inspect final artifacts
  and run the full SelfAware eval.
