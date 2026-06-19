---
schema_version: research-session/v1
session_id: amendment-a-seed2-recovery
title: Amendment A Seed2 Recovery
status: active
created_at: '2026-06-17T01:29:02Z'
updated_at: '2026-06-17T10:01:08Z'
phase: phase1
question: How did we recover clean Amendment A seed2 evidence after discovering the bad SFT seed2 merge?
tags:
- experiment-runner
- amendment-a
- local-gpu
run_ids:
- sft_dpo__4b__amendment_a__seed2
- sft_kto__4b__amendment_a__seed2
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Phase 1 local work is testing the signed Amendment A question of whether sequential SFT-warmed preference training can preserve abstention while reducing SFT over-refusal.
  changed_by_session: Reclassified the original seed2 sequential DPO/KTO artifacts as confounded by a bad SFT merge, rebuilt the SFT seed2 merge with a low-memory path, completed clean SFT->DPO seed2 training/eval, and completed clean SFT->KTO seed2 training/eval.
checkpoints:
- id: 001-bad-merge-detected
  at: '2026-06-16T20:06:46Z'
  kind: result
  title: Bad SFT Seed2 Merge Detected
  summary: Post-hoc sanity evaluation showed the original merged SFT seed2 checkpoint behaved base-like despite structural validity, so downstream sequential seed2 artifacts using that merge were confounded.
  evidence:
  - experiment/phase1/eval/results_sft_merged_seed2_selfaware_192_sanity
  - experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json
  run_ids:
  - sft_dpo__4b__amendment_a__seed2
  - sft_kto__4b__amendment_a__seed2
  commands: []
  decisions:
  - Exclude the original SFT->DPO seed2 result from clean sequential evidence.
  - Stop the active SFT->KTO seed2 run because it used the same bad merged base.
  next_steps:
  - Rebuild the SFT seed2 merged model through a lower-memory merge path.
  signals:
    algedonic: outlier sequential DPO seed2 behavior triggered lineage and merged-checkpoint audit.
- id: 002-clean-dpo-recovered
  at: '2026-06-16T22:36:00Z'
  kind: result
  title: Clean SFT->DPO Seed2 Recovered
  summary: The low-memory SFT seed2 merge passed behavioral sanity checks, clean SFT->DPO seed2 training completed, and full SelfAware eval produced plausible seed2 metrics with no thinking-token contamination.
  evidence:
  - experiment/phase1/eval/results_sft_merged_seed2_lowmem_selfaware_192_sanity
  - experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b/sft_dpo_seed2_lowmem__selfaware/metrics.json
  - experiment/phase1/eval/analysis/amendment_a_transition_report.md
  - TODO.md
  run_ids:
  - sft_dpo__4b__amendment_a__seed2
  commands: []
  decisions:
  - Use the clean low-memory seed2 DPO eval as the valid seed2 comparator.
  - Preserve the bad-merge attempt as provenance, not evidence.
  next_steps:
  - Continue the same recovery path for SFT->KTO seed2.
  signals:
    clean_selfaware_metrics: refusal_recall 65.89, over_refusal 18.36, truthful 34.82.
- id: 003-clean-kto-relaunched
  at: '2026-06-17T01:29:02Z'
  kind: launch
  title: Clean SFT->KTO Seed2 Relaunched
  summary: Clean SFT->KTO seed2 is running from the verified low-memory SFT seed2 merged base; the latest heartbeat saw step 1300 of 3599 with low OOM risk and stable VRAM.
  evidence:
  - experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json
  - synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/logs/training_20260616_223856.jsonl
  - .codex/pact/session.md
  run_ids:
  - sft_kto__4b__amendment_a__seed2
  commands: []
  decisions:
  - Keep monitoring until completion before treating KTO seed2 as evidence.
  - After completion, verify final_model, training_lineage, capacity features, concrete training log, and behavioral eval.
  next_steps:
  - Continue heartbeat monitoring.
  - On completion, update the run record, TODO, transition report, and this session note.
  signals:
    container: zealous_villani
    container_id: 2a33dd0f3d8f
    latest_step: 1300
    total_steps: 3599
    oom_risk: low
- id: 004-pr39-session-memory-pulled
  at: '2026-06-17T01:29:02Z'
  kind: infrastructure
  title: PR39 Session Memory Pulled
  summary: Remote main was fast-forwarded to PR #39, adding KG search and research-session memory infrastructure; local skill conflicts were resolved by preserving both the new search instructions and the Windows validation gotcha.
  evidence:
  - .skills/experiment-runner/reference/research-sessions.md
  - .skills/experiment-runner/scripts/research_session.py
  - .skills/knowledge-graph/SKILL.md
  - docs/sessions/0001 - kg-search-and-session-memory.md
  run_ids: []
  commands:
  - git fetch origin main
  - git merge --ff-only origin/main
  - py -3.11 sync_skills.py --check
  decisions:
  - Use docs/sessions notes for meaningful experiment checkpoints moving forward.
  - Keep KG skill trees in sync from canonical .skills sources.
  next_steps:
  - Validate this session note.
  - Use the session note as the durable checkpoint for the ongoing KTO seed2 heartbeat.
  signals:
    pulled_commit: b963ae72
