---
schema_version: research-session/v1
session_id: 20260617T113756Z-grpo-stated-confidence
title: GRPO Stated Confidence
status: active
created_at: '2026-06-17T11:37:56Z'
updated_at: '2026-06-17T11:47:49Z'
phase: phase1
question: How should Amendment B add GRPO and stated-confidence tracking to the epistemic-humility
  framework?
tags:
- experiment-runner
- grpo
- stated-confidence
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Amendment B is a prospective extension that adds GRPO reward design
    and stated-confidence measurement without changing the signed v0.3 headline matrix.
  changed_by_session: Added JSON-only answer/confidence contract, eval-side stated-confidence
    distance metrics, GRPO reward/dataset scaffolding, and a draft amendment plus
    session-memory workflow correction.
checkpoints:
- id: 001-planning
  at: '2026-06-17T11:38:05Z'
  kind: planning
  title: Amendment B Direction
  summary: Opened an Amendment B session for GRPO and stated-confidence tracking.
    The working decision is to keep signed v0.3 results separate while adding a prospective
    output contract for answer plus confidence.
  evidence:
  - experiments/stated-confidence-grpo/AMENDMENT.md
  - experiment/phase1/grpo/README.md
  run_ids: []
  commands: []
  decisions:
  - Treat stated-confidence reruns as Amendment B evidence, not a replacement for
    locked v0.3 headline results.
  next_steps:
  - Use a structured JSON answer/confidence contract with no legacy Confidence-line
    compatibility because no Amendment B runs have used the old draft format.
  signals: {}
- id: 002-decision
  at: '2026-06-17T11:41:02Z'
  kind: decision
  title: JSON Output Contract
  summary: Settled Amendment B stated-confidence output on a JSON-only contract with
    answer and confidence fields. Removed the draft Confidence-line compatibility
    path because no Amendment B runs have used it.
  evidence:
  - experiment/phase1/eval/scorers.py
  - experiment/phase1/grpo/humility_reward.py
  - experiment/phase1/grpo/build_grpo_dataset.py
  - experiments/stated-confidence-grpo/AMENDMENT.md
  run_ids: []
  commands: []
  decisions:
  - 'Use JSON-only output: {"answer": string, "confidence": number}; do not support
    the abandoned Confidence-line draft format.'
  next_steps:
  - Rerun approved seeds under Amendment B with prompts that require the JSON object,
    then analyze stated-confidence distance metrics.
  signals: {}
- id: 003-decision
  at: '2026-06-17T11:43:48Z'
  kind: decision
  title: Baseline Eval Rerun Scope
  summary: Clarified that Amendment B requires rerunning the existing eval suite under
    the JSON answer/confidence contract across baseline training regimens and seeds
    before comparing GRPO stated-confidence behavior.
  evidence:
  - experiments/stated-confidence-grpo/AMENDMENT.md
  - experiment/phase1/eval/scorers.py
  run_ids: []
  commands: []
  decisions:
  - Do not retrofit old eval outputs into stated-confidence baselines; re-evaluate
    base, v0.3 SFT/DPO/KTO seeds, relevant Amendment A sequential cells, and future
    GRPO cells with the same JSON output prompt and scorer.
  next_steps:
  - Before launching reruns, enumerate the exact arms/seeds/eval configs and get explicit
    approval for those cells.
  signals: {}
- id: 004-result
  at: '2026-06-17T11:47:49Z'
  kind: result
  title: Formal Amendment And Template Added
  summary: Promoted Amendment B from a lightweight draft to a formal ready-for-sign-off
    protocol artifact and added reusable amendment workflow/template guidance to the
    experiment-runner skill.
  evidence:
  - experiments/stated-confidence-grpo/AMENDMENT.md
  - .skills/experiment-runner/reference/protocol-amendments.md
  - .skills/experiment-runner/reference/protocol-amendment-template.md
  run_ids: []
  commands: []
  decisions:
  - Protocol changes that alter arms, metrics, output contracts, or rerun scope should
    use a separate AMENDMENT-<LETTER> artifact plus a session note checkpoint.
  next_steps:
  - Create a PR with Amendment B infrastructure and merge after checks/review are
    acceptable.
  signals: {}
