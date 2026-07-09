---
schema_version: research-session/v1
session_id: 20260624T183052Z-grpo-centered-stacking-plan
title: GRPO-Centered Stacking Plan
status: active
created_at: '2026-06-24T18:30:52Z'
updated_at: '2026-06-25T11:50:55Z'
phase: phase1
question: Which completed local SelfAware runs are strongest so far, and should the
  next training extension test GRPO as a third-stage stack with DPO/KTO?
tags:
- experiment-runner
- amendment-f
- response-confidence
- grpo
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: After Amendment E clean response-confidence SFT, DPO, KTO, GRPO
    v1, and GRPO v2 seed-1 evals; before any GRPO-centered three-stage launches.
  changed_by_session: Adds durable run comparison artifacts and drafts Amendment F
    for GRPO-centered stacking.
checkpoints:
- id: 001-analysis
  at: '2026-06-24T18:30:52Z'
  kind: result
  title: Durable SelfAware Full-Run Comparison
  summary: Materialized full SelfAware comparison CSVs from checked-in metrics.json
    artifacts so seed-level and grouped evidence are durable outside chat.
  evidence:
  - experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  run_ids: []
  commands:
  - python experiment\\phase1\\eval\\analysis\\build_selfaware_full_run_comparison.py
  decisions:
  - Keep protocol families separate and treat the balanced behavior score as exploratory/unregistered.
  next_steps:
  - Use grouped CSV as the quick comparison index and per-run CSV for seed-level provenance.
  signals: {}
- id: 002-amendment
  at: '2026-06-24T18:30:52Z'
  kind: amendment
  title: GRPO-Centered Stacking Draft
  summary: Drafted Amendment F for clean_sft_dpo_grpo, clean_sft_kto_grpo, clean_sft_grpo_dpo,
    and clean_sft_grpo_kto.
  evidence:
  - experiments/grpo-centered-stacking/AMENDMENT.md
  run_ids: []
  commands: []
  decisions:
  - Use the latest clean Amendment E response-confidence lineage by default, with
    GRPO v2 as the current GRPO source unless superseded.
  next_steps:
  - Before launching, validate source lineage, merge immediate source models, run
    bounded merged-source sanity evals, and name exact paths/configs in launch records.
  signals: {}
- id: 003-signoff-and-launch-scope
  at: '2026-06-24T19:24:35Z'
  kind: decision
  title: Amendment F Seed-1 Local Scope Signed
  summary: Joseph approved moving into the next experiment set after HF publication;
    Amendment F is signed for the four seed-1 local GRPO-centered three-stage arms
    only.
  evidence:
  - experiments/grpo-centered-stacking/AMENDMENT.md
  - notes/experiments/clean-sft-dpo-grpo.md
  - notes/experiments/clean-sft-kto-grpo.md
  - notes/experiments/clean-sft-grpo-dpo.md
  - notes/experiments/clean-sft-grpo-kto.md
  run_ids:
  - clean_sft_dpo_grpo_seed1
  - clean_sft_kto_grpo_seed1
  - clean_sft_grpo_dpo_seed1
  - clean_sft_grpo_kto_seed1
  commands:
  - docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
  - nvidia-smi --query-gpu=name,memory.used,memory.total,utilization.gpu --format=csv,noheader
  decisions:
  - Launch order starts with `clean_sft_dpo_grpo` after merging the clean SFT->DPO
    seed-1 adapter onto the clean SFT merged base and running a bounded sanity eval.
  - Adapters and merged models remain unpublished until each cell passes run/eval
    provenance gates.
  next_steps:
  - Merge the clean SFT->DPO seed-1 adapter into a local `merged-16bit` source for
    `clean_sft_dpo_grpo`.
  - Create or verify the GRPO config points at the merged SFT->DPO source model.
  - Run bounded SelfAware sanity eval before the full GRPO launch.
  signals:
    gpu: RTX 3090 idle at 1 MiB used before launch prep
    docker: no active containers before launch prep
