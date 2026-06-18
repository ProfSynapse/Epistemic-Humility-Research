---
schema_version: research-session/v1
session_id: phase3-causal-pilot-start
title: Phase 3 Causal Pilot Start
status: active
created_at: '2026-06-18T20:09:45Z'
updated_at: '2026-06-18T21:36:00Z'
phase: phase1
question: Track startup of the Phase 3 exploratory causal-pilot mechanistic-interpretability
  work from existing hidden-state directions.
tags:
- experiment-runner
- knowledge-graph
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Phase 3 exploratory mechanism work is moving from verified hidden-state
    direction readiness into a small causal-pilot design.
  changed_by_session: Starts the causal-pilot session, records the smoke-slice decision,
    and summarizes existing Tier 1 hidden-state diagnostics before Tier 2 intervention.
checkpoints:
- id: 001-planning
  at: '2026-06-18T20:10:56Z'
  kind: planning
  title: Causal Pilot Session Started
  summary: Started a fresh Phase 3 causal-pilot session after the Amendment B sequential
    results synthesis. Current target is a small Tier 2 exploratory local activation-addition/subtraction
    pilot from existing verified SFT hidden-state directions, with no claim promotion
    and no reward-loop use.
  evidence:
  - docs/plans/phase3-interpretability-direction.md
  - docs/plans/phase3-interpretability-research-process.md
  - experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml
  run_ids: []
  commands: []
  decisions:
  - Reduce the broad 112-arm dry-run plan to a smoke-slice before any live model intervention.
  next_steps:
  - Verify extraction/direction artifacts and design the smallest executable runner
    or diagnostic step.
  signals: {}
- id: 002-result
  at: '2026-06-18T20:40:48Z'
  kind: result
  title: Initial Activation-Addition Smoke Complete
  summary: Implemented and ran the first explicit Phase 3 activation-addition runner.
    The runner gate, CPU tests, Docker/GPU smoke path, and hook telemetry all worked.
    Coefficients 1, 5, and 50 on the SFT h_lora layer-36 known/unknown direction produced
    no behavior or text changes on the 16-row smoke slice; hook telemetry confirmed
    the coefficient-50 intervention applied.
  evidence:
  - docs/plans/phase3-causal-pilot-smoke-results.md
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203542Z/metrics.json
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203936Z/scored_rows.jsonl
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 1 --max-rows
    16 --allow-generation
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 5 --max-rows
    16 --allow-generation
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 50 --max-rows
    16 --allow-generation
  decisions:
  - Do not scale row count yet; next add a logit-level diagnostic to distinguish a
    behaviorally stable greedy decode from a hook/layer placement issue.
  next_steps:
  - Implement or run a next-token logit/refusal-token diagnostic for baseline/add/subtract
    before trying other directions or larger slices.
  signals: {}
- id: 003-result
  at: '2026-06-18T21:30:00Z'
  kind: result
  title: Logit Diagnostic Smoke Complete
  summary: Added and ran the explicit Phase 3 logit diagnostic mode through the
    existing activation-hook/model/candidate path. CPU tests passed, and 2-row
    plus 16-row GPU smokes exited 0 after overriding the Unsloth Docker image
    entrypoint; a post-remediation 2-row smoke then verified corrected row-level
    diagnostic metadata. The diagnostic showed activation addition/subtraction
    changed the next-token logit distribution on all 16 rows, but coefficient 50
    did not change greedy next-token top-1 on this smoke slice.
  evidence:
  - docs/plans/phase3-causal-pilot-smoke-results.md
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --allow-logit-diagnostic --max-rows 16
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2
  decisions:
  - Treat the prior no-generation-change result as not simply a dead hook; the
    intervention is mechanically active and changes logits.
  - Do not scale generation rows yet from this direction/coefficient alone,
    because coefficient 50 on SFT h_lora layer 36 did not change greedy
    next-token top-1 on the 16-row smoke.
  next_steps:
  - Prefer richer logit targets/probability slices, the alternate SFT delta
    layer-35 direction, a layer/position sweep, or a final-norm intervention
    before broader generation scaling.
  signals:
    cpu_tests: 21 passed in 2.06s
    post_remediation_smoke: run_20260618T213414Z exited 0
    row_metadata: generation_executed false; logit_diagnostic_executed true
    activation_addition_hook_applied: 16/16
    activation_subtraction_hook_applied: 16/16
    top1_changed_rate: 0.0
---
# Phase 3 Causal Pilot Start

## Question

Track startup of the Phase 3 exploratory causal-pilot mechanistic-interpretability work from existing hidden-state directions.

## Trajectory Position

This session follows the completed Amendment B sequential SelfAware reruns and
the initial Phase 3 dry-run readiness materialization. It is not a protocol
change and does not alter Phase 1 headline evidence. The immediate aim is to
test whether existing known/unknown hidden-state directions are merely
correlational readouts or have controlled behavioral leverage under a small
local activation-addition/subtraction pilot.

## Summary