legacy_session:
  id: grpo-stated-confidence
  path: docs/sessions/0003 - grpo-stated-confidence.md
---
# GRPO Stated Confidence

## Question

How should Amendment B add GRPO and stated-confidence tracking to the epistemic-humility framework?

## Trajectory Position

Amendment B is a prospective extension that adds GRPO reward design and stated-confidence measurement without changing the signed v0.3 headline matrix.

## Summary

This session established a JSON-only output contract for stated-confidence reruns, added eval metrics for distance to model-specific known/unknown labels and factual answer correctness, scaffolded a custom GRPO reward and dataset projection outside the `synaptic-tuner/` submodule, and updated the experiment-runner session-memory guidance so future durable experiment work starts with a session note stub.

## Checkpoints
### 001-planning - Amendment B Direction

- at: `2026-06-17T11:38:05Z`
- kind: `planning`
- summary: Opened an Amendment B session for GRPO and stated-confidence tracking. The working decision is to keep signed v0.3 results separate while adding a prospective output contract for answer plus confidence.
- evidence:
  - `experiments/stated-confidence-grpo/AMENDMENT.md`
  - `experiment/phase1/grpo/README.md`
- decisions:
  - Treat stated-confidence reruns as Amendment B evidence, not a replacement for locked v0.3 headline results.
- next steps:
  - Use a structured JSON answer/confidence contract with no legacy Confidence-line compatibility because no Amendment B runs have used the old draft format.
### 002-decision - JSON Output Contract

- at: `2026-06-17T11:41:02Z`
- kind: `decision`
- summary: Settled Amendment B stated-confidence output on a JSON-only contract with answer and confidence fields. Removed the draft Confidence-line compatibility path because no Amendment B runs have used it.
- evidence:
  - `experiment/phase1/eval/scorers.py`
  - `experiment/phase1/grpo/humility_reward.py`
  - `experiment/phase1/grpo/build_grpo_dataset.py`
  - `experiments/stated-confidence-grpo/AMENDMENT.md`
- decisions:
  - Use JSON-only output: {"answer": string, "confidence": number}; do not support the abandoned Confidence-line draft format.
- next steps:
  - Rerun approved seeds under Amendment B with prompts that require the JSON object, then analyze stated-confidence distance metrics.
### 003-decision - Baseline Eval Rerun Scope

- at: `2026-06-17T11:43:48Z`
- kind: `decision`
- summary: Clarified that Amendment B requires rerunning the existing eval suite under the JSON answer/confidence contract across baseline training regimens and seeds before comparing GRPO stated-confidence behavior.
- evidence:
  - `experiments/stated-confidence-grpo/AMENDMENT.md`
  - `experiment/phase1/eval/scorers.py`
- decisions:
  - Do not retrofit old eval outputs into stated-confidence baselines; re-evaluate base, v0.3 SFT/DPO/KTO seeds, relevant Amendment A sequential cells, and future GRPO cells with the same JSON output prompt and scorer.
- next steps:
  - Before launching reruns, enumerate the exact arms/seeds/eval configs and get explicit approval for those cells.
### 004-result - Formal Amendment And Template Added

- at: `2026-06-17T11:47:49Z`
- kind: `result`
- summary: Promoted Amendment B from a lightweight draft to a formal ready-for-sign-off protocol artifact and added reusable amendment workflow/template guidance to the experiment-runner skill.
- evidence:
  - `experiments/stated-confidence-grpo/AMENDMENT.md`
  - `.skills/experiment-runner/reference/protocol-amendments.md`
  - `.skills/experiment-runner/reference/protocol-amendment-template.md`
- decisions:
  - Protocol changes that alter arms, metrics, output contracts, or rerun scope should use a separate AMENDMENT-<LETTER> artifact plus a session note checkpoint.
- next steps:
  - Create a PR with Amendment B infrastructure and merge after checks/review are acceptable.
