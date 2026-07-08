---
schema_version: research-session/v1
session_id: 20260617T111205Z-amendment-a-kto-seed3-launch
title: Amendment A KTO Seed3 Launch
status: active
created_at: '2026-06-17T11:12:05Z'
updated_at: '2026-06-17T11:19:20Z'
phase: phase1
question: Can clean SFT->KTO seed3 complete from the seed3 merged SFT base and close
  the KTO three-seed Amendment A evidence gap?
tags:
- experiment-runner
- amendment-a
- local-gpu
run_ids:
- sft_kto__4b__amendment_a__seed3
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Phase 1 local work is completing the signed Amendment A three-seed
    sequential KTO arm after seed1 and clean seed2 showed high abstention retention
    with high over-refusal.
  changed_by_session: Launched clean SFT->KTO seed3 locally and verified first optimizer-step
    evidence.
checkpoints:
- id: 001-seed3-kto-launched
  at: '2026-06-17T11:03:34Z'
  kind: launch
  title: Clean SFT->KTO Seed3 Launched
  summary: Clean SFT->KTO seed3 was launched from the seed3 merged SFT base with the
    prepared Amendment A recipe settings; direct Docker launch was used because Windows
    PowerShell background launch routes did not persist from the Codex shell.
  evidence:
  - experiment/phase1/run_records/sft_kto__4b__amendment_a__seed3.json
  - experiment/phase1/run_records/materialized_recipes/sft_kto__4b__amendment_a__seed3.yaml
  - synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334/logs/training_20260617_110523.jsonl
  - TODO.md
  run_ids:
  - sft_kto__4b__amendment_a__seed3
  commands:
  - docker run -d --rm --gpus all ... Trainers/kto/train_kto.py ...
  decisions:
  - Treat the materialized recipe as the settings source of truth even though the
    container was launched directly.
  - Monitor the concrete timestamped training log, not training_latest.jsonl, because
    the latest link is unreadable on Windows.
  next_steps:
  - Continue heartbeat monitoring until train_end.
  - On completion, verify final_model, capacity_features, training_lineage, and then
    run full SelfAware eval plus contamination scan.
  signals:
    container_name: local-run-sft-kto-4b-amendment-a-seed3-20260617_070334
    container_id: 6a6db9a4b858
    artifact_root: synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334
    metrics_log: synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334/logs/training_20260617_110523.jsonl
    latest_step: 95
    total_steps: 3599
    latest_loss: 0.5014
    latest_gpu_memory_reserved_gb: 4.385
    oom_risk: low
    checkpoints_observed: checkpoint-25, checkpoint-50, checkpoint-75
legacy_session:
  id: amendment-a-kto-seed3-launch
  path: docs/sessions/0003 - amendment-a-kto-seed3-launch.md
---
# Amendment A KTO Seed3 Launch

## Question

Can clean SFT->KTO seed3 complete from the seed3 merged SFT base and close the KTO three-seed Amendment A evidence gap?

## Summary

Clean SFT->KTO seed3 is running locally from the seed3 merged SFT base. Early checks passed: balanced KTO labels, model load, LoRA application, trainer initialization, first optimizer steps, and checkpoint writes. The latest checked step was 95 / 3,599 with low OOM risk.

## Checkpoints

### 001-seed3-kto-launched - Clean SFT->KTO Seed3 Launched

- at: `2026-06-17T11:03:34Z`
- kind: `launch`
- summary: Clean SFT->KTO seed3 was launched from the seed3 merged SFT base with prepared Amendment A recipe settings; direct Docker launch was used because Windows PowerShell background launch routes did not persist from the Codex shell.
- evidence:
  - `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed3.json`
  - `experiment/phase1/run_records/materialized_recipes/sft_kto__4b__amendment_a__seed3.yaml`
  - `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed3/20260617_070334/logs/training_20260617_110523.jsonl`
- metrics: step 95 / 3,599, loss 0.5014, reserved VRAM 4.385 GB, OOM risk low; checkpoints observed at 25, 50, and 75.
- next steps:
  - Monitor until `train_end`, then verify artifacts and run full SelfAware eval.
