---
schema_version: research-session/v1
session_id: grpo-reward-variance-diagnostic
title: GRPO Reward Variance Diagnostic
status: active
created_at: '2026-06-21T09:09:44Z'
updated_at: '2026-06-21T09:46:00Z'
phase: phase1
question: Can local GRPO rollouts produce parseable completions and nonzero reward
  variance under intended generation/reward settings before scaling training?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'Amendment B / GRPO bootstrap preflight after stated-confidence eval layer.'
  changed_by_session: 'GRPO base smoke moved from infrastructure-only to nonzero reward-variance proof under native Qwen template plus high-exploration sampling; SFT-start remains blocked on answer-only format inertia.'
checkpoints:
- id: 001-planning
  at: '2026-06-21T09:09:44Z'
  kind: planning
  title: Reward-Variance Gate
  summary: Prior GRPO smokes proved Docker/model/reward plumbing but had zero within-prompt reward variance. This session gates longer GRPO on raw rollout inspection, JSON parse coverage, and nonzero trainer reward std.
  evidence:
  - experiment/phase1/grpo/configs/grpo_base_micro_smoke.yaml
  - experiment/phase1/grpo/humility_reward.py
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/grpo/tests/test_humility_reward.py experiment/phase1/grpo/tests/test_build_grpo_dataset.py -q
  decisions:
  - Do not scale GRPO until sampled completions and trainer logs show a real comparative reward signal.
  next_steps: []
  signals: {}
- id: 002-observation
  at: '2026-06-21T09:24:46Z'
  kind: observation
  title: Native Qwen Template Fix
  summary: Base rollout diagnostics with tokenizer-native Qwen templating and enable_thinking=false produced high JSON coverage, no clipping, and nonzero reward variance; generic ChatML templating ignored the Qwen thinking switch and produced clipped think traces.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/base_20260621_052343/summary.json
  - scratch/grpo_bootstrap/diagnostics/base_20260621_052343/rollouts.jsonl
  - https://qwen.readthedocs.io/en/latest/getting_started/quickstart.html
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1 -Mode base -MaxRows 4 -NumRollouts 4 -MaxCompletionLength 256
  decisions:
  - Add generic Synaptic Tuner GRPO support for chat_template_kwargs and native/tokenizer chat-template preservation.
  next_steps: []
  signals:
    mean_valid_json_rate: 0.875
    mean_clipped_rate: 0.0
    mean_reward_std: 0.4778972476243142
    zero_std_prompt_rate: 0.25
- id: 003-observation
  at: '2026-06-21T09:28:33Z'
  kind: observation
  title: SFT-Start Format Inertia
  summary: SFT seed 1 retained the old answer-only/refusal behavior and produced zero valid JSON even with native Qwen thinking-off templating and eight rollouts per prompt. SFT-start GRPO is therefore not ready for the stated-confidence objective without a format bridge or separate prompt-contract adaptation.
  evidence:
  - scratch/grpo_bootstrap/diagnostics/sft-seed1_20260621_052656/summary.json
  - scratch/grpo_bootstrap/diagnostics/sft-seed1_20260621_052656/rollouts.jsonl
  run_ids: []
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_rollout_diagnostic.ps1 -Mode sft-seed1 -MaxRows 4 -NumRollouts 8 -MaxCompletionLength 256
  decisions:
  - Treat base-start GRPO as the first working GRPO bootstrap target; treat SFT-start GRPO as requiring an additional format/alignment bridge before scale.
  next_steps: []
  signals:
    mean_valid_json_rate: 0.0
    mean_clipped_rate: 0.0
    mean_reward_std: 0.18069985738082223
    zero_std_prompt_rate: 0.5
- id: 004-result
  at: '2026-06-21T09:43:51Z'
  kind: result
  title: Trainer Reward Variance Achieved
  summary: Base GRPO micro-smoke with native Qwen template, four generations, 256 completion tokens, and high-exploration sampling produced nonzero reward std on three of six trainer steps, nonzero grad norms, nonzero KL after step 1, no clipping, and completed artifact save-out.
  evidence:
  - scratch/grpo_bootstrap/runs/base_micro_smoke/20260621_094323/logs/training_20260621_094351.jsonl
  - scratch/grpo_bootstrap/reward_debug/base_latest.jsonl
  run_ids:
  - grpo_base_micro_smoke_20260621_094323
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base -Force -DebugReward
  decisions:
  - The GRPO base pipeline is now locally operational as a smoke-tested training path; longer runs still need a protocol-scale decision and post-run eval gate.
  - Keep reward debug opt-in only; use it when reward_std unexpectedly collapses.
  next_steps:
  - Decide whether to run a bounded base-GRPO pilot or first build an SFT-format bridge for SFT-start GRPO.
  - If scaling base-GRPO, keep native Qwen template and high-exploration sampling, then evaluate against the stated-confidence comparison set.
  signals:
    nonzero_reward_std_steps: 3
    total_logged_train_steps: 6
    max_reward_std: 0.8133816123008728
    max_grad_norm: 5.968965530395508
    max_kl: 0.010111197829246521
    max_clipped_ratio: 0.0
---
# GRPO Reward Variance Diagnostic

## Question

Can local GRPO rollouts produce parseable completions and nonzero reward variance under intended generation/reward settings before scaling training?

## Trajectory Position

This sits in Amendment B / GRPO bootstrap after the stated-confidence evaluation layer. The goal is not headline evidence yet; it is proving that local GRPO can produce parseable answer/confidence rollouts and a nonzero comparative reward signal before any longer pilot.

## Summary

Base-start GRPO now works as a local smoke-tested training path when Qwen uses its tokenizer-native chat template with `enable_thinking: false` and high-exploration sampling. SFT-start GRPO is not ready for the same objective because the SFT seed 1 checkpoint keeps producing answer-only outputs with zero valid JSON; it likely needs a small format bridge or separate prompt-contract adaptation before confidence-reward GRPO.

## Checkpoints

### 001-planning - Reward-Variance Gate

- at: `2026-06-21T09:09:44Z`
- kind: `planning`
- summary: Prior GRPO smokes proved Docker/model/reward plumbing but had zero within-prompt reward variance. This session gates longer GRPO on raw rollout inspection, JSON parse coverage, and nonzero trainer reward std.

### 002-observation - Native Qwen Template Fix

- at: `2026-06-21T09:24:46Z`
- kind: `observation`
- summary: Base rollout diagnostics with tokenizer-native Qwen templating and `enable_thinking: false` produced high JSON coverage, no clipping, and nonzero reward variance. Generic ChatML templating ignored the Qwen thinking switch and produced clipped think traces.

### 003-observation - SFT-Start Format Inertia

- at: `2026-06-21T09:28:33Z`
- kind: `observation`
- summary: SFT seed 1 retained the old answer-only/refusal behavior and produced zero valid JSON even with native Qwen thinking-off templating and eight rollouts per prompt.

### 004-result - Trainer Reward Variance Achieved

- at: `2026-06-21T09:43:51Z`
- kind: `result`
- summary: Base GRPO micro-smoke with native Qwen template, four generations, 256 completion tokens, and high-exploration sampling produced nonzero reward std on three of six trainer steps, nonzero grad norms, nonzero KL after step 1, no clipping, and completed artifact save-out.
