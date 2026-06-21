---
schema_version: research-session/v1
session_id: grpo-reward-variance-diagnostic
title: GRPO Reward Variance Diagnostic
status: active
created_at: '2026-06-21T09:09:44Z'
updated_at: '2026-06-21T10:08:00Z'
phase: phase1
question: Can local GRPO rollouts produce parseable completions and nonzero reward
  variance under intended generation/reward settings before scaling training?
tags:
- experiment-runner
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: 'Amendment B / GRPO bootstrap preflight after stated-confidence eval layer.'
  changed_by_session: 'GRPO base smoke moved from infrastructure-only to nonzero reward-variance proof under native Qwen template plus high-exploration sampling; a bounded 64-step base pilot trained and evaluated cleanly but did not move core SelfAware refusal/correctness behavior versus the base control; SFT-start remains blocked on answer-only format inertia.'
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
- id: 005-launch
  at: '2026-06-21T10:04:00Z'
  kind: launch
  title: Bounded Base-GRPO Pilot
  summary: Proceeding from the successful base smoke to a bounded base-GRPO pilot on the full projected GRPO train JSONL with the same native Qwen thinking-off template and high-exploration sampler. This remains local Amendment B pilot evidence, not headline Phase 1 evidence.
  evidence:
  - experiment/phase1/grpo/configs/grpo_base_pilot.yaml
  - scratch/grpo_bootstrap/qwen3-4b-instruct/grpo_train.jsonl
  run_ids:
  - grpo_base_pilot_pending
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base-pilot -Force -DebugReward
  decisions:
  - Keep the smoke config separate from the pilot config so the six-step gate remains fast and reproducible.
  - Run reward debug for the first pilot so raw candidate diversity can be audited if reward variance collapses.
  next_steps:
  - Inspect reward std, clipping, grad norms, KL, train_end, final_model, training_lineage, and reward debug trace after completion.
  - If pilot artifacts are healthy, evaluate the pilot adapter against the stated-confidence eval layer.
  signals: {}
- id: 006-result
  at: '2026-06-21T10:08:00Z'
  kind: result
  title: Base-GRPO Pilot Completed
  summary: The 64-step base-GRPO pilot completed locally, saved a final LoRA adapter and lineage, maintained nonzero reward variance on most logged steps, and showed no clipping or OOM pressure. Reward-debug rollouts were mostly parseable JSON and frequently had within-group diversity, so the GRPO training signal exists under this setup.
  evidence:
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/logs/training_20260621_095545.jsonl
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/final_model/adapter_model.safetensors
  - scratch/grpo_bootstrap/runs/base_pilot/20260621_095511/training_lineage.json
  - scratch/grpo_bootstrap/reward_debug/base-pilot_latest.jsonl
  run_ids:
  - grpo_base_pilot_20260621_095511
  commands:
  - powershell -NoProfile -ExecutionPolicy Bypass -File experiment/phase1/grpo/run_micro_smoke.ps1 -Mode base-pilot -Force -DebugReward
  decisions:
  - Treat reward variance as a training-plumbing gate only; behavioral movement must be checked by same-slice eval before interpreting the pilot as scientific evidence.
  next_steps:
  - Evaluate the pilot adapter on the 192-row SelfAware stated-confidence slice and compare against the same prompt-contract base control.
  signals:
    steps: 64
    nonzero_reward_std_steps: 40
    zero_std_rate: 0.375
    mean_reward_std: 0.415088304085657
    max_reward_std: 1.6887495517730713
    mean_reward: -0.30478515452705324
    max_clipped_ratio: 0.0
    max_grad_norm: 11.482610702514648
    max_kl: 0.03641607612371445
    valid_json_rate: 0.9453125
    multi_unique_group_rate: 0.78125
    refusal_text_rate: 0.5078125
