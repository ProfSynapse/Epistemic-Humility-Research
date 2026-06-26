---
schema_version: research-session/v1
session_id: best-stack-replication-scale-gate
title: Best Stack Replication And Scale Gate
status: active
created_at: '2026-06-25T11:53:30Z'
updated_at: '2026-06-25T11:55:11Z'
phase: phase1
question: Should the best Amendment F stack be replicated across clean response-confidence
  seeds and/or scaled before public artifact publication?
tags:
- experiment-runner
- amendment-g
- response-confidence
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-06-25T11:55:11Z'
  kind: planning
  title: Amendment G Drafted For Best-Stack Replication
  summary: Drafted a governed follow-up for the best Amendment F stack. The proposed
    next evidence path is clean response-confidence seed replication of clean SFT
    -> GRPO v2 -> DPO before public artifact publication or 8B scale-up.
  evidence:
  - experiment/protocol/AMENDMENT-G-best-stack-replication-scale-gate.md
  - experiment/notes/clean-sft-grpo-dpo-seed-replication.md
  - experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv
  run_ids: []
  commands: []
  decisions:
  - Treat Amendment G as draft/not signed; no GPU launch is authorized by the draft
    alone.
  next_steps:
  - If Joseph approves, prepare exact seed-2 launch plan with source lineage and eval
    gates before starting training.
  signals: {}
---
# Best Stack Replication And Scale Gate

## Question

Should the best Amendment F stack be replicated across clean response-confidence seeds and/or scaled before public artifact publication?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-planning - Amendment G Drafted For Best-Stack Replication

- at: `2026-06-25T11:55:11Z`
- kind: `planning`
- summary: Drafted a governed follow-up for the best Amendment F stack. The proposed next evidence path is clean response-confidence seed replication of clean SFT -> GRPO v2 -> DPO before public artifact publication or 8B scale-up.
- evidence:
  - `experiment/protocol/AMENDMENT-G-best-stack-replication-scale-gate.md`
  - `experiment/notes/clean-sft-grpo-dpo-seed-replication.md`
  - `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`
- decisions:
  - Treat Amendment G as draft/not signed; no GPU launch is authorized by the draft alone.
- next steps:
  - If Joseph approves, prepare exact seed-2 launch plan with source lineage and eval gates before starting training.
