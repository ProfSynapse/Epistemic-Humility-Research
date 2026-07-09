---
schema_version: research-session/v1
session_id: replace-with-session-id
title: Replace With Session Title
status: active
created_at: "YYYY-MM-DDTHH:MM:SSZ"
updated_at: "YYYY-MM-DDTHH:MM:SSZ"
question: What research question or workflow state is this session tracking?
tags:
  - experiment-runner
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ""
  changed_by_session: ""
checkpoints:
  - id: 001-planning
    at: "YYYY-MM-DDTHH:MM:SSZ"
    kind: planning
    title: Planning Checkpoint
    summary: State the checkpoint in one or two factual sentences.
    evidence:
      - docs/research-trajectory.md
    run_ids: []
    commands: []
    decisions: []
    next_steps: []
    signals: {}
---
# Replace With Session Title

## Question

What research question or workflow state is this session tracking?

## Trajectory Position

Describe where this sits relative to `docs/research-trajectory.md`.

## Summary

Keep this updated when the session closes or materially changes direction.

## Checkpoints

### 001-planning - Planning Checkpoint

- at: `YYYY-MM-DDTHH:MM:SSZ`
- kind: `planning`
- summary: State the checkpoint in one or two factual sentences.
- evidence:
  - `docs/research-trajectory.md`
