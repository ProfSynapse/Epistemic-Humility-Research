---
schema_version: research-session/v1
session_id: '0022'
title: 8B scale and hyperparameter planning
status: active
created_at: '2026-06-25T14:15:48Z'
updated_at: '2026-06-25T14:48:44Z'
phase: phase1
question: Which 8B response-confidence and thinking-enabled variants should be prepared,
  and what local training exhaust plus literature should we inspect before spending
  compute on LR, beta, KL, reward, or LoRA sensitivity runs?
tags:
- scale
- hyperparameters
- thinking
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-06-25T14:20:42Z'
  kind: planning
  title: 8B variants and hyperparameter audit map
  summary: Set up Amendment I as a draft planning layer for 8B response-confidence
    variants, 8B thinking source probes, and a required training-exhaust/hyperparameter
    audit before new LR, beta, KL, reward, epoch, or LoRA-rank sweeps. Seed replication
    is deferred until the seed-1 stack feels final enough to replicate.
  evidence:
  - Added experiment/protocol/AMENDMENT-I-8b-scale-and-hyperparameter-gates.md, experiment/notes/qwen3-8b-response-confidence-scale-map.md,
    experiment/notes/training-exhaust-hyperparameter-audit.md, and updated TODO.md.
    KG/arXiv check identified new candidate papers 2602.04998, 2602.06204, 2407.08639,
    and 2502.13177, all currently NEW to the vault.
  run_ids: []
  commands: []
  decisions:
  - 'Use tiered 8B setup: Tier 1 = 8b_clean_sft, 8b_clean_sft_grpo_v2, 8b_clean_sft_grpo_dpo;
    Tier 2 mirrors the full clean 4B seed-1 matrix; Tier 3 requires separate Qwen3-8B
    thinking/non-thinking source probes before any thinking 8B training. Complete
    the hyperparameter/training-exhaust audit before launching sensitivity sweeps.'
  next_steps:
  - Run the training-exhaust audit over existing local configs/logs, ingest the selected
    LR/LoRA and DPO beta papers, then recommend whether to prioritize mech interp,
    8B Tier 1, or bounded hyperparameter sweeps.
  signals: {}
- id: 002-result
  at: '2026-06-25T14:40:28Z'
  kind: result
  title: Training-exhaust audit derived from local scratch runs
  summary: 'Built experiment/phase1/analysis/build_training_exhaust_audit.py and generated
    training_exhaust_summary.csv plus training_exhaust_hyperparameter_report.md from
    32 local capacity/log artifacts joined to self-aware eval rollups. Main read:
    clean LoRA settings are constant (r32/alpha64/dropout0.05), so current data does
    not identify a LoRA-rank effect; batch headroom is arm-specific (DPO low VRAM,
    GRPO batch32 plausible with guard, KTO batch12 already high/moderate risk); clean
    DPO/KTO generally optimize trainer objectives but move downstream behavior modestly;
    GRPO/stacks push refusal recall strongly but still trade off over-refusal and
    confidence calibration.'
  evidence:
  - experiment/phase1/analysis/training_exhaust_summary.csv; experiment/phase1/analysis/training_exhaust_hyperparameter_report.md
  run_ids: []
  commands:
  - python experiment\\phase1\\analysis\\build_training_exhaust_audit.py
  decisions:
  - Do not blanket-increase batch size or launch LR/beta/LoRA sweeps yet; first ingest/update
    theory for LoRA LR scaling and DPO beta, then choose a small theory-backed panel.
    Treat the SFT capacity_pct_over_100 telemetry as unsafe for batch increases but
    not a literal physical VRAM percentage without rerun.
  next_steps:
  - Use KG-backed literature ingest for LoRA learning-rate/rank scaling and DPO beta
    sensitivity, then revise the hyperparameter panel recommendation and 8B Tier 1
    gate.
  signals: {}
- id: 003-interpretation
  at: '2026-06-25T14:48:44Z'
  kind: interpretation
  title: LoRA-LR and DPO-beta papers ingested for hyperparameter planning
  summary: 'Ingested 2602.06204 (Learning Rate Scaling across LoRA Ranks and Transfer
    to Full Finetuning) and 2407.08639 (beta-DPO) into the KG with four reusable atoms:
    maximal-update-adaptation, beta-dpo, lora-rank-changes-require-learning-rate-retuning,
    and dpo-beta-should-follow-pair-quality. Decision implication: LoRA-rank sweeps
    must jointly reason about learning rate/effective LoRA multiplier, and DPO beta
    sweeps should be grounded in preference-pair quality rather than treated as a
    blind scalar knob.'
  evidence:
  - library/notes/2602.06204--learning-rate-scaling-across-lora-ranks-transfer.md;
    library/notes/2407.08639--dpo-direct-preference-optimization-dynamic.md; library/concepts/mechanisms/lora-rank-changes-require-learning-rate-retuning.md;
    library/concepts/mechanisms/dpo-beta-should-follow-pair-quality.md
  run_ids: []
  commands:
  - python .agents\\skills\\knowledge-graph\\scripts\\validate_kg_relationships.py
    --root library
  decisions:
  - Recommended next hyperparameter panel should not vary LoRA rank alone; pair rank
    with LR/multiplier rationale. Recommended DPO panel should first audit pair-gap
    distribution and test beta around static 0.1 only if the objective/reward target
    is worth rerunning.
  next_steps:
  - Draft a concise hyperparameter recommendation section in the training-exhaust
    note/report and use it to decide whether to run mech interp, 8B Tier 1, or a small
    LR/beta diagnostic next.
  signals: {}
