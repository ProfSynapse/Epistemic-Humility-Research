---
schema_version: research-session/v1
session_id: 20260620T230051Z-grpo-bootstrap
title: GRPO Bootstrap
status: active
created_at: '2026-06-20T23:00:51Z'
updated_at: '2026-06-21T05:27:53Z'
track: research
question: Can we safely bootstrap Amendment B GRPO training locally with a calibrated
  answer/confidence reward before any full GRPO cells?
tags:
- experiment-runner
- grpo
- stated-confidence
- training
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-gate
  at: '2026-06-20T23:06:37Z'
  kind: gate
  title: GRPO Reward And Dataset Preflight
  summary: 'Started Amendment B GRPO bootstrap. Tightened the custom reward to align
    stated-confidence refusal handling with the evaluator, added a material invalid-JSON
    penalty, added a deterministic reward sanity table, projected the Qwen3-4B GRPO
    dataset into scratch, and created a 32-row balanced smoke subset plus base and
    SFT-seed1 micro-smoke configs. A generic Synaptic Tuner custom-reward import bug
    was found and fixed: dynamically loaded reward modules must be registered in sys.modules
    before exec_module so dataclass-decorated reward helpers work.'
  evidence:
  - archive/experiment/phase1/grpo/humility_reward.py
  - archive/experiment/phase1/grpo/reward_sanity_table.py
  - archive/experiment/phase1/grpo/make_smoke_subset.py
  - archive/experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml
  - archive/experiment/phase1/grpo/configs/grpo_sft_seed1_micro_smoke.yaml
  - synaptic-tuner/Trainers/grpo/src/rewards.py
  run_ids: []
  commands:
  - python -m pytest archive/experiment/phase1/grpo/tests/test_humility_reward.py archive/experiment/phase1/grpo/tests/test_build_grpo_dataset.py
    -q
  - python -m pytest synaptic-tuner/tests/trainers/grpo/test_fitness_reward.py -q
  - python archive/experiment/phase1/grpo/build_grpo_dataset.py --model-tag qwen3-4b-instruct
    --output-dir scratch/grpo_bootstrap/qwen3-4b-instruct
  - python archive/experiment/phase1/grpo/make_smoke_subset.py --input scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl
    --output scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train_smoke_32.jsonl --per-label
    16
  decisions:
  - Treat the next GRPO run as a two-step plumbing smoke only, not a reportable Amendment
    B training cell.
  - Do not launch the GPU micro-smoke while the thinking eval container is actively
    using the GPU unless the user explicitly prioritizes GRPO over eval throughput.
  next_steps:
  - When GPU is free, run the base micro smoke first to prove trainer/reward/data
    plumbing, then the SFT-seed1 micro smoke if base plumbing succeeds.
  signals: {}
- id: 002-gate
  at: '2026-06-20T23:08:11Z'
  kind: gate
  title: GPU Launch Guard Held
  summary: Tested the GRPO micro-smoke launch wrapper. It correctly refused to start
    the Docker GRPO run because the thinking eval container was still active and nvidia-smi
    reported 12364 MiB used, above the 4096 MiB default guard threshold. No GRPO GPU
    training was launched.
  evidence:
  - archive/experiment/phase1/grpo/run_micro_smoke.ps1
  - archive/experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode base
  decisions:
  - Keep the GRPO base micro-smoke queued until the running eval frees enough GPU
    memory, unless explicitly forced.
  next_steps:
  - After the eval container exits, run powershell -NoProfile -ExecutionPolicy Bypass
    -File archive/experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base, then inspect scratch/grpo_bootstrap/runs/base_micro_smoke
    for checkpoints/logs.
  signals: {}
- id: 003-result
  at: '2026-06-21T05:27:53Z'
  kind: result
  title: Base And SFT-Seed1 GRPO Micro-Smokes Completed
  summary: 'The thinking eval batch completed all 10 configs, then the guarded local
    path launched the Amendment B base GRPO micro-smoke and the SFT-seed1 GRPO micro-smoke.
    Both completed max_steps=2, wrote final adapters, lineage, and capacity features,
    and stayed low-risk on VRAM. The smoke validated Docker, model load, SFT-merged
    model resolution, dataset formatting, custom reward loading, trainer execution,
    checkpointing, and artifact write-out. It also exposed a training-readiness issue:
    both smokes logged zero reward standard deviation on each step, so these runs
    prove plumbing but do not prove that the current rollout/reward setup provides
    useful GRPO learning signal.'
  evidence:
  - scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_051848/training_lineage.json
  - scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_051848/logs/training_20260621_051920.jsonl
  - scratch/grpo_bootstrap/runs/sft_seed1_micro_smoke/20260621_052546/training_lineage.json
  - scratch/grpo_bootstrap/runs/sft_seed1_micro_smoke/20260621_052546/logs/training_20260621_052652.jsonl
  - archive/experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode base
  - powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1
    -Mode sft-seed1
  decisions:
  - Treat the completed GRPO micro-smokes as infrastructure validation only; do not
    interpret them as behavioral evidence.
  - Before any longer GRPO run, add or run a rollout/reward-variance diagnostic that
    samples completions and confirms nonzero within-prompt reward variance under the
    intended generation settings.
  next_steps:
  - Inspect raw rollout outputs or add a lightweight GRPO rollout diagnostic so the
    reward/prompt/generation settings can be adjusted before full GRPO training.
  signals: {}
