---
schema_version: research-session/v1
session_id: 20260618T192924Z-phase1-writeup-and-mech-interp-start
title: Phase 1 Writeup And Mech Interp Start
status: active
created_at: '2026-06-18T19:29:24Z'
updated_at: '2026-06-18T19:32:06Z'
phase: phase1
question: Track synthesis of Amendment B sequential evaluation results and startup
  of Phase 3 mechanistic-interpretability work.
tags:
- experiment-runner
- knowledge-graph
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Amendment B sequential SelfAware reruns are complete; the next
    work is paper-facing synthesis and Phase 3 exploratory mechanism probing.
  changed_by_session: Creates a results writeup artifact and starts bounded GPU-free
    validation of the existing hidden-state / causal-pilot infrastructure.
checkpoints:
- id: 001-validation
  at: '2026-06-18T19:31:20Z'
  kind: validation
  title: Initial Mech-Interp Readiness Checks
  summary: GPU-free validation passed for the hidden-state probe suite, extraction
    gate, and Phase 3 causal-pilot dry-run. The extraction gate is PASS for the default
    SFT config, with reproducibility warnings for unpinned model.revision and null
    expected_probe_config_sha.
  evidence:
  - experiment/phase1/probe/README.md
  - experiment/phase1/probe/config/hidden_state_probe.yaml
  - experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_hidden_state_probe.py
    experiment\\phase1\\probe\\tests\\test_hidden_state_directions.py experiment\\phase1\\probe\\tests\\test_hidden_state_linear_probe.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q
  - python .agents\\skills\\experiment-runner\\scripts\\prepare_extraction_cell.py
    --config experiment\\phase1\\probe\\config\\hidden_state_probe.yaml
  - python experiment\\phase1\\probe\\phase3_causal_pilot_dry_run.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_smoke.yaml
    --no-write
  decisions: []
  next_steps:
  - Decide whether to write the no-generation causal-pilot manifest or proceed to
    a GPU intervention smoke after reviewing the planned controls.
  signals: {}
- id: 002-infrastructure
  at: '2026-06-18T19:31:42Z'
  kind: infrastructure
  title: Causal-Pilot Dry-Run Manifest Materialized
  summary: Materialized the Phase 3 SFT causal-pilot dry-run manifest, planned arms,
    and metrics plan. This wrote only no-generation planning artifacts; no model generation,
    GPU intervention, training, reward update, or hidden-state tensor mutation was
    executed.
  evidence:
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/dry_run_manifest.json
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/planned_arms.json
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/metrics_plan.json
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\phase3_causal_pilot_dry_run.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_smoke.yaml
  decisions: []
  next_steps:
  - Review planned arms and controls, then decide whether to implement or run the
    first GPU activation-addition smoke.
  signals: {}
- id: 003-handoff
  at: '2026-06-18T19:32:06Z'
  kind: handoff
  title: Specialist Handoffs Integrated
  summary: 'Read-only writeup and mech-interp planning handoffs confirmed the current
    path: report Amendment B sequential results as local stated-confidence evidence,
    keep decision-enum schema steering as a measurement-artifact finding, and defer
    GPU intervention until no-generation causal-pilot readiness artifacts are reviewed.'
  evidence:
  - experiment/phase1/eval/analysis/amendment_b_sequential_results_report.md
  - docs/plans/phase3-causal-pilot-readiness.md
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/dry_run_manifest.json
  run_ids: []
  commands: []
  decisions:
  - Use existing hidden-state/candidate-direction infrastructure rather than building
    a new encoder or SAE before simple direction controls are tested.
  next_steps:
  - Review the dry-run planned arms and, if acceptable, implement or run the first
    activation-addition/subtraction GPU smoke on the SFT candidate directions.
  signals: {}
legacy_session:
  id: phase1-writeup-mech-interp-start
  path: docs/sessions/0005 - phase1-writeup-and-mech-interp-start.md
---
# Phase 1 Writeup And Mech Interp Start

## Question

Track synthesis of Amendment B sequential evaluation results and startup of Phase 3 mechanistic-interpretability work.

## Trajectory Position

This session sits after Amendment B stated-confidence sequential evals and
before any new tuning sweep. The behavioral result now supports a more precise
sequential-training question: SFT creates abstention behavior with substantial
over-refusal, while SFT-warmed DPO and KTO move along different parts of the
abstention-vs-over-refusal tradeoff.