- id: 005-meta-workflow-instructions
  at: '2026-06-17T01:38:00Z'
  kind: infrastructure
  title: Meta Workflow Instructions Updated
  summary: Root project instructions and the experiment-runner research-session taxonomy now explicitly support the search, do, save, validate loop for ongoing research work.
  evidence:
  - AGENTS.md
  - CLAUDE.md
  - .skills/experiment-runner/scripts/research_session.py
  - .skills/experiment-runner/reference/research-sessions.md
  run_ids: []
  commands:
  - py -3.12 sync_skills.py --check
  - py -3.12 .agents/skills/experiment-runner/scripts/research_session.py validate docs/sessions
  - python -m pytest .skills/experiment-runner/tests/test_run_matrix.py -q
  decisions:
  - Treat KG/local search as the first-pass discovery path for project research tasks.
  - Save meaningful gates, launches, heartbeats, recoveries, results, decisions, and infrastructure changes under docs/sessions.
  next_steps:
  - Continue KTO seed2 heartbeat monitoring and append durable checkpoints when state changes materially.
  signals: {}
- id: 006-clean-kto-training-complete
  at: '2026-06-17T06:09:09Z'
  kind: result
  title: Clean SFT->KTO Seed2 Training Complete
  summary: Clean SFT->KTO seed2 completed training from the verified low-memory SFT seed2 merged base, saved final adapter artifacts, and ended with low OOM risk; behavioral eval is still pending before scientific interpretation.
  evidence:
  - experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json
  - synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/logs/training_20260616_223856.jsonl
  - synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/capacity_features.json
  - synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/final_model/adapter_model.safetensors
  - TODO.md
  run_ids:
  - sft_kto__4b__amendment_a__seed2
  commands:
  - docker ps -a --filter name=zealous_villani
  - nvidia-smi --query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total --format=csv
  decisions:
  - Mark the run record completed and verified for training artifacts.
  - Keep the result out of behavioral evidence summaries until full SelfAware eval and plausibility audit complete.
  next_steps:
  - Create or reuse a full SelfAware eval config for clean SFT->KTO seed2 lowmem.
  - Run eval, scan for thinking-token contamination, and compare against KTO seed1 plus DPO seed2 controls before interpreting.
  signals:
    final_step: 3599
    total_steps: 3599
    final_loss: 0.2636691490522058
    train_runtime_seconds: 26859.501
    peak_gpu_memory_reserved_gb: 4.393
    oom_risk: low
- id: 007-clean-kto-eval-complete
  at: '2026-06-17T10:01:08Z'
  kind: result
  title: Clean SFT->KTO Seed2 Eval Complete
  summary: Clean SFT->KTO seed2 full SelfAware eval completed with no thinking-token contamination; behavior is consistent with seed1 KTO, preserving high unknown refusal while retaining high over-refusal.
  evidence:
  - experiment/phase1/eval/config/eval_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b.yaml
  - experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b/sft_kto_seed2_lowmem__selfaware/metrics.json
  - experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b/sft_kto_seed2_lowmem__selfaware/scored_rows.jsonl
  - experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json
  - TODO.md
  run_ids:
  - sft_kto__4b__amendment_a__seed2
  commands:
  - docker logs --tail 120 eh-amendment-kto-seed2-eval
  - rg -n "<think>|</think>|reasoning_content" experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b
  decisions:
  - Treat clean KTO seed2 as bounded local behavioral evidence.
  - Keep KTO seed3 as the remaining clean KTO three-seed gap.
  next_steps:
  - Run or prepare clean SFT->KTO seed3 from the corresponding verified SFT seed3 merge.
  - Add KTO seed2 to the Amendment A comparison report after seed3 or when making an interim two-seed readout.
  signals:
    config_sha: b18d66c711bc62bd
    n: 3369
    n_unknown_labeled: 1032
    n_known_labeled: 2337
    refusal_recall_pct: 78.68
    answer_on_unknown_pct: 21.32
    over_refusal_pct: 45.53
    correct_on_known_pct: 37.16
    truthful_pct: 38.14
    contamination_matches: 0
---
# Amendment A Seed2 Recovery

## Question

How did we recover clean Amendment A seed2 evidence after discovering the bad SFT seed2 merge?

## Trajectory Position

This sits inside the signed Amendment A extension, not the locked v0.3 headline matrix. The local question is whether SFT-warmed DPO or KTO can preserve SFT's unknown-question abstention while reducing known-question over-refusal.

## Summary

The original sequential seed2 DPO and KTO path was not clean evidence because the first merged SFT seed2 checkpoint lost the expected SFT refusal behavior. The SFT seed2 model was re-merged through a lower-memory path, sanity-checked behaviorally, and then used for a clean SFT->DPO seed2 rerun/eval and clean SFT->KTO seed2 training/eval.

## Checkpoints

### 001-bad-merge-detected - Bad SFT Seed2 Merge Detected

