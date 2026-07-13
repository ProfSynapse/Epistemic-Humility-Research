---
schema_version: research-session/v1
session_id: 20260619T122000Z-amendment-c-crossover-preference-stacking
title: Amendment C Cross-Over Preference Stacking
status: active
created_at: '2026-06-19T12:20:00Z'
updated_at: '2026-06-19T12:20:00Z'
track: research
question: Track the unsigned Amendment C draft proposing cross-over sequential preference
  stacking after Amendment A.
tags:
- experiment-runner
- protocol-amendment
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Amendment C is an unsigned exploratory protocol draft only; no
    training or eval launch is authorized from this note.
  changed_by_session: Adds a protocol draft for SFT -> DPO -> KTO and SFT -> KTO ->
    DPO cross-over preference stacking, separate from signed v0.3, Amendment A, and
    Amendment B.
checkpoints:
- id: 001-draft
  at: '2026-06-19T12:20:00Z'
  kind: amendment
  title: Amendment C Draft Created
  summary: Created the unsigned Amendment C protocol draft for cross-over sequential
    preference stacking. The proposed additive scope is SFT -> DPO -> KTO and SFT
    -> KTO -> DPO, with seed-1 local smoke first, seeds 2/3 gated on merge, sanity
    eval, and artifact provenance, and 8B deferred. No training, eval, commit, large
    artifact movement, or synaptic-tuner edit is authorized by this session.
  evidence:
  - experiments/crossover-preference-stacking/AMENDMENT.md
  - docs/sessions/20260619T122000Z-amendment-c-crossover-preference-stacking.md
  run_ids: []
  commands: []
  decisions:
  - Keep Amendment C separate from signed PROTOCOL v0.3, Amendment A sequential refinement,
    and Amendment B stated-confidence / GRPO scope.
  - Label any future results from these arms as Amendment C evidence.
  - Require exact later approval for cells, seeds, configs, artifacts, and lane before
    any launch.
  next_steps:
  - Await explicit user sign-off or revision before treating Amendment C as active.
  - If approved later, enumerate seed-1 local smoke configs and provenance gates before
    running either stacked arm.
  signals: {}
legacy_session:
  id: amendment-c-crossover-preference-stacking
  path: docs/sessions/0008 - amendment-c-crossover-preference-stacking.md
---
# 0008 - Amendment C Cross-Over Preference Stacking

## Status

Amendment C is a draft and is not signed. It authorizes no training, eval
launch, artifact publication, or protocol replacement.

## Summary

Created an unsigned protocol amendment proposing two cross-over sequential
preference-stacking arms:

- `sft_dpo_kto`: merge `SFT -> DPO`, then train KTO.
- `sft_kto_dpo`: merge `SFT -> KTO`, then train DPO.

The rationale comes from the current sequential result skeleton: `SFT -> DPO`
reduces over-refusal but appears to overshoot on unknown-row abstention, while
`SFT -> KTO` preserves refusal behavior better but leaves more over-refusal.
The amendment tests whether the two preference objectives can compose into a
better refusal/known-answer balance, while preserving the competing hypothesis
that stacking may instead cause washout, over-answering, over-refusal, known
accuracy loss, or provenance/schema failures.

## Boundary

This note and the linked amendment are documentation only. Any future launch
requires exact approval for cells, seeds, configs, artifact sources, output
locations, and execution lane. Results must be labeled Amendment C if run.

## Checkpoints

### 001-draft - Amendment C Draft Created

- at: `2026-06-19T12:20:00Z`
- kind: `amendment`
- summary: Created the unsigned Amendment C protocol draft for cross-over sequential preference stacking. The proposed additive scope is SFT -> DPO -> KTO and SFT -> KTO -> DPO, with seed-1 local smoke first, seeds 2/3 gated on merge, sanity eval, and artifact provenance, and 8B deferred. No training, eval, commit, large artifact movement, or synaptic-tuner edit is authorized by this session.
- evidence:
  - `experiments/crossover-preference-stacking/AMENDMENT.md`
  - `docs/sessions/20260619T122000Z-amendment-c-crossover-preference-stacking.md`
- decisions:
  - Keep Amendment C separate from signed PROTOCOL v0.3, Amendment A sequential refinement, and Amendment B stated-confidence / GRPO scope.
  - Label any future results from these arms as Amendment C evidence.
  - Require exact later approval for cells, seeds, configs, artifacts, and lane before any launch.
- next steps:
  - Await explicit user sign-off or revision before treating Amendment C as active.
  - If approved later, enumerate seed-1 local smoke configs and provenance gates before running either stacked arm.