---
# 8B scale and hyperparameter planning

## Question

Which 8B response-confidence and thinking-enabled variants should be prepared, and what local training exhaust plus literature should we inspect before spending compute on LR, beta, KL, reward, or LoRA sensitivity runs?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-planning - 8B variants and hyperparameter audit map

- at: `2026-06-25T14:20:42Z`
- kind: `planning`
- summary: Set up Amendment I as a draft planning layer for 8B response-confidence variants, 8B thinking source probes, and a required training-exhaust/hyperparameter audit before new LR, beta, KL, reward, epoch, or LoRA-rank sweeps. Seed replication is deferred until the seed-1 stack feels final enough to replicate.
- evidence:
  - `Added experiment/protocol/AMENDMENT-I-8b-scale-and-hyperparameter-gates.md, experiment/notes/qwen3-8b-response-confidence-scale-map.md, experiment/notes/training-exhaust-hyperparameter-audit.md, and updated TODO.md. KG/arXiv check identified new candidate papers 2602.04998, 2602.06204, 2407.08639, and 2502.13177, all currently NEW to the vault.`
- decisions:
  - Use tiered 8B setup: Tier 1 = 8b_clean_sft, 8b_clean_sft_grpo_v2, 8b_clean_sft_grpo_dpo; Tier 2 mirrors the full clean 4B seed-1 matrix; Tier 3 requires separate Qwen3-8B thinking/non-thinking source probes before any thinking 8B training. Complete the hyperparameter/training-exhaust audit before launching sensitivity sweeps.
- next steps:
  - Run the training-exhaust audit over existing local configs/logs, ingest the selected LR/LoRA and DPO beta papers, then recommend whether to prioritize mech interp, 8B Tier 1, or bounded hyperparameter sweeps.
### 002-result - Training-exhaust audit derived from local scratch runs

- at: `2026-06-25T14:40:28Z`
- kind: `result`
- summary: Built experiment/phase1/analysis/build_training_exhaust_audit.py and generated training_exhaust_summary.csv plus training_exhaust_hyperparameter_report.md from 32 local capacity/log artifacts joined to self-aware eval rollups. Main read: clean LoRA settings are constant (r32/alpha64/dropout0.05), so current data does not identify a LoRA-rank effect; batch headroom is arm-specific (DPO low VRAM, GRPO batch32 plausible with guard, KTO batch12 already high/moderate risk); clean DPO/KTO generally optimize trainer objectives but move downstream behavior modestly; GRPO/stacks push refusal recall strongly but still trade off over-refusal and confidence calibration.
- evidence:
  - `experiment/phase1/analysis/training_exhaust_summary.csv; experiment/phase1/analysis/training_exhaust_hyperparameter_report.md`
- commands:
  - `python experiment\\phase1\\analysis\\build_training_exhaust_audit.py`
- decisions:
  - Do not blanket-increase batch size or launch LR/beta/LoRA sweeps yet; first ingest/update theory for LoRA LR scaling and DPO beta, then choose a small theory-backed panel. Treat the SFT capacity_pct_over_100 telemetry as unsafe for batch increases but not a literal physical VRAM percentage without rerun.
- next steps:
  - Use KG-backed literature ingest for LoRA learning-rate/rank scaling and DPO beta sensitivity, then revise the hyperparameter panel recommendation and 8B Tier 1 gate.
### 003-interpretation - LoRA-LR and DPO-beta papers ingested for hyperparameter planning

- at: `2026-06-25T14:48:44Z`
- kind: `interpretation`
- summary: Ingested 2602.06204 (Learning Rate Scaling across LoRA Ranks and Transfer to Full Finetuning) and 2407.08639 (beta-DPO) into the KG with four reusable atoms: maximal-update-adaptation, beta-dpo, lora-rank-changes-require-learning-rate-retuning, and dpo-beta-should-follow-pair-quality. Decision implication: LoRA-rank sweeps must jointly reason about learning rate/effective LoRA multiplier, and DPO beta sweeps should be grounded in preference-pair quality rather than treated as a blind scalar knob.
- evidence:
  - `library/notes/2602.06204--learning-rate-scaling-across-lora-ranks-transfer.md; library/notes/2407.08639--dpo-direct-preference-optimization-dynamic.md; library/concepts/mechanisms/lora-rank-changes-require-learning-rate-retuning.md; library/concepts/mechanisms/dpo-beta-should-follow-pair-quality.md`
- commands:
  - `python .agents\\skills\\knowledge-graph\\scripts\\validate_kg_relationships.py --root library`
- decisions:
  - Recommended next hyperparameter panel should not vary LoRA rank alone; pair rank with LR/multiplier rationale. Recommended DPO panel should first audit pair-gap distribution and test beta around static 0.1 only if the objective/reward target is worth rerunning.
- next steps:
  - Draft a concise hyperparameter recommendation section in the training-exhaust note/report and use it to decide whether to run mech interp, 8B Tier 1, or a small LR/beta diagnostic next.
