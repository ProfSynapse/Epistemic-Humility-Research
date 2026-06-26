---
schema_version: research-session/v1
session_id: triviaqa-thinking-knowledge-audit
title: TriviaQA Thinking Knowledge Audit
status: active
created_at: '2026-06-25T12:23:52Z'
updated_at: '2026-06-25T13:59:42Z'
phase: phase1
question: Does enabling Qwen3 thinking change the TriviaQA known/unknown labels used
  as Phase 1 source of truth?
tags:
- experiment-runner
- triviaqa
- thinking
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-06-25T12:25:33Z'
  kind: planning
  title: Audit Plan
  summary: Paused training to audit whether Qwen3 thinking mode changes TriviaQA knowledge-boundary
    labels derived from the locked non-thinking probe. Added a gated thinking-on probe
    path that keeps non-thinking strict, scores only post-</think> final answers for
    thinking runs, and plans a 512-row deterministic subset comparison before any
    protocol replacement.
  evidence:
  - experiment/phase1/probe/config/probe_thinking_audit_512.yaml
  - experiment/phase1/probe/compare_thinking_probe_results.py
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_probe_smoke.py -q
  decisions:
  - Treat this as exploratory source-of-truth audit evidence only; if label migration
    is material, draft a governed protocol amendment before rebuilding datasets or
    retraining.
  next_steps:
  - Run the 512-row thinking-enabled TriviaQA probe locally in Docker, then compare
    against qwen3-4b-instruct/probe_results.jsonl.
  signals: {}
- id: 002-launch
  at: '2026-06-25T12:26:20Z'
  kind: launch
  title: Launched Thinking Audit Probe
  summary: Launched local Docker container eh-triviaqa-thinking-audit-512-20260625a
    for the 512-row Qwen3 thinking-enabled TriviaQA probe audit.
  evidence:
  - experiment/phase1/probe/config/probe_thinking_audit_512.yaml
  run_ids: []
  commands:
  - docker run -d --name eh-triviaqa-thinking-audit-512-20260625a --gpus all --ipc=host
    --entrypoint python3 ... experiment/phase1/probe/probe.py --config experiment/phase1/probe/config/probe_thinking_audit_512.yaml
  decisions: []
  next_steps:
  - Inspect logs after warm-up, then compare thinking rows against the locked non-thinking
    probe when complete.
  signals: {}
- id: 003-observation
  at: '2026-06-25T12:29:22Z'
  kind: observation
  title: 384 Token Audit Pilot Invalid
  summary: 'Early rows from the 512-row thinking audit showed systematic truncation:
    the first inspected greedy outputs opened <think> and never reached </think>,
    and sampled outputs were mostly unterminated. This means the 384-token audit would
    mainly measure trace truncation rather than latent knowledge under thinking.'
  evidence:
  - experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-512/probe_results.jsonl
  run_ids: []
  commands: []
  decisions:
  - Stop the 512-row 384-token pilot and relaunch a smaller thinking audit with a
    larger max_new_tokens budget before interpreting label migration.
  next_steps:
  - Create a 128-row thinking audit config with max_new_tokens=1024 and compare once
    extraction statuses show final answers are usually reached.
  signals: {}
- id: 004-launch
  at: '2026-06-25T12:31:29Z'
  kind: launch
  title: Relaunched 128 Row 1024 Token Audit
  summary: Relaunched the thinking-enabled TriviaQA audit as eh-triviaqa-thinking-audit-128-1024-20260625a
    using a 128-row deterministic subset and max_new_tokens=1024 to reduce trace truncation.
  evidence:
  - experiment/phase1/probe/config/probe_thinking_audit_128_1024.yaml
  run_ids: []
  commands:
  - docker run -d --name eh-triviaqa-thinking-audit-128-1024-20260625a --gpus all
    --ipc=host --entrypoint python3 ... experiment/phase1/probe/probe.py --config
    experiment/phase1/probe/config/probe_thinking_audit_128_1024.yaml
  decisions: []
  next_steps:
  - Inspect early rows for post_think extraction rates before interpreting any label
    changes.
  signals: {}
- id: 005-observation
  at: '2026-06-25T12:36:41Z'
  kind: observation
  title: Early 1024 Token QA
  summary: 'The 128-row 1024-token audit produced usable early rows: 5/6 inspected
    greedy generations reached post_think and 131/192 sampled generations reached
    post_think. One visually correct title answer was scored wrong because existing
    TriviaQA alias matching did not tolerate an inserted article, so label migration
    should be interpreted as conservative under the locked scorer.'
  evidence:
  - experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024/probe_results.jsonl
  run_ids: []
  commands: []
  decisions:
  - Continue the 128-row audit with the locked scorer for comparability, and treat
    scorer alias/article sensitivity as a separate source-of-truth noise finding.
  next_steps:
  - Wait for completion, run compare_thinking_probe_results.py, then decide whether
    the source-of-truth concern warrants a protocol amendment.
  signals: {}