The broad dry-run plan contains 112 planned arms/controls. Before any live model
intervention, this session narrows the first causal pilot to a smoke slice and
records the existing Tier 1 diagnostic baseline. Existing verified 128 known /
128 unknown extractions show SFT has stronger active-adapter and delta
known/unknown separability than cold-start DPO/KTO, while sequential DPO/KTO
preserve or reshape high SFT separability over the merged-SFT base. This remains
correlational until a controlled intervention changes behavior.

## Checkpoints
### 001-planning - Causal Pilot Session Started

- at: `2026-06-18T20:10:56Z`
- kind: `planning`
- summary: Started a fresh Phase 3 causal-pilot session after the Amendment B sequential results synthesis. Current target is a small Tier 2 exploratory local activation-addition/subtraction pilot from existing verified SFT hidden-state directions, with no claim promotion and no reward-loop use.
- evidence:
  - `docs/plans/phase3-interpretability-direction.md`
  - `docs/plans/phase3-interpretability-research-process.md`
  - `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml`
- decisions:
  - Reduce the broad 112-arm dry-run plan to a smoke-slice before any live model intervention.
- next steps:
  - Verify extraction/direction artifacts and design the smallest executable runner or diagnostic step.

### 002-observation - Tier 1 Diagnostic Baseline

- at: `2026-06-18T20:24:00Z`
- kind: `observation`
- summary: Existing hidden-state diagnostic artifacts show a stable Tier 1
  pattern: SFT has higher active-adapter/delta known-vs-unknown separability
  than cold-start DPO/KTO, and sequential DPO/KTO retain high separability over
  the merged-SFT base. This does not establish causal control.
- evidence:
  - `docs/plans/phase3-hidden-state-diagnostic-summary.md`
  - `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8/manifest.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8/hidden_state_linear_probe_kfold5_diagnostic.csv`
- commands:
  - `python - <<summary script over hidden-state manifests and diagnostic CSVs>>`
- decisions:
  - Treat the first causal pilot as a test of behavioral leverage, not a repeat of the linear-probe result.
- next steps:
  - Wait for the implementation-feasibility handoff, then decide whether to add a minimal activation-addition runner or another readiness layer.
### 002-result - Initial Activation-Addition Smoke Complete

- at: `2026-06-18T20:40:48Z`
- kind: `result`
- summary: Implemented and ran the first explicit Phase 3 activation-addition runner. The runner gate, CPU tests, Docker/GPU smoke path, and hook telemetry all worked. Coefficients 1, 5, and 50 on the SFT h_lora layer-36 known/unknown direction produced no behavior or text changes on the 16-row smoke slice; hook telemetry confirmed the coefficient-50 intervention applied.
- evidence:
  - `docs/plans/phase3-causal-pilot-smoke-results.md`
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203542Z/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203936Z/scored_rows.jsonl`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 1 --max-rows 16 --allow-generation`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 5 --max-rows 16 --allow-generation`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 50 --max-rows 16 --allow-generation`
- decisions:
  - Do not scale row count yet; next add a logit-level diagnostic to distinguish a behaviorally stable greedy decode from a hook/layer placement issue.
- next steps:
  - Implement or run a next-token logit/refusal-token diagnostic for baseline/add/subtract before trying other directions or larger slices.

### 003-result - Logit Diagnostic Smoke Complete

- at: `2026-06-18T21:30:00Z`
- kind: `result`
- summary: Added and ran the explicit Phase 3 logit diagnostic mode through the existing activation-hook/model/candidate path. CPU tests passed, and 2-row plus 16-row GPU smokes exited 0 after overriding the Unsloth Docker image entrypoint; a post-remediation 2-row smoke then verified corrected row-level diagnostic metadata. The diagnostic showed activation addition/subtraction changed the next-token logit distribution on all 16 rows, but coefficient 50 did not change greedy next-token top-1 on this smoke slice.
- evidence:
  - `docs/plans/phase3-causal-pilot-smoke-results.md`
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 16`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2`
- result:
  - Post-remediation CPU tests: `21 passed in 2.06s`.
  - 2-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z`, exit 0.
  - 16-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z`, exit 0.
  - Post-remediation 2-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z`, exit 0.
  - Row-level diagnostic metadata now reports `generation_executed: false` and `logit_diagnostic_executed: true`; metrics remained nonzero.
  - The runner now validates non-empty coefficient/control grids.
  - Activation addition applied hooks on `16/16` rows; `delta_abs_sum_mean=1488.159424`, `l2_logit_delta_mean=145.364276`, `max_abs_logit_delta_max=1.763671875`, `top1_changed_rate=0.0`.
  - Activation subtraction applied hooks on `16/16` rows; `delta_abs_sum_mean=1488.159424`, `l2_logit_delta_mean=141.963216`, `max_abs_logit_delta_max=1.734375`, `top1_changed_rate=0.0`.
  - Baseline deltas were zero.
- interpretation:
  - The intervention is mechanically active and changes the logit distribution, so the prior no-generation-change result is not simply a dead hook.
  - Coefficient 50 on this SFT `h_lora` layer-36 direction did not change greedy next-token top-1 on the 16-row smoke.
- next steps:
  - Prefer richer logit targets/probability slices, the alternate SFT `delta` layer-35 direction, a layer/position sweep, or a final-norm intervention before broader generation scaling.