Mechanistic-interpretability work remains exploratory Phase 3 work. Existing
hidden-state extractions and candidate directions can be used to validate and
plan causal-pilot infrastructure, but these outputs must not be promoted into
Phase 1 headline evidence or fed back into rewards without a later signed
protocol revision.

## Summary

Durable repo memory is the active memory channel for this session. The external
Nexus/session-memory MCP surface was not callable in this environment, so
`docs/sessions/20260617T000000Z-amendment-b-stated-confidence-eval-launch.md` remains the
authoritative saved memory for the completed evals. This session extends that
record by creating a paper-ready Amendment B sequential results report and by
validating the existing hidden-state / causal-pilot probe surface before any new
GPU execution.

## Checkpoints

### 001-planning - Writeup And Mechanism Startup

- at: `2026-06-18T19:29:24Z`
- kind: `planning`
- summary: Start paper-facing synthesis of the completed Amendment B sequential
  evals and begin bounded Phase 3 mechanistic-interpretability work from the
  existing probe infrastructure.
- evidence:
  - `docs/sessions/20260617T000000Z-amendment-b-stated-confidence-eval-launch.md`
  - `docs/research-trajectory.md`
  - `docs/plans/lora-hidden-state-probing-tier.md`
  - `docs/plans/phase3-causal-pilot-readiness.md`
  - `experiment/phase1/probe/README.md`
- decisions:
  - Treat the completed Amendment B sequential results as local sequential-track
    evidence, not locked v0.3 headline evidence.
  - Start mechanism work with readiness validation and existing 128x128
    hidden-state diagnostics before any new generation or GPU intervention.
- next_steps:
  - Draft an Amendment B sequential results report under
    `experiment/phase1/eval/analysis/`.
  - Run GPU-free probe and causal-pilot validation tests.
  - Record any validation gaps before launching longer mechanistic work.
### 001-validation - Initial Mech-Interp Readiness Checks

- at: `2026-06-18T19:31:20Z`
- kind: `validation`
- summary: GPU-free validation passed for the hidden-state probe suite, extraction gate, and Phase 3 causal-pilot dry-run. The extraction gate is PASS for the default SFT config, with reproducibility warnings for unpinned model.revision and null expected_probe_config_sha.
- evidence:
  - `experiment/phase1/probe/README.md`
  - `experiment/phase1/probe/config/hidden_state_probe.yaml`
  - `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_hidden_state_probe.py experiment\\phase1\\probe\\tests\\test_hidden_state_directions.py experiment\\phase1\\probe\\tests\\test_hidden_state_linear_probe.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `python .agents\\skills\\experiment-runner\\scripts\\prepare_extraction_cell.py --config experiment\\phase1\\probe\\config\\hidden_state_probe.yaml`
  - `python experiment\\phase1\\probe\\phase3_causal_pilot_dry_run.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_smoke.yaml --no-write`
- next steps:
  - Decide whether to write the no-generation causal-pilot manifest or proceed to a GPU intervention smoke after reviewing the planned controls.
### 002-infrastructure - Causal-Pilot Dry-Run Manifest Materialized

- at: `2026-06-18T19:31:42Z`
- kind: `infrastructure`
- summary: Materialized the Phase 3 SFT causal-pilot dry-run manifest, planned arms, and metrics plan. This wrote only no-generation planning artifacts; no model generation, GPU intervention, training, reward update, or hidden-state tensor mutation was executed.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/dry_run_manifest.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/planned_arms.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/metrics_plan.json`
- commands:
  - `python experiment\\phase1\\probe\\phase3_causal_pilot_dry_run.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_smoke.yaml`
- next steps:
  - Review planned arms and controls, then decide whether to implement or run the first GPU activation-addition smoke.
### 003-handoff - Specialist Handoffs Integrated

- at: `2026-06-18T19:32:06Z`
- kind: `handoff`
- summary: Read-only writeup and mech-interp planning handoffs confirmed the current path: report Amendment B sequential results as local stated-confidence evidence, keep decision-enum schema steering as a measurement-artifact finding, and defer GPU intervention until no-generation causal-pilot readiness artifacts are reviewed.
- evidence:
  - `experiment/phase1/eval/analysis/amendment_b_sequential_results_report.md`
  - `docs/plans/phase3-causal-pilot-readiness.md`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_smoke/dry_run_manifest.json`
- decisions:
  - Use existing hidden-state/candidate-direction infrastructure rather than building a new encoder or SAE before simple direction controls are tested.
- next steps:
  - Review the dry-run planned arms and, if acceptable, implement or run the first activation-addition/subtraction GPU smoke on the SFT candidate directions.