- id: 004-clean-sft-dpo-grpo-launch
  at: '2026-06-24T19:46:33Z'
  kind: launch
  title: Clean SFT -> DPO -> GRPO Seed 1 Launched
  summary: Merged the clean SFT->DPO seed-1 adapter onto the clean SFT merged base,
    ran the bounded merged-source sanity eval, and launched the full Amendment F `clean_sft_dpo_grpo`
    GRPO run.
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
  - docker run -d --name eh-amend-f-dpo-merged-sanity-20260624a ... experiment/phase1/eval/run_eval.py
    --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_merged_seed1_sanity_local_4b.yaml
    --live-vllm
  - docker run -d --name eh-clean-sft-dpo-grpo-seed1-full-20260624a ... synaptic-tuner/Trainers/grpo/train_grpo.py
    --config experiment/phase1/grpo/configs/grpo_clean_sft_dpo_grpo_seed1_full.yaml
  decisions:
  - The source sanity eval passed the launch gate with exit 0, 192/192 response-confidence
    coverage, and in-family DPO-source behavior.
  - The full GRPO run is permitted to continue because step-25 telemetry shows low
    OOM risk and active non-degenerate reward variance.
  next_steps:
  - Monitor the full GRPO run through completion.
  - After completion, inspect final artifacts and reward logs, then run the full SelfAware
    eval before moving to the next Amendment F arm.
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
  at: '2026-06-25T00:42:45Z'
  kind: result
  title: Clean SFT -> DPO -> GRPO Seed 1 Training Complete And Full Eval Launched
  summary: The Amendment F `clean_sft_dpo_grpo` seed-1 GRPO run exited 0 after 1861
    steps, wrote final adapter artifacts, and the full 3369-row SelfAware eval was
    launched with the adapter on the merged SFT->DPO source model.
  evidence:
  - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/final_model
  - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/training_lineage.json
  - scratch/schema_response_confidence/runs/clean_sft_dpo_grpo_seed1_full/20260624_193929/capacity_features.json
  - experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_local_4b.yaml
  run_ids:
  - clean_sft_dpo_grpo_seed1
  commands:
  - docker ps -a --filter "name=eh-clean-sft-dpo-grpo-seed1-full-20260624a" --format
    "{{.Names}}\t{{.Status}}"
  - docker run -d --name eh-clean-sft-dpo-grpo-full-eval-20260625a ... experiment/phase1/eval/run_eval.py
    --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_local_4b.yaml
    --live-vllm
  decisions:
  - Do not interpret the three-stage arm until the full SelfAware eval completes and
    row/sample sanity checks pass.
  - Use the merged SFT->DPO model as `model_name` and the GRPO `final_model` as the
    eval adapter.
  next_steps:
  - Monitor `eh-clean-sft-dpo-grpo-full-eval-20260625a` to completion.
  - Inspect metrics, confidence distribution, and sample rows before moving to the
    next Amendment F arm.
  - Update durable comparison CSVs after metrics land.
  signals:
    training_container_status: Exited (0)
    final_step: 1861
    total_epochs: 1.0
    final_loss: 0.1629
    peak_reserved_vram_pct: 57.99
    oom_risk: low
    eval_container: eh-clean-sft-dpo-grpo-full-eval-20260625a