- id: 006-observation
  at: '2026-06-25T12:47:20Z'
  kind: observation
  title: Partial Transition Check
  summary: 'At 29 joined rows, thinking changed some TriviaQA outcomes: 3 rows moved
    greedy wrong->right, 2 base-unknown rows moved to discard, and no base-unknown
    row had yet crossed to thinking-known. Extraction was usable but imperfect, with
    713 post_think sampled outputs and 215 unterminated outputs.'
  evidence:
  - experiment/phase1/probe/analysis/thinking_audit_128_1024_partial/summary.json
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\compare_thinking_probe_results.py --out-dir
    experiment\\phase1\\probe\\analysis\\thinking_audit_128_1024_partial
  decisions: []
  next_steps:
  - Let the 128-row audit complete before deciding whether this warrants a governed
    source-of-truth amendment.
  signals: {}
- id: 007-result
  at: '2026-06-25T13:36:18Z'
  kind: result
  title: 128 Row Thinking Audit Result
  summary: 'The thinking-enabled Qwen3 TriviaQA audit completed 128/128 rows with
    56 known, 33 unknown, and 39 discard labels under the locked scorer. Against the
    matching non-thinking rows, 1/47 base-unknown rows became thinking-known and 15/47
    became thinking-discard; greedy correctness moved false->true on 13 rows and true->false
    on 10 rows. Extraction remained imperfect but usable: 3303 sampled outputs reached
    post_think and 793 were unterminated.'
  evidence:
  - experiment/phase1/probe/analysis/thinking_audit_128_1024/summary.json
  - experiment/phase1/probe/analysis/thinking_audit_128_1024/README.md
  - experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024/probe_manifest.json
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\compare_thinking_probe_results.py
  decisions:
  - Do not replace the locked source labels from this bounded audit. Treat thinking
    as a real but moderate source-of-truth perturbation and treat exact TriviaQA alias
    scoring as a separate conservative label-noise issue.
  next_steps:
  - If source labels become central again, draft a governed amendment for a larger
    thinking-aware probe plus scorer-sensitivity analysis before rebuilding datasets.
  signals: {}
- id: 008-decision
  at: '2026-06-25T13:44:18Z'
  kind: decision
  title: Thinking Branch Framed As Parallel Arm
  summary: 'Accepted the 128-row thinking audit as evidence for a parallel thinking-enabled
    research arm rather than a replacement for the current non-thinking source labels.
    Drafted Amendment H and two experiment notes: one for a full thinking-aware TriviaQA
    source probe, one for downstream thinking-enabled training/eval replication across
    the same regimen families and seed policy.'
  evidence:
  - experiment/protocol/AMENDMENT-H-thinking-enabled-parallel-arm.md
  - experiment/notes/thinking-triviaqa-source-probe.md
  - experiment/notes/thinking-enabled-training-replication.md
  run_ids: []
  commands: []
  decisions:
  - Continue current non-thinking fine-tuning matrices as the active branch; treat
    thinking as a separately labeled Amendment H branch to run after explicit launch
    approval.
  next_steps:
  - Return to checking off Amendment F/G non-thinking fine-tuning matrices, with clean_sft_grpo_dpo
    as the current best seed-1 stack and Amendment G seed replication still proposed.
  signals: {}
- id: 009-decision
  at: '2026-06-25T13:59:42Z'
  kind: decision
  title: Deprioritize reciprocal DPO/KTO stacks
  summary: A quick KG-first and arXiv literature check found support for preference-derived
    signals feeding a later RL-style optimizer, especially RTO / DPO Meets PPO, but
    did not find a comparable theoretical reason to prioritize reciprocal DPO->KTO
    versus KTO->DPO ordering. Amendment H default matrix should focus on preference->RL
    and RL->preference crossings.
  evidence:
  - Ingested library/notes/2404.18922--dpo-meets-ppo-reinforced-token-optimization-rlhf.md
    plus method:reinforced-token-optimization and mechanism:dpo-token-rewards-enable-rl-policy-optimization.
    Updated Amendment C to dormant/deprioritized and Amendment H thinking replication
    docs to defer reciprocal preference-family stacks.
  run_ids: []
  commands: []
  decisions:
  - Do not run SFT->DPO->KTO or SFT->KTO->DPO as near-term seed-1 matrix cells. Keep
    SFT->DPO->GRPO, SFT->KTO->GRPO, SFT->GRPO->DPO, and SFT->GRPO->KTO as the relevant
    three-step crossings.
  next_steps:
  - 'Return to the seed-1 matrix: if all four preference/RL crossings are complete,
    analyze and choose whether to replicate best arms across seeds or move to the
    thinking parallel arm.'
  signals: {}