legacy_session:
  id: grpo-bootstrap
  path: docs/sessions/0014 - grpo-bootstrap.md
---
# GRPO Bootstrap

## Question

Can we safely bootstrap Amendment B GRPO training locally with a calibrated answer/confidence reward before any full GRPO cells?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-gate - GRPO Reward And Dataset Preflight

- at: `2026-06-20T23:06:37Z`
- kind: `gate`
- summary: Started Amendment B GRPO bootstrap. Tightened the custom reward to align stated-confidence refusal handling with the evaluator, added a material invalid-JSON penalty, added a deterministic reward sanity table, projected the Qwen3-4B GRPO dataset into scratch, and created a 32-row balanced smoke subset plus base and SFT-seed1 micro-smoke configs. A generic Synaptic Tuner custom-reward import bug was found and fixed: dynamically loaded reward modules must be registered in sys.modules before exec_module so dataclass-decorated reward helpers work.
- evidence:
  - `archive/experiment/phase1/grpo/humility_reward.py`
  - `archive/experiment/phase1/grpo/reward_sanity_table.py`
  - `archive/experiment/phase1/grpo/make_smoke_subset.py`
  - `archive/experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml`
  - `archive/experiment/phase1/grpo/configs/grpo_sft_seed1_micro_smoke.yaml`
  - `synaptic-tuner/Trainers/grpo/src/rewards.py`
- commands:
  - `python -m pytest archive/experiment/phase1/grpo/tests/test_humility_reward.py archive/experiment/phase1/grpo/tests/test_build_grpo_dataset.py -q`
  - `python -m pytest synaptic-tuner/tests/trainers/grpo/test_fitness_reward.py -q`
  - `python archive/experiment/phase1/grpo/build_grpo_dataset.py --model-tag qwen3-4b-instruct --output-dir scratch/grpo_bootstrap/qwen3-4b-instruct`
  - `python archive/experiment/phase1/grpo/make_smoke_subset.py --input scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl --output scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train_smoke_32.jsonl --per-label 16`
- decisions:
  - Treat the next GRPO run as a two-step plumbing smoke only, not a reportable Amendment B training cell.
  - Do not launch the GPU micro-smoke while the thinking eval container is actively using the GPU unless the user explicitly prioritizes GRPO over eval throughput.
- next steps:
  - When GPU is free, run the base micro smoke first to prove trainer/reward/data plumbing, then the SFT-seed1 micro smoke if base plumbing succeeds.
### 002-gate - GPU Launch Guard Held

- at: `2026-06-20T23:08:11Z`
- kind: `gate`
- summary: Tested the GRPO micro-smoke launch wrapper. It correctly refused to start the Docker GRPO run because the thinking eval container was still active and nvidia-smi reported 12364 MiB used, above the 4096 MiB default guard threshold. No GRPO GPU training was launched.
- evidence:
  - `archive/experiment/phase1/grpo/run_micro_smoke.ps1`
  - `archive/experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl`
- commands:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base`
- decisions:
  - Keep the GRPO base micro-smoke queued until the running eval frees enough GPU memory, unless explicitly forced.
- next steps:
  - After the eval container exits, run powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base, then inspect scratch/grpo_bootstrap/runs/base_micro_smoke for checkpoints/logs.
### 003-result - Base And SFT-Seed1 GRPO Micro-Smokes Completed

- at: `2026-06-21T05:27:53Z`
- kind: `result`
- summary: The thinking eval batch completed all 10 configs, then the guarded local path launched the Amendment B base GRPO micro-smoke and the SFT-seed1 GRPO micro-smoke. Both completed max_steps=2, wrote final adapters, lineage, and capacity features, and stayed low-risk on VRAM. The smoke validated Docker, model load, SFT-merged model resolution, dataset formatting, custom reward loading, trainer execution, checkpointing, and artifact write-out. It also exposed a training-readiness issue: both smokes logged zero reward standard deviation on each step, so these runs prove plumbing but do not prove that the current rollout/reward setup provides useful GRPO learning signal.
- evidence:
  - `scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_051848/training_lineage.json`
  - `scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_051848/logs/training_20260621_051920.jsonl`
  - `scratch/grpo_bootstrap/runs/sft_seed1_micro_smoke/20260621_052546/training_lineage.json`
  - `scratch/grpo_bootstrap/runs/sft_seed1_micro_smoke/20260621_052546/logs/training_20260621_052652.jsonl`
  - `archive/experiment/phase1/eval/logs/thinking_eval_batch/batch_status_current.jsonl`
- commands:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File archive/experiment/phase1/grpo/run_micro_smoke.ps1 -Mode sft-seed1`
- decisions:
  - Treat the completed GRPO micro-smokes as infrastructure validation only; do not interpret them as behavioral evidence.
  - Before any longer GRPO run, add or run a rollout/reward-variance diagnostic that samples completions and confirms nonzero within-prompt reward variance under the intended generation settings.
- next steps:
  - Inspect raw rollout outputs or add a lightweight GRPO rollout diagnostic so the reward/prompt/generation settings can be adjusted before full GRPO training.