- id: 006-clean-sft-dpo-grpo-full-eval-result
  at: '2026-06-25T01:11:34Z'
  kind: result
  title: Clean SFT -> DPO -> GRPO Seed 1 Full Eval Complete
  summary: 'The full SelfAware eval completed with 100% response-confidence coverage
    and no thinking contamination. Behavior moved toward the SFT->GRPO v2 profile:
    lower unknown answering than DPO, but high known over-refusal.'
  evidence:
  - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b/clean_sft_dpo_grpo_seed1__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_dpo_grpo_seed1_full_4b/clean_sft_dpo_grpo_seed1__selfaware/scored_rows.jsonl
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  run_ids:
  - clean_sft_dpo_grpo_seed1
  commands:
  - docker ps -a --filter "name=eh-clean-sft-dpo-grpo-full-eval-20260625a" --format
    "{{.Names}}\t{{.Status}}"
  - python experiment\\phase1\\eval\\analysis\\build_selfaware_full_run_comparison.py
  decisions:
  - Treat `clean_sft_dpo_grpo` as an interpretable tradeoff result, not as a solved
    humility/calibration cell.
  - Continue to `clean_sft_kto_grpo` because it tests whether the gentler KTO-warmed
    source changes the GRPO tradeoff.
  next_steps:
  - Merge the clean SFT->KTO seed-1 adapter onto the clean SFT merged base.
  - Run the bounded merged-source sanity eval before launching KTO->GRPO.
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
  at: '2026-06-25T01:29:50Z'
  kind: launch
  title: Clean SFT -> KTO -> GRPO Seed 1 Launched
  summary: Merged the clean SFT->KTO seed-1 adapter onto the clean SFT merged base,
    ran the bounded merged-source sanity eval, and launched the full Amendment F `clean_sft_kto_grpo`
    GRPO run.
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
  - docker run -d --name eh-amend-f-kto-merged-sanity-20260625a ... experiment/phase1/eval/run_eval.py
    --config experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_merged_seed1_sanity_local_4b.yaml
    --live-vllm
  - docker run -d --name eh-clean-sft-kto-grpo-seed1-full-20260625a ... synaptic-tuner/Trainers/grpo/train_grpo.py
    --config experiment/phase1/grpo/configs/grpo_clean_sft_kto_grpo_seed1_full.yaml
  decisions:
  - The merged KTO source sanity eval passed the gate with in-family KTO behavior
    and no schema/thinking contamination.
  - The full KTO->GRPO run is permitted to continue because step-25 telemetry shows
    low OOM risk and active reward variance.
  next_steps:
  - Monitor the full KTO->GRPO run through checkpoints and completion.
  - After completion, inspect final artifacts and run the full SelfAware eval.
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
- id: 008-decision
  at: '2026-06-25T11:50:55Z'
  kind: decision
  title: Amendment F Complete And Next Evidence Fork
  summary: All four Amendment F seed-1 local GRPO-centered stack arms completed training
    and full SelfAware evals. The strongest seed-1 stack is clean_sft_grpo_dpo, but
    its advantage is modest and all Amendment F arms still show high, behavior-insensitive
    response confidence.
  evidence:
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  - notes/experiments/clean-sft-grpo-dpo.md
  - notes/experiments/clean-sft-grpo-kto.md
  run_ids: []
  commands: []
  decisions:
  - Do not treat any Amendment F arm as a solved confidence-calibrated humility policy.
  - If the next goal is a pristine public evidence set, prioritize rebuilding and
    evaluating clean response-confidence clean_sft_grpo_dpo seeds 2/3 before publishing
    merged models.
  next_steps:
  - Checkpoint the completed Amendment F artifacts in git before launching additional
    GPU work.
  - Draft a governed seed-replication extension or launch plan for clean SFT -> GRPO
    v2 -> DPO seeds 2/3 if Joseph approves the compute spend.
  signals: {}
legacy_session:
  id: grpo-centered-stacking-plan
  path: docs/sessions/0019 - grpo-centered-stacking-plan.md
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
  - `experiments/grpo-centered-stacking/AMENDMENT.md`
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
  - `experiments/grpo-centered-stacking/AMENDMENT.md`
  - `notes/experiments/clean-sft-dpo-grpo.md`
  - `notes/experiments/clean-sft-kto-grpo.md`
  - `notes/experiments/clean-sft-grpo-dpo.md`
  - `notes/experiments/clean-sft-grpo-kto.md`
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

### 008-clean-sft-kto-grpo-train-complete-eval-launch - Clean SFT -> KTO -> GRPO Seed 1 Training Complete And Full Eval Launched