---
# TriviaQA Thinking Knowledge Audit

## Question

Does enabling Qwen3 thinking change the TriviaQA known/unknown labels used as Phase 1 source of truth?

## Trajectory Position

_Not yet recorded._

## Summary

_No summary yet._

## Checkpoints
### 001-planning - Audit Plan

- at: `2026-06-25T12:25:33Z`
- kind: `planning`
- summary: Paused training to audit whether Qwen3 thinking mode changes TriviaQA knowledge-boundary labels derived from the locked non-thinking probe. Added a gated thinking-on probe path that keeps non-thinking strict, scores only post-</think> final answers for thinking runs, and plans a 512-row deterministic subset comparison before any protocol replacement.
- evidence:
  - `experiment/phase1/probe/config/probe_thinking_audit_512.yaml`
  - `experiment/phase1/probe/compare_thinking_probe_results.py`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_probe_smoke.py -q`
- decisions:
  - Treat this as exploratory source-of-truth audit evidence only; if label migration is material, draft a governed protocol amendment before rebuilding datasets or retraining.
- next steps:
  - Run the 512-row thinking-enabled TriviaQA probe locally in Docker, then compare against qwen3-4b-instruct/probe_results.jsonl.
### 002-launch - Launched Thinking Audit Probe

- at: `2026-06-25T12:26:20Z`
- kind: `launch`
- summary: Launched local Docker container eh-triviaqa-thinking-audit-512-20260625a for the 512-row Qwen3 thinking-enabled TriviaQA probe audit.
- evidence:
  - `experiment/phase1/probe/config/probe_thinking_audit_512.yaml`
- commands:
  - `docker run -d --name eh-triviaqa-thinking-audit-512-20260625a --gpus all --ipc=host --entrypoint python3 ... experiment/phase1/probe/probe.py --config experiment/phase1/probe/config/probe_thinking_audit_512.yaml`
- next steps:
  - Inspect logs after warm-up, then compare thinking rows against the locked non-thinking probe when complete.
### 003-observation - 384 Token Audit Pilot Invalid

- at: `2026-06-25T12:29:22Z`
- kind: `observation`
- summary: Early rows from the 512-row thinking audit showed systematic truncation: the first inspected greedy outputs opened <think> and never reached </think>, and sampled outputs were mostly unterminated. This means the 384-token audit would mainly measure trace truncation rather than latent knowledge under thinking.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-512/probe_results.jsonl`
- decisions:
  - Stop the 512-row 384-token pilot and relaunch a smaller thinking audit with a larger max_new_tokens budget before interpreting label migration.
- next steps:
  - Create a 128-row thinking audit config with max_new_tokens=1024 and compare once extraction statuses show final answers are usually reached.
### 004-launch - Relaunched 128 Row 1024 Token Audit

- at: `2026-06-25T12:31:29Z`
- kind: `launch`
- summary: Relaunched the thinking-enabled TriviaQA audit as eh-triviaqa-thinking-audit-128-1024-20260625a using a 128-row deterministic subset and max_new_tokens=1024 to reduce trace truncation.
- evidence:
  - `experiment/phase1/probe/config/probe_thinking_audit_128_1024.yaml`
- commands:
  - `docker run -d --name eh-triviaqa-thinking-audit-128-1024-20260625a --gpus all --ipc=host --entrypoint python3 ... experiment/phase1/probe/probe.py --config experiment/phase1/probe/config/probe_thinking_audit_128_1024.yaml`
- next steps:
  - Inspect early rows for post_think extraction rates before interpreting any label changes.
### 005-observation - Early 1024 Token QA

