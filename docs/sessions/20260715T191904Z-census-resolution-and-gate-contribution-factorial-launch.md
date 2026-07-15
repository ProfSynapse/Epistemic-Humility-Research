---
schema_version: research-session/v1
session_id: 20260715T191904Z-census-resolution-and-gate-contribution-factorial-launch
title: Census resolution and gate-contribution factorial launch
status: active
created_at: '2026-07-15T19:19:04Z'
updated_at: '2026-07-15T19:19:45Z'
question: Census verdicts folded into paper 5 and the KG; can the doubt gate (not
  the write direction) be shown to supply selective abstention without training, via
  the signed 2x2 gate-contribution factorial?
tags: []
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-launch
  at: '2026-07-15T19:19:45Z'
  kind: launch
  title: Factorial signed, harness pinned, generation running
  summary: 'Census (PR 294) merged and ingested; paper 5 updated (PR 295, awaiting
    PI merge). Gate-contribution-factorial signed 2026-07-15 on exp/gate-contribution-factorial:
    all 17 knobs resolved (PI: Qwen3.5-4B hs20 12.608; Sel_abs metric; Gap_Sel(c_hat)
    floor 0.20; directional-only random leg; cost-protection 0.10). Predictions scoreboard
    registered pre-run with a genuine differentiating slot: orchestrator calls mistral
    gate axis PASS (dissociation), PI calls mistral FULL FAIL; both call qwen full
    pass. Harness: 24 pinned modules, 50/50 CPU smokes, RG0 byte-repro passed both
    families, qwen permuted-gate reproduces midband-heldout artifact byte-for-byte.
    Lead decoy decision: held-back clear-negative pool from fresh unsteered FIT-split
    baseline pass (238 qwen / 254 mistral survivors), audited repin of 3 files. Generation
    detached on free 3090 (PID 297775, ~26 rows/min): qwen permuted_gate_c_hat done,
    random seeds 1-2 done, seed 3 in progress; mistral follows; ETA ~2026-07-16 05:00Z.
    Commits cf65da38, 68163acb, 01be4ee5.'
  evidence: []
  run_ids: []
  commands: []
  decisions:
  - Mistral permuted seed 20260715 and substrate revision c170c708 pinned at sign;
    decoy source is a lead instrument-input decision within registered rubric text,
    not a criterion change.
  next_steps:
  - 'After generation: SC1 ledger, blinded pool build, sharded context-free adjudication
    under hash-commit-before-unblind, report.py, Outcome adjudication of the split
    scoreboard. Post-factorial: config-driven engine extraction (task 11), llama retest,
    scale test.'
  signals: {}
track: actuation
---
# Census resolution and gate-contribution factorial launch

## Question

Census verdicts folded into paper 5 and the KG; can the doubt gate (not the write direction) be shown to supply selective abstention without training, via the signed 2x2 gate-contribution factorial?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-launch - Factorial signed, harness pinned, generation running

- at: `2026-07-15T19:19:45Z`
- kind: `launch`
- summary: Census (PR 294) merged and ingested; paper 5 updated (PR 295, awaiting PI merge). Gate-contribution-factorial signed 2026-07-15 on exp/gate-contribution-factorial: all 17 knobs resolved (PI: Qwen3.5-4B hs20 12.608; Sel_abs metric; Gap_Sel(c_hat) floor 0.20; directional-only random leg; cost-protection 0.10). Predictions scoreboard registered pre-run with a genuine differentiating slot: orchestrator calls mistral gate axis PASS (dissociation), PI calls mistral FULL FAIL; both call qwen full pass. Harness: 24 pinned modules, 50/50 CPU smokes, RG0 byte-repro passed both families, qwen permuted-gate reproduces midband-heldout artifact byte-for-byte. Lead decoy decision: held-back clear-negative pool from fresh unsteered FIT-split baseline pass (238 qwen / 254 mistral survivors), audited repin of 3 files. Generation detached on free 3090 (PID 297775, ~26 rows/min): qwen permuted_gate_c_hat done, random seeds 1-2 done, seed 3 in progress; mistral follows; ETA ~2026-07-16 05:00Z. Commits cf65da38, 68163acb, 01be4ee5.
- decisions:
  - Mistral permuted seed 20260715 and substrate revision c170c708 pinned at sign; decoy source is a lead instrument-input decision within registered rubric text, not a criterion change.
- next steps:
  - After generation: SC1 ledger, blinded pool build, sharded context-free adjudication under hash-commit-before-unblind, report.py, Outcome adjudication of the split scoreboard. Post-factorial: config-driven engine extraction (task 11), llama retest, scale test.