- at: `2026-06-25T06:46:57Z`
- kind: `result`
- summary: The Amendment F `clean_sft_kto_grpo` seed-1 GRPO run exited `0`
  after `1861` steps, wrote final adapter artifacts, and the full 3369-row
  SelfAware eval was launched with the adapter on the merged SFT->KTO source
  model.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/final_model`
  - `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/training_lineage.json`
  - `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_local_4b.yaml`
- training result: final step `1861`, total epochs `1.0`, final loss
  `0.1162`, peak reserved VRAM `72.62%`, OOM risk `low`.
- eval launch: container `eh-clean-sft-kto-grpo-full-eval-20260625a`.
- next setup: prepared the bounded merged-source sanity eval config for the
  next Amendment F source, `clean_sft_grpo_v2_merged_seed1_sanity`, at
  `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_local_4b.yaml`.
- decision: Do not launch the GRPO-v2 source merge or the `clean_sft_grpo_dpo`
  arm until the active `clean_sft_kto_grpo` full eval completes and passes
  post-eval sanity checks.

### 009-clean-sft-kto-grpo-full-eval-result - Clean SFT -> KTO -> GRPO Seed 1 Full Eval Complete

- at: `2026-06-25T07:08:00Z`
- kind: `result`
- summary: The full SelfAware eval for `clean_sft_kto_grpo` completed cleanly
  with `100%` response-confidence coverage, no thinking contamination, and zero
  schema retries.
- evidence:
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_4b/clean_sft_kto_grpo_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_kto_grpo_seed1_full_4b/clean_sft_kto_grpo_seed1__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
- metrics: `truthful_pct=40.84`, `refusal_recall_pct=92.54`,
  `answer_on_unknown_pct=7.46`, `over_refusal_pct=66.37`,
  `correct_on_known_pct=53.56`, mean response confidence `0.862188`, Brier vs
  response appropriateness `0.447663`.
- confidence sanity: only `5` distinct confidence values on `3369` rows; all
  behavioral-cell means cluster near `0.862`, so this remains a stated
  confidence collapse rather than calibrated response appropriateness.
- interpretation: KTO-warmed GRPO did not materially beat DPO-warmed GRPO or
  direct clean SFT->GRPO v2. It reduced KTO's high unknown-answering failure
  but returned to the familiar GRPO-final tradeoff: low unknown answering with
  high known-row over-refusal.

### 010-clean-sft-grpo-dpo-launch - Clean SFT -> GRPO -> DPO Seed 1 Launched

- at: `2026-06-25T07:22:15Z`
- kind: `launch`
- summary: Merged the clean SFT->GRPO v2 seed-1 adapter onto the clean SFT
  merged base, verified the merged source against the same 192-row slice as the
  adapter-on-base eval, and launched the full Amendment F `clean_sft_grpo_dpo`
  DPO run.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/Qwen3-4B-clean-sft-grpo-v2/merged-16bit`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_4b/clean_sft_grpo_v2_merged_seed1_sanity__selfaware/metrics.json`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/logs/training_20260625_071912.jsonl`
- merged-source sanity: exit 0; `n=192`; response-confidence coverage `100%`;
  truthful `50.52%`; unknown refusal recall `90.53%`; unknown answer rate
  `9.47%`; known over-refusal `75.26%`.
- merge equivalence gate: the adapter-on-base GRPO v2 full eval on the same
  offset slice was effectively matched (`truthful_pct=50.52`,
  `answer_on_unknown_pct=8.42`, `over_refusal_pct=77.32`), so the merged source
  is treated as semantically valid.
- launch: container `eh-clean-sft-grpo-dpo-seed1-full-20260625a`, run dir
  `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724`.
- first telemetry: step `60/1868`, OOM risk `low`, peak reserved VRAM
  `8.543 GB`, live card VRAM about `8.877 GB`, reward margin `0.2936`, reward
  accuracy `0.80`.
- decision: Keep the conservative DPO batch `2` / accumulation `4` for this
  first GRPO->DPO arm because prior DPO batch-4 full runs showed late VRAM
  growth; revisit speed only after the behavioral objective is worth rerunning.

### 011-clean-sft-grpo-dpo-progress - DPO Memory Growth Window Cleared