- id: 007-result
  at: '2026-06-21T10:08:00Z'
  kind: result
  title: Base-GRPO Pilot Eval Was Base-Like
  summary: >-
    Live vLLM eval of the 64-step base-GRPO pilot on the 192-row SelfAware
    stated-confidence slice completed successfully, but the scored behavior was
    unchanged from the base prompt-contract control: refusal recall 1.05%,
    over-refusal 1.03%, correct-on-known 23.96%, truthful 12.5%. Row-level
    comparison showed 52/192 answer texts changed, but 0 refusal decisions
    changed and only 2 correctness labels moved, one improvement and one
    regression.
  evidence:
  - experiment/phase1/eval/config/eval_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_local_4b.yaml
  - experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b/base_grpo_pilot_64__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_4b/base_grpo_pilot_64__selfaware/scored_rows.jsonl
  - experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed1_base_smoke_4b/base_seed1_smoke__selfaware/metrics.json
  run_ids:
  - eval_base_grpo_pilot_64_selfaware_20260621
  commands:
  - docker run --rm --gpus all --ipc=host --entrypoint python3 -e HF_HOME=/workspace/repo/.cache/hf -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v "${PWD}:/workspace/repo" -w /workspace/repo unsloth/unsloth:latest experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_amendment_b_stated_confidence_selfaware_base_grpo_pilot_smoke_local_4b.yaml --live-vllm
  decisions:
  - Do not treat this pilot as evidence that GRPO improved humility yet; it is evidence that local base-GRPO training/eval plumbing works and that 64 low-LR steps are behaviorally too weak on the current slice.
  - Next GRPO scaling should change one of duration, reward strength, curriculum, or starting policy, and should keep same-slice behavioral comparators as a hard gate.
  next_steps:
  - Decide whether the next GRPO step is a longer base-start pilot, a prompt-contract/format bridge for SFT-start GRPO, or reward-weight/curriculum tuning before another pilot.
  signals:
    n: 192
    refusal_recall_pct: 1.05
    over_refusal_pct: 1.03
    correct_on_known_pct: 23.96
    truthful_pct: 12.5
    stated_confidence_coverage_pct: 100.0
    mean_stated_confidence: 0.901562
    changed_answer_text_rows: 52
    changed_refusal_rows: 0
    changed_correctness_rows: 2
---
# GRPO Reward Variance Diagnostic

## Question

Can local GRPO rollouts produce parseable completions and nonzero reward variance under intended generation/reward settings before scaling training?

## Trajectory Position

This sits in Amendment B / GRPO bootstrap after the stated-confidence evaluation layer. The goal is not headline evidence yet; it is proving that local GRPO can produce parseable answer/confidence rollouts and a nonzero comparative reward signal before any longer pilot.

## Summary

Base-start GRPO now works as a local smoke-tested training path when Qwen uses its tokenizer-native chat template with `enable_thinking: false` and high-exploration sampling. The 64-step base pilot trained and evaluated cleanly, but the same-slice SelfAware behavior remained base-like: wording moved, but refusal behavior did not. SFT-start GRPO is not ready for the same objective because the SFT seed 1 checkpoint keeps producing answer-only outputs with zero valid JSON; it likely needs a small format bridge or separate prompt-contract adaptation before confidence-reward GRPO.

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

### 005-launch - Bounded Base-GRPO Pilot

- at: `2026-06-21T10:04:00Z`
- kind: `launch`
- summary: Proceeding from the successful base smoke to a bounded base-GRPO pilot on the full projected GRPO train JSONL with the same native Qwen thinking-off template and high-exploration sampler. This remains local Amendment B pilot evidence, not headline Phase 1 evidence.

### 006-result - Base-GRPO Pilot Completed

- at: `2026-06-21T10:08:00Z`
- kind: `result`
- summary: The 64-step base-GRPO pilot completed locally, saved `final_model`, lineage, and reward-debug artifacts, and produced nonzero reward std on 40/64 logged steps with no clipping or OOM pressure.

### 007-result - Base-GRPO Pilot Eval Was Base-Like

- at: `2026-06-21T10:08:00Z`
- kind: `result`
- summary: Live vLLM eval of the pilot on the 192-row SelfAware stated-confidence slice matched the base control on core metrics: refusal recall 1.05%, over-refusal 1.03%, correct-on-known 23.96%, truthful 12.5%. Row-level comparison found 52 changed answer texts but zero changed refusal decisions.