- at: `2026-06-16T20:06:46Z`
- kind: `result`
- summary: Post-hoc sanity evaluation showed the original merged SFT seed2 checkpoint behaved base-like despite structural validity, so downstream sequential seed2 artifacts using that merge were confounded.
- evidence:
  - `experiment/phase1/eval/results_sft_merged_seed2_selfaware_192_sanity`
  - `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json`
- decisions:
  - Exclude the original SFT->DPO seed2 result from clean sequential evidence.
  - Stop the active SFT->KTO seed2 run because it used the same bad merged base.

### 002-clean-dpo-recovered - Clean SFT->DPO Seed2 Recovered

- at: `2026-06-16T22:36:00Z`
- kind: `result`
- summary: The low-memory SFT seed2 merge passed behavioral sanity checks, clean SFT->DPO seed2 training completed, and full SelfAware eval produced plausible seed2 metrics with no thinking-token contamination.
- evidence:
  - `experiment/phase1/eval/results_sft_merged_seed2_lowmem_selfaware_192_sanity`
  - `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_dpo_lowmem_local_4b/sft_dpo_seed2_lowmem__selfaware/metrics.json`
  - `experiment/phase1/eval/analysis/amendment_a_transition_report.md`
  - `TODO.md`
- metrics: refusal_recall 65.89, over_refusal 18.36, truthful 34.82.

### 003-clean-kto-relaunched - Clean SFT->KTO Seed2 Relaunched

- at: `2026-06-17T01:29:02Z`
- kind: `launch`
- summary: Clean SFT->KTO seed2 is running from the verified low-memory SFT seed2 merged base; the latest heartbeat saw step 1300 of 3599 with low OOM risk and stable VRAM.
- evidence:
  - `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json`
  - `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/logs/training_20260616_223856.jsonl`
  - `.codex/pact/session.md`
- next steps:
  - Continue heartbeat monitoring.
  - On completion, verify artifacts and run the behavioral eval before using KTO seed2 as evidence.

### 004-pr39-session-memory-pulled - PR39 Session Memory Pulled

- at: `2026-06-17T01:29:02Z`
- kind: `infrastructure`
- summary: Remote main was fast-forwarded to PR #39, adding KG search and research-session memory infrastructure; local skill conflicts were resolved by preserving both the new search instructions and the Windows validation gotcha.
- evidence:
  - `.skills/experiment-runner/reference/research-sessions.md`
  - `.skills/experiment-runner/scripts/research_session.py`
  - `.skills/knowledge-graph/SKILL.md`
  - `docs/sessions/0001 - kg-search-and-session-memory.md`

### 005-meta-workflow-instructions - Meta Workflow Instructions Updated

- at: `2026-06-17T01:38:00Z`
- kind: `infrastructure`
- summary: Root project instructions and the experiment-runner research-session taxonomy now explicitly support the search, do, save, validate loop for ongoing research work.
- evidence:
  - `AGENTS.md`
  - `CLAUDE.md`
  - `.skills/experiment-runner/scripts/research_session.py`
  - `.skills/experiment-runner/reference/research-sessions.md`

### 006-clean-kto-training-complete - Clean SFT->KTO Seed2 Training Complete

- at: `2026-06-17T06:09:09Z`
- kind: `result`
- summary: Clean SFT->KTO seed2 completed training from the verified low-memory SFT seed2 merged base, saved final adapter artifacts, and ended with low OOM risk; behavioral eval is still pending before scientific interpretation.
- evidence:
  - `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json`
  - `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/logs/training_20260616_223856.jsonl`
  - `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/capacity_features.json`
  - `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_kto__4b__amendment_a__seed2/20260616_183650/final_model/adapter_model.safetensors`
- metrics: final step 3,599 / 3,599, final loss 0.2636691490522058, train runtime 26,859.501 seconds, peak reserved VRAM 4.393 GB, OOM risk low.
- next steps:
  - Run clean full SelfAware eval and contamination scan before interpreting seed2 KTO behavior.

### 007-clean-kto-eval-complete - Clean SFT->KTO Seed2 Eval Complete

- at: `2026-06-17T10:01:08Z`
- kind: `result`
- summary: Clean SFT->KTO seed2 full SelfAware eval completed with no thinking-token contamination; behavior is consistent with seed1 KTO, preserving high unknown refusal while retaining high over-refusal.
- evidence:
  - `experiment/phase1/eval/config/eval_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b.yaml`
  - `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b/sft_kto_seed2_lowmem__selfaware/metrics.json`
  - `experiment/phase1/eval/results_amendment_a_selfaware_full_seed2_sft_kto_lowmem_local_4b/sft_kto_seed2_lowmem__selfaware/scored_rows.jsonl`
  - `experiment/phase1/run_records/sft_kto__4b__amendment_a__seed2.json`
- metrics: n 3,369 = 1,032 unknown / 2,337 known; refusal_recall 78.68, answer_on_unknown 21.32, over_refusal 45.53, correct_on_known 37.16, truthful 38.14.
- contamination: 0 matches for `<think>`, `</think>`, or `reasoning_content`.
- next steps:
  - Run or prepare clean SFT->KTO seed3 from the corresponding verified SFT seed3 merge.
 
 