- at: `2026-06-25T07:39:30Z`
- kind: `heartbeat`
- summary: The `clean_sft_grpo_dpo` DPO run cleared the historical early
  memory-growth window without VRAM risk.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/logs/training_20260625_071912.jsonl`
- progress: step `440/1868`, OOM risk `low`, max reserved VRAM `11.203 GB`,
  live card VRAM about `9.367 GB`.
- observation: DPO separation is saturating quickly (`rewards/accuracies=1.0`,
  `rewards/margins` above `11` near step 440). This is treated as behavioral
  evidence to evaluate after the full run, not as an infrastructure reason to
  stop, because the arm is intended to be comparable to prior one-epoch DPO
  settings.

### 012-clean-sft-grpo-dpo-train-complete-eval-launch - Clean SFT -> GRPO -> DPO Seed 1 Training Complete And Full Eval Launched

- at: `2026-06-25T08:46:00Z`
- kind: `result`
- summary: The Amendment F `clean_sft_grpo_dpo` seed-1 DPO run exited `0`
  after `1868` steps, wrote final adapter artifacts, and the full 3369-row
  SelfAware eval was prepared for the adapter on the merged SFT->GRPO v2 source
  model.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/final_model`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/training_lineage.json`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_local_4b.yaml`
- training result: final step `1868`, total epochs `1.0`, train runtime
  `5068.499s`, peak reserved VRAM `46.68%`, OOM risk `low`.
- training observation: DPO reached near-perfect preference separation for much
  of the run (`rewards/accuracies=1.0`, final observed margins around `13.8`).
  The eval must decide whether this recovers known answers or simply produces
  another overconfident preference-distorted policy.

### 013-clean-sft-grpo-dpo-full-eval-result - Clean SFT -> GRPO -> DPO Seed 1 Full Eval Complete

- at: `2026-06-25T09:19:00Z`
- kind: `result`
- summary: The full SelfAware eval for `clean_sft_grpo_dpo` completed cleanly
  with `100%` response-confidence coverage, no thinking contamination, zero
  schema retries, and a structurally sane row count.
- evidence:
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b/clean_sft_grpo_dpo_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_4b/clean_sft_grpo_dpo_seed1__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
- metrics: `truthful_pct=41.64`, `refusal_recall_pct=93.31`,
  `answer_on_unknown_pct=6.69`, `over_refusal_pct=63.63`,
  `correct_on_known_pct=51.76`, mean response confidence `0.866301`, Brier vs
  response appropriateness `0.445413`.
- confidence sanity: `38` distinct confidence values on `3369` rows, but all
  behavioral-cell means cluster high (`known_correct=0.862274`,
  `known_refused=0.868638`, `known_wrong_answer=0.858148`,
  `unknown_abstain=0.868605`, `unknown_answer=0.857903`). This remains
  confidence amplification rather than calibrated response appropriateness.
- interpretation: DPO after GRPO did not re-open unknown answering and did trim
  known over-refusal slightly versus direct GRPO v2 (`66.62% -> 63.63%`), but
  the gain is modest and confidence worsened. Treat this as another
  GRPO-boundary-preserving stack, not a solved epistemic-humility policy.

### 014-clean-sft-grpo-kto-launch - Clean SFT -> GRPO -> KTO Seed 1 Launched

- at: `2026-06-25T09:31:00Z`
- kind: `launch`
- summary: Launched the final Amendment F seed-1 local stack,
  `clean_sft_grpo_kto`, using the already sanity-gated merged clean SFT->GRPO
  v2 source model as the KTO base.
- evidence:
  - `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/Qwen3-4B-clean-sft-grpo-v2/merged-16bit`
  - `scratch/schema_response_confidence/qwen3-4b-instruct/kto_response_confidence_train.jsonl`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
- launch: container `eh-clean-sft-grpo-kto-seed1-full-20260625a`, run dir
  `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610`.
- training configuration: `29886` examples, `2491` total steps, batch `12`,
  accumulation `1`, learning rate `1e-6`, beta `0.1`, seed `1`, LoRA rank
  `32`, alpha `64`, dropout `0.05`.
- first telemetry: dataset validation passed with balanced labels (`14943`
  true / `14943` false); model loaded from the GRPO-v2 merged source; live VRAM
  around `13.25 GB` during transition into training, so the provisional batch
  `12` plan remains acceptable for now.
- next: inspect the first logged training metrics and monitor near the
  historical KTO checkpoint window before accepting the batch size for the full
  run.

### 015-clean-sft-grpo-kto-early-telemetry - KTO Batch 12 Early Window Looks Safe

- at: `2026-06-25T09:33:00Z`
- kind: `heartbeat`
- summary: The `clean_sft_grpo_kto` run reached step `100/2491` with low VRAM
  risk and stable logging.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