- at: `2026-06-25T12:36:41Z`
- kind: `observation`
- summary: The 128-row 1024-token audit produced usable early rows: 5/6 inspected greedy generations reached post_think and 131/192 sampled generations reached post_think. One visually correct title answer was scored wrong because existing TriviaQA alias matching did not tolerate an inserted article, so label migration should be interpreted as conservative under the locked scorer.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024/probe_results.jsonl`
- decisions:
  - Continue the 128-row audit with the locked scorer for comparability, and treat scorer alias/article sensitivity as a separate source-of-truth noise finding.
- next steps:
  - Wait for completion, run compare_thinking_probe_results.py, then decide whether the source-of-truth concern warrants a protocol amendment.
### 006-observation - Partial Transition Check

- at: `2026-06-25T12:47:20Z`
- kind: `observation`
- summary: At 29 joined rows, thinking changed some TriviaQA outcomes: 3 rows moved greedy wrong->right, 2 base-unknown rows moved to discard, and no base-unknown row had yet crossed to thinking-known. Extraction was usable but imperfect, with 713 post_think sampled outputs and 215 unterminated outputs.
- evidence:
  - `experiment/phase1/probe/analysis/thinking_audit_128_1024_partial/summary.json`
- commands:
  - `python experiment\\phase1\\probe\\compare_thinking_probe_results.py --out-dir experiment\\phase1\\probe\\analysis\\thinking_audit_128_1024_partial`
- next steps:
  - Let the 128-row audit complete before deciding whether this warrants a governed source-of-truth amendment.
### 007-result - 128 Row Thinking Audit Result

- at: `2026-06-25T13:36:18Z`
- kind: `result`
- summary: The thinking-enabled Qwen3 TriviaQA audit completed 128/128 rows with 56 known, 33 unknown, and 39 discard labels under the locked scorer. Against the matching non-thinking rows, 1/47 base-unknown rows became thinking-known and 15/47 became thinking-discard; greedy correctness moved false->true on 13 rows and true->false on 10 rows. Extraction remained imperfect but usable: 3303 sampled outputs reached post_think and 793 were unterminated.
- evidence:
  - `experiment/phase1/probe/analysis/thinking_audit_128_1024/summary.json`
  - `experiment/phase1/probe/analysis/thinking_audit_128_1024/README.md`
  - `experiment/phase1/probe/qwen3-4b-instruct-thinking-audit-128-1024/probe_manifest.json`
- commands:
  - `python experiment\\phase1\\probe\\compare_thinking_probe_results.py`
- decisions:
  - Do not replace the locked source labels from this bounded audit. Treat thinking as a real but moderate source-of-truth perturbation and treat exact TriviaQA alias scoring as a separate conservative label-noise issue.
- next steps:
  - If source labels become central again, draft a governed amendment for a larger thinking-aware probe plus scorer-sensitivity analysis before rebuilding datasets.
### 008-decision - Thinking Branch Framed As Parallel Arm

- at: `2026-06-25T13:44:18Z`
- kind: `decision`
- summary: Accepted the 128-row thinking audit as evidence for a parallel thinking-enabled research arm rather than a replacement for the current non-thinking source labels. Drafted Amendment H and two experiment notes: one for a full thinking-aware TriviaQA source probe, one for downstream thinking-enabled training/eval replication across the same regimen families and seed policy.
- evidence:
  - `experiment/protocol/AMENDMENT-H-thinking-enabled-parallel-arm.md`
  - `experiment/notes/thinking-triviaqa-source-probe.md`
  - `experiment/notes/thinking-enabled-training-replication.md`
- decisions:
  - Continue current non-thinking fine-tuning matrices as the active branch; treat thinking as a separately labeled Amendment H branch to run after explicit launch approval.
- next steps:
  - Return to checking off Amendment F/G non-thinking fine-tuning matrices, with clean_sft_grpo_dpo as the current best seed-1 stack and Amendment G seed replication still proposed.
### 009-decision - Deprioritize reciprocal DPO/KTO stacks

- at: `2026-06-25T13:59:42Z`
- kind: `decision`
- summary: A quick KG-first and arXiv literature check found support for preference-derived signals feeding a later RL-style optimizer, especially RTO / DPO Meets PPO, but did not find a comparable theoretical reason to prioritize reciprocal DPO->KTO versus KTO->DPO ordering. Amendment H default matrix should focus on preference->RL and RL->preference crossings.
- evidence:
  - `Ingested library/notes/2404.18922--dpo-meets-ppo-reinforced-token-optimization-rlhf.md plus method:reinforced-token-optimization and mechanism:dpo-token-rewards-enable-rl-policy-optimization. Updated Amendment C to dormant/deprioritized and Amendment H thinking replication docs to defer reciprocal preference-family stacks.`
- decisions:
  - Do not run SFT->DPO->KTO or SFT->KTO->DPO as near-term seed-1 matrix cells. Keep SFT->DPO->GRPO, SFT->KTO->GRPO, SFT->GRPO->DPO, and SFT->GRPO->KTO as the relevant three-step crossings.
- next steps:
  - Return to the seed-1 matrix: if all four preference/RL crossings are complete, analyze and choose whether to replicate best arms across seeds or move to the thinking parallel arm.