- progress: step `100/2491`, elapsed `238.881s`, throughput about `0.419`
  steps/s and `5.023` samples/s.
- capacity: max reserved VRAM `12.605 GB` (`52.52%`), live card VRAM about
  `12.939 GB`, OOM risk `low`.
- training signal: loss remains near `0.499` and reward margins are still small
  in warmup; this is not yet behavioral evidence, only a capacity and liveness
  gate.
- decision: Keep batch `12` for now and re-check near step `250`.

### 016-clean-sft-grpo-kto-step-250-gate - KTO Batch 12 Accepted Past Early Checkpoint

- at: `2026-06-25T09:40:00Z`
- kind: `validation`
- summary: The `clean_sft_grpo_kto` run passed the step-250 monitoring gate
  without VRAM escalation or obvious objective instability.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/checkpoints/checkpoint-250`
- progress: step `250/2491`; checkpoint `checkpoint-250` written.
- capacity: max reserved VRAM `16.639 GB` (`69.33%`) with live `nvidia-smi`
  around `12.534 GB`; OOM risk remained `low`.
- objective telemetry: loss decreased to `0.4735`, reward margin rose to
  `0.2128`, and KL was `0.4377` at step 250. This shows KTO separation
  emerging, not a runaway spike at this checkpoint.
- decision: Continue the full run at batch `12` / accumulation `1`; next poll
  can be longer unless VRAM or KL behavior changes.

### 017-clean-sft-grpo-kto-midrun - KTO Objective Separates Hard Again

- at: `2026-06-25T10:01:00Z`
- kind: `observation`
- summary: At the mid-run check, `clean_sft_grpo_kto` was stable on hardware
  but had already reached strong KTO reward separation, matching the earlier
  KTO pattern where training separation did not guarantee better SelfAware
  behavior.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_local_4b.yaml`
- progress: latest inspected step `785/2491`, throughput about `0.417`
  steps/s.
- capacity: max reserved VRAM still `16.639 GB` (`69.33%`), live `nvidia-smi`
  around `10.908 GB`, OOM risk `low`.
- objective telemetry: recent loss was near `0.0126`, chosen rewards around
  `4.04`, rejected rewards around `-7.73`, and margins around `11.77`.
- interpretation: This is a useful training-completion signal but not evidence
  of improved epistemic humility. Prior KTO showed strong in-training separation
  while hurting the behavior tradeoff, so the full SelfAware eval remains the
  gate.

### 018-clean-sft-grpo-kto-late-run - KTO Continues With High But Acceptable VRAM

- at: `2026-06-25T10:33:00Z`
- kind: `heartbeat`
- summary: The `clean_sft_grpo_kto` run reached step `1590/2491` with no
  container failure and acceptable capacity, though peak reserved VRAM rose
  above the early window.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
- progress: latest inspected step `1590/2491`, about `64%` through, throughput
  about `0.413` steps/s.
- capacity: max reserved VRAM `19.332 GB` (`80.55%`) with live `nvidia-smi`
  about `16.804 GB`; OOM risk still reported `low`.
- objective telemetry: loss is around `0.0033` and margins remain near `16`,
  indicating a saturated KTO objective.
- interpretation: Continue because the run is stable and near enough to finish,
  but do not treat the saturated objective as success. The full SelfAware eval
  must determine whether GRPO->KTO improved the behavior tradeoff or merely
  repeated KTO's preference-separation artifact.

### 019-clean-sft-grpo-kto-final-stretch - KTO Near Finish With Moderate Peak VRAM

- at: `2026-06-25T10:54:00Z`
- kind: `heartbeat`
- summary: The `clean_sft_grpo_kto` run reached step `2075/2491`, about `83%`
  through, with stable live VRAM but a higher peak reserved-memory watermark.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/logs/training_20260625_092807.jsonl`
- capacity: max reserved VRAM rose to `21.412 GB` (`89.22%`) and the trainer
  reported OOM risk `moderate`; live `nvidia-smi` was lower at about
  `14.574 GB`.
- objective telemetry: loss remained near `0.003`, margins near `15-17`, and
  KL continued to log as `0.0` in the saturated region.
- decision: Continue, but shorten monitoring interval until artifacts are saved
  because the peak reserved watermark has moved from low into moderate risk.

### 020-clean-sft-grpo-kto-train-complete-eval-launch - Clean SFT -> GRPO -> KTO Seed 1 Training Complete And Full Eval Launched

- at: `2026-06-25T11:15:00Z`
- kind: `result`
- summary: The Amendment F `clean_sft_grpo_kto` seed-1 KTO run exited `0`,
  wrote final adapter artifacts, and the full 3369-row SelfAware eval was
  launched with the adapter on the merged SFT->GRPO v2 source model.
- evidence:
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/final_model`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/training_lineage.json`
  - `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/capacity_features.json`
  - `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_local_4b.yaml`
- training result: final step `2491`, total epochs `1.0`, train runtime
  `6159.447s`, final loss `0.0931598`.
- capacity: batch `12` completed without OOM, but peak reserved VRAM reached
  `21.412 GB` (`89.22%`) and final capacity risk was `moderate`; treat batch
  `12` as workable but not roomy for this model/data family.
- training observation: KTO reached saturated preference separation by mid-run,
  with final-region margins around `16-17` and KL logging as `0.0`. The full
  eval must decide whether this improved behavior or repeated the earlier KTO
  pattern of strong training separation without better epistemic humility.
- eval launch: container `eh-clean-sft-grpo-kto-full-eval-20260625a`.

### 021-clean-sft-grpo-kto-full-eval-result - Clean SFT -> GRPO -> KTO Seed 1 Full Eval Complete

- at: `2026-06-25T11:46:00Z`
- kind: `result`
- summary: The full SelfAware eval for `clean_sft_grpo_kto` completed cleanly
  with `100%` response-confidence coverage, no thinking contamination, and zero
  schema retries.
- evidence:
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_4b/clean_sft_grpo_kto_seed1__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_4b/clean_sft_grpo_kto_seed1__selfaware/scored_rows.jsonl`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
- metrics: `truthful_pct=40.90`, `refusal_recall_pct=89.63`,
  `answer_on_unknown_pct=10.37`, `over_refusal_pct=60.59`,
  `correct_on_known_pct=49.19`, mean response confidence `0.864039`, Brier vs
  response appropriateness `0.448626`.
- confidence sanity: only `6` distinct confidence values on `3369` rows; all
  behavioral-cell means cluster near `0.864` (`known_correct=0.864061`,
  `known_refused=0.864242`, `known_wrong_answer=0.863337`,
  `unknown_abstain=0.864321`, `unknown_answer=0.861890`). This is still a
  high-confidence style scalar, not calibrated response appropriateness.
- interpretation: KTO after GRPO did soften GRPO's known over-refusal
  (`66.62% -> 60.59%`) but reopened unknown answering (`6.59% -> 10.37%`) and
  reduced answered-known accuracy (`53.85% -> 49.19%`). Within the Amendment F
  seed-1 stacks, `clean_sft_grpo_dpo` is stronger than `clean_sft_grpo_kto` on
  truthful rate and unknown-answer control; neither solves confidence
  calibration.
### 008-decision - Amendment F Complete And Next Evidence Fork

- at: `2026-06-25T11:50:55Z`
- kind: `decision`
- summary: All four Amendment F seed-1 local GRPO-centered stack arms completed training and full SelfAware evals. The strongest seed-1 stack is clean_sft_grpo_dpo, but its advantage is modest and all Amendment F arms still show high, behavior-insensitive response confidence.
- evidence:
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
  - `notes/experiments/clean-sft-grpo-dpo.md`
  - `notes/experiments/clean-sft-grpo-kto.md`
- decisions:
  - Do not treat any Amendment F arm as a solved confidence-calibrated humility policy.
  - If the next goal is a pristine public evidence set, prioritize rebuilding and evaluating clean response-confidence clean_sft_grpo_dpo seeds 2/3 before publishing merged models.
- next steps:
  - Checkpoint the completed Amendment F artifacts in git before launching additional GPU work.
  - Draft a governed seed-replication extension or launch plan for clean SFT -> GRPO v2 -> DPO seeds 2/3 if Joseph approves the compute spend.
