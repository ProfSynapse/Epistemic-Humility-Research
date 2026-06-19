---
schema_version: research-session/v1
session_id: phase3-selfaware-stratified-row-manifest
title: Phase 3 SelfAware Stratified Row Manifest
status: active
created_at: '2026-06-19T10:19:26Z'
updated_at: '2026-06-19T17:30:00Z'
phase: phase3
question: Track bounded no-GPU/no-Docker Phase 3 SelfAware stratified row-manifest
  work, including bridge failure rationale, manifest/script changes, validation, and
  result checkpoints.
tags:
- experiment-runner
- mech-interp
- selfaware
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-06-19T10:19:35Z'
  kind: planning
  title: No-GPU SelfAware Row Manifest Setup
  summary: 'Start a distinct Phase 3 row-manifest session for SelfAware stratified
    row selection. Scope is manifest/script planning and validation only: no GPU execution,
    no Docker execution, no synaptic-tuner edits, no PROTOCOL/library/KG/skills edits.
    Capture bridge failure rationale from existing artifacts if discoverable, then
    implement the smallest backend/script change needed for a deterministic stratified
    row manifest and record validation checkpoints here.'
  evidence:
  - docs/plans/phase3-stratified-row-selection-diagnostic.md
  - docs/sessions/0006 - phase3-causal-pilot-start.md
  run_ids: []
  commands: []
  decisions:
  - Keep 0006 as prior causal-pilot history and do not append this phase there unless
    a minimal pointer becomes necessary.
  - Treat bridge-row failures as a rationale to make row selection explicit and auditable
    rather than relying on implicit bridge replay state.
  next_steps:
  - Locate existing SelfAware evaluation outputs, row-selection diagnostics, and downstream
    causal-pilot consumers without touching forbidden areas.
  - Add or update a deterministic manifest/script path and focused no-GPU tests.
  signals: {}
- id: 002-infrastructure
  at: '2026-06-19T10:22:45Z'
  kind: infrastructure
  title: SelfAware Stratified Row Manifest Materialized
  summary: Added a no-GPU/no-Docker manifest builder for Phase 3 SelfAware stratified
    row selection and materialized row_manifest.json from existing Phase 3 causal-pilot
    scored_rows baselines. The builder deduplicates repeated coefficient-grid baselines
    only when behavioral fields are consistent, emits strata counts matching the prior
    diagnostic plan, and records that broad SelfAware eval rows are not runner-ready
    because they lack probe_pool_row_key.
  evidence:
  - experiment/phase1/probe/phase3_selfaware_stratified_row_manifest.py
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_selfaware_stratified_row_manifest/row_manifest.json
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py
  decisions:
  - Use the 12-row first-smoke union from existing Phase 3 probe_pool_row_key artifacts;
    do not create a broad runnable config from eval-local SelfAware identities until
    a validated bridge or frozen extraction exists.
  next_steps:
  - If approved later, feed first_smoke.row_keys_by_candidate into a logit-diagnostic
    config for the selected candidate directions.
  signals: {}
- id: 003-validation
  at: '2026-06-19T10:23:50Z'
  kind: validation
  title: Focused No-GPU Validation Passed
  summary: Focused no-GPU validation passed for the SelfAware stratified row-manifest
    builder and the new research session note. No Docker, GPU, synaptic-tuner, PROTOCOL,
    library/KG, or skill edits were made by this task.
  evidence:
  - experiment/phase1/probe/tests/test_phase3_selfaware_stratified_row_manifest.py
  - docs/sessions/0007 - phase-3-selfaware-stratified-row-manifest.md
  run_ids: []
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_phase3_selfaware_stratified_row_manifest.py
    -q
  - python -m py_compile experiment\phase1\probe\phase3_selfaware_stratified_row_manifest.py
  - python .skills\experiment-runner\scripts\research_session.py validate "docs\sessions\0007
    - phase-3-selfaware-stratified-row-manifest.md"
  decisions: []
  next_steps: []
  signals: {}
- id: 004-amendment
  at: '2026-06-19T10:29:20Z'
  kind: amendment
  title: Correction To Frozen SelfAware Manifest
  summary: Corrected the row-manifest artifact source and naming. The SelfAware-named
    builder now consumes only SelfAware row-level eval scored_rows artifacts and materializes
    a frozen SelfAware manifest keyed by eval_set, row_index, and raw id. The prior
    probe_pool_row_key smoke helper was retained under a probe-smoke-specific name
    and the stale ignored smoke output under the misleading SelfAware path was removed.
  evidence:
  - experiment/phase1/probe/phase3_selfaware_stratified_row_manifest.py
  - experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json
  - experiment/phase1/probe/phase3_probe_smoke_stratified_row_manifest.py
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py
  decisions:
  - The core manifest is not runner-ready for the current probe_pool_row_key causal-pilot
    runner; it is a frozen input for future dedicated SelfAware hidden-state extraction.
  next_steps:
  - Create a dedicated SelfAware extraction config/loader that reads experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json,
    renders prompts from its question/prompt fields, and emits hidden-state rows preserving
    row_key and strata.
  signals: {}
- id: 005-validation
  at: '2026-06-19T10:29:42Z'
  kind: validation
  title: Corrected SelfAware Manifest Validation Passed
  summary: Focused validation passed after correcting the manifest source and script
    naming. The true frozen SelfAware manifest contains 1233 high-signal rows from
    nine Amendment B sequential SelfAware row-level eval arms, with stable identity
    format selfaware::<eval_set>::<zero_padded_row_index>::<raw_id>.
  evidence:
  - experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json
  - experiment/phase1/probe/tests/test_phase3_selfaware_stratified_row_manifest.py
  - experiment/phase1/probe/tests/test_phase3_probe_smoke_stratified_row_manifest.py
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_selfaware_stratified_row_manifest.py
    experiment\\phase1\\probe\\tests\\test_phase3_probe_smoke_stratified_row_manifest.py
    -q
  - python -m py_compile experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py
    experiment\\phase1\\probe\\phase3_probe_smoke_stratified_row_manifest.py
  - python .skills\experiment-runner\scripts\research_session.py validate "docs\sessions\0007
    - phase-3-selfaware-stratified-row-manifest.md"
  decisions: []
  next_steps: []
  signals: {}
- id: 006-infrastructure
  at: '2026-06-19T10:34:43Z'
  kind: infrastructure
  title: SelfAware Extraction Prep Path Added
  summary: Prepared a no-GPU dedicated hidden-state extraction path for the frozen
    SelfAware manifest. hidden_state_probe.py now supports selection.source=selfaware_manifest,
    converts frozen SelfAware rows into extraction rows while preserving row_key,
    stable_identity, strata, label, question/prompt, answer metadata, and source-arm
    evidence, and leaves the existing probe_pool selection path as the default. Added
    a concrete prep config for sft_dpo_seed1 selecting 128 rows from the frozen manifest
    without running model extraction.
  evidence:
  - experiment/phase1/probe/hidden_state_probe.py
  - experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml
  - experiment/phase1/probe/tests/test_hidden_state_probe.py
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_hidden_state_probe.py
    -q
  - python -m py_compile experiment\\phase1\\probe\\hidden_state_probe.py
  - python -c parse_config_and_select_hidden_state_selfaware_manifest_sft_dpo_seed1
  decisions:
  - Do not run extraction until an explicit GPU gate is approved; the future command
    is python experiment/phase1/probe/hidden_state_probe.py --config experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml
    after verifying local model/adapter paths, disk budget, and whether max_rows should
    stay 128 or be raised.
  next_steps:
  - Open the GPU gate only after confirming the seed1 merged model and DPO adapter
    paths exist on the execution host, the frozen manifest is unchanged, and output
    space is sufficient for 128 rows x all layers x h_base/h_lora/delta.
  signals: {}
- id: 007-bugfix
  at: '2026-06-19T11:10:00Z'
  kind: checkpoint
  title: SelfAware Extraction Provenance Finalization Fixed
  summary: Fixed the SelfAware hidden-state extraction finalization bug where
    aligned_probe_config_sha remained null for selection.source=selfaware_manifest.
    SelfAware manifest rows now carry a deterministic tagged frozen-manifest SHA256
    value, and static provenance falls back to the same source identity before the
    strict Decision-D finalize gate. No GPU extraction was rerun.
  evidence:
  - experiment/phase1/probe/hidden_state_probe.py
  - experiment/phase1/probe/tests/test_hidden_state_probe.py
  run_ids: []
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_hidden_state_probe.py -q
  - python -m py_compile experiment\phase1\probe\hidden_state_probe.py
  decisions:
  - Preserve the strict finalization gate and use selfaware-manifest-sha256:<digest>
    as the aligned_probe_config_sha equivalent for frozen SelfAware manifest selection.
  next_steps:
  - The existing completed Docker artifacts can be finalized by rerunning the extraction
    command in resume mode only if an explicit GPU/Docker gate is opened later; the
    model forward does not need to be repeated.
  signals: {}
- id: 008-validation
  at: '2026-06-19T12:35:00Z'
  kind: validation
  title: SelfAware Extraction Finalized
  summary: Docker resume rerun completed in 114s with exit code 0 and finalized
    the existing 128-row SelfAware hidden-state extraction output. Manifest status
    is ok, verified is true, aligned_probe_config_sha is
    selfaware-manifest-sha256:8dc5e509f2f4ba27fb90c48c768eb28548b0872b119f402d2f90ef11741a5bc4,
    rows.jsonl was backfilled so 128/128 row-level aligned_probe_config_sha values
    match the manifest, bad rows are 0, 384 safetensors are present, and sampled
    delta tensors are nonzero.
  evidence:
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware/extraction__c34432cdf3cc
  run_ids: []
  commands: []
  decisions:
  - Treat this extraction as verified and finalized for downstream analysis.
  next_steps:
  - Analyze the verified extraction; do not rerun extraction unless analysis finds
    a new concrete defect.
  signals:
    rows: 128
    safetensors: 384
    bad_rows: 0
    manifest_status: ok
    verified: true
    strata:
      stable_known_correct: 86
      known_recovery_transition: 29
      known_corruption_transition: 13
- id: 009-validation
  at: '2026-06-19T17:10:30Z'
  kind: validation
  title: Full SelfAware Extraction Finalized
  summary: Full frozen-manifest SelfAware extraction completed and finalized for
    the seed1 SFT->DPO artifact. The full config selects all 1233 frozen SelfAware
    manifest rows into hidden_states_selfaware_full with extraction config sha d3d0e6d19c0eddb4.
    The first full run produced all rows and tensors but failed finalization because
    Git provenance fields were null; Docker resume with safe.directory configured
    for both /workspace/repo and /workspace/repo/synaptic-tuner fixed provenance
    operationally, wrote 0 new rows, skipped 1233 existing rows, and finalized the
    manifest in 152.1s.
  evidence:
  - experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1_full.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e
  run_ids: []
  commands: []
  decisions:
  - Treat the full extraction artifact as verified and finalized for downstream full-run
    analysis.
  - Record torchao cpp extension, tokenizer regex, and torch_dtype deprecation messages
    as runtime warnings, not blockers.
  next_steps:
  - Run full-run analysis over the verified hidden_states_selfaware_full artifact.
  signals:
    rows: 1233
    safetensors: 3699
    manifest_status: ok
    verified: true
    config_sha: d3d0e6d19c0eddb4
    output_subdir: hidden_states_selfaware_full
    resume_seconds: 152.1
    rows_written_on_resume: 0
    rows_skipped_on_resume: 1233
    research_repo_commit: 13075d10f610edd0375147e9ecc0b827dd755783
    submodule_commit: 3a3d7a26e976e70d095c7f965e7d6e7b210843f7
    aligned_probe_config_sha: selfaware-manifest-sha256:8dc5e509f2f4ba27fb90c48c768eb28548b0872b119f402d2f90ef11741a5bc4
    strata:
      known_recovery_transition: 120
      stable_known_correct: 368
      known_corruption_transition: 68
      kto_unknown_refusal_loss_transition: 137
      dpo_unknown_refusal_loss_transition: 447
      stable_unknown_refusal: 227
    runtime_warnings:
    - torchao cpp extension skipped due torch/torchao version
    - tokenizer regex warning
    - torch_dtype deprecated
- id: 010-analysis
  at: '2026-06-19T17:30:00Z'
  kind: result
  title: Full SelfAware Hidden-State Analysis Materialized
  summary: Fixed downstream analysis shard lookup for SelfAware row keys by mirroring
    the extraction writer's filesystem-safe tensor key behavior in the linear-probe
    and direction scripts. Full 1233-row k-fold linear-probe analysis and candidate-direction
    derivation now read the colon-keyed SelfAware shards. Best balanced accuracy
    by role was h_base layer 18 = 0.9723175669213522, h_lora layer 23 = 0.9745332242330212,
    and delta layer 24 = 0.9793510833873522. Direction derivation produced 222 ok
    manifest rows with 222 materialized vector shards.
  evidence:
  - experiment/phase1/probe/hidden_state_linear_probe.py
  - experiment/phase1/probe/hidden_state_directions.py
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e/selfaware_full_linear_probe_kfold5.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e/selfaware_full_candidate_directions.manifest.json
  run_ids: []
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_hidden_state_linear_probe.py
    experiment\phase1\probe\tests\test_hidden_state_directions.py -q
  - python experiment\phase1\probe\hidden_state_linear_probe.py experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\hidden_states_selfaware_full\extraction__d3d0e6d19c0e
    --cv stratified_kfold --cv-folds 5 --prefix selfaware_full_linear_probe_kfold5
  - python experiment\phase1\probe\hidden_state_directions.py experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\hidden_states_selfaware_full\extraction__d3d0e6d19c0e
    --prefix selfaware_full_candidate_directions
  decisions:
  - Treat the skipped analysis outputs from the pre-fix colon-key mismatch as superseded
    by the materialized k-fold and direction outputs.
  next_steps:
  - Use delta layer 24 as the top full-run diagnostic candidate if a later causal
    pilot needs one candidate from this analysis; keep the result labeled diagnostic/exploratory,
    not pre-registered headline evidence.
  signals:
    rows: 1233
    linear_probe_ok_rows: 111
    cv_strategy: stratified_kfold
    cv_folds: 5
    best_balanced_accuracy:
      h_base:
        layer: 18
        value: 0.9723175669213522
      h_lora:
        layer: 23
        value: 0.9745332242330212
      delta:
        layer: 24
        value: 0.9793510833873522
    directions_ok: 222
    direction_vector_files: 222
---
# Phase 3 SelfAware Stratified Row Manifest

## Question

Track bounded no-GPU/no-Docker Phase 3 SelfAware stratified row-manifest work, including bridge failure rationale, manifest/script changes, validation, and result checkpoints.

## Trajectory Position

_Not yet recorded._

## Summary

Created this session as the durable record for the Phase 3 pivot from the
TriviaQA/probe-pool row path to a dedicated frozen SelfAware row-manifest path.
The bridge from SelfAware eval identities into the existing `probe_pool_row_key`
causal-pilot runner failed for the high-signal stable-refusal and transition
strata, so the working plan is now: keep causal pilots on existing probe-pool
artifacts, and run a separate SelfAware hidden-state extraction path keyed by
stable `selfaware::<eval_set>::<row_index>::<raw_id>` identities.

Current state: the full frozen-manifest SelfAware extraction run is complete.
`experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1_full.yaml`
selected all 1233 frozen SelfAware manifest rows into
`hidden_states_selfaware_full` with extraction config sha
`d3d0e6d19c0eddb4`. The finalized artifact is
`experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e`.
The first full run produced all rows and tensors but failed finalization because
Git provenance fields were null. Docker resume with `safe.directory` configured
for both `/workspace/repo` and `/workspace/repo/synaptic-tuner` fixed provenance
operationally, wrote 0 new rows, skipped 1233 existing rows, and finalized the
manifest in 152.1s. The manifest is `ok` and verified; it records
`research_repo_commit=13075d10f610edd0375147e9ecc0b827dd755783`,
`submodule_commit=3a3d7a26e976e70d095c7f965e7d6e7b210843f7`, and
`aligned_probe_config_sha=selfaware-manifest-sha256:8dc5e509f2f4ba27fb90c48c768eb28548b0872b119f402d2f90ef11741a5bc4`.
The artifact has 1233 rows, 3699 safetensors, row-level provenance matching the
manifest, and sampled delta tensors are nonzero. The recorded non-exclusive
strata tag counts are: known_recovery_transition=120,
stable_known_correct=368, known_corruption_transition=68,
kto_unknown_refusal_loss_transition=137,
dpo_unknown_refusal_loss_transition=447, and stable_unknown_refusal=227.
Torchao cpp extension, tokenizer regex, and `torch_dtype` deprecation messages
were runtime warnings, not blockers.

Full-run analysis over this verified artifact is now materialized after fixing
analysis shard lookup for SelfAware row keys containing colons. The best
5-fold balanced accuracies by role are: h_base layer 18 = 0.9723175669213522,
h_lora layer 23 = 0.9745332242330212, and delta layer 24 =
0.9793510833873522. Candidate direction derivation produced 222 ok manifest
rows with 222 materialized vector shards. These are diagnostic/exploratory
Phase 3 artifacts, not pre-registered headline evidence.

## Checkpoints
### 001-planning - No-GPU SelfAware Row Manifest Setup

- at: `2026-06-19T10:19:35Z`
- kind: `planning`
- summary: Start a distinct Phase 3 row-manifest session for SelfAware stratified row selection. Scope is manifest/script planning and validation only: no GPU execution, no Docker execution, no synaptic-tuner edits, no PROTOCOL/library/KG/skills edits. Capture bridge failure rationale from existing artifacts if discoverable, then implement the smallest backend/script change needed for a deterministic stratified row manifest and record validation checkpoints here.
- evidence:
  - `docs/plans/phase3-stratified-row-selection-diagnostic.md`
  - `docs/sessions/0006 - phase3-causal-pilot-start.md`
- decisions:
  - Keep 0006 as prior causal-pilot history and do not append this phase there unless a minimal pointer becomes necessary.
  - Treat bridge-row failures as a rationale to make row selection explicit and auditable rather than relying on implicit bridge replay state.
- next steps:
  - Locate existing SelfAware evaluation outputs, row-selection diagnostics, and downstream causal-pilot consumers without touching forbidden areas.
  - Add or update a deterministic manifest/script path and focused no-GPU tests.
### 002-infrastructure - SelfAware Stratified Row Manifest Materialized

- at: `2026-06-19T10:22:45Z`
- kind: `infrastructure`
- summary: Added a no-GPU/no-Docker manifest builder for Phase 3 SelfAware stratified row selection and materialized row_manifest.json from existing Phase 3 causal-pilot scored_rows baselines. The builder deduplicates repeated coefficient-grid baselines only when behavioral fields are consistent, emits strata counts matching the prior diagnostic plan, and records that broad SelfAware eval rows are not runner-ready because they lack probe_pool_row_key.
- evidence:
  - `experiment/phase1/probe/phase3_selfaware_stratified_row_manifest.py`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_selfaware_stratified_row_manifest/row_manifest.json`
- commands:
  - `python experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py`
- decisions:
  - Use the 12-row first-smoke union from existing Phase 3 probe_pool_row_key artifacts; do not create a broad runnable config from eval-local SelfAware identities until a validated bridge or frozen extraction exists.
- next steps:
  - If approved later, feed first_smoke.row_keys_by_candidate into a logit-diagnostic config for the selected candidate directions.
### 003-validation - Focused No-GPU Validation Passed

- at: `2026-06-19T10:23:50Z`
- kind: `validation`
- summary: Focused no-GPU validation passed for the SelfAware stratified row-manifest builder and the new research session note. No Docker, GPU, synaptic-tuner, PROTOCOL, library/KG, or skill edits were made by this task.
- evidence:
  - `experiment/phase1/probe/tests/test_phase3_selfaware_stratified_row_manifest.py`
  - `docs/sessions/0007 - phase-3-selfaware-stratified-row-manifest.md`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_selfaware_stratified_row_manifest.py -q`
  - `python -m py_compile experiment\phase1\probe\phase3_selfaware_stratified_row_manifest.py`
  - `python .skills\experiment-runner\scripts\research_session.py validate "docs\sessions\0007 - phase-3-selfaware-stratified-row-manifest.md"`
### 004-amendment - Correction To Frozen SelfAware Manifest

- at: `2026-06-19T10:29:20Z`
- kind: `amendment`
- summary: Corrected the row-manifest artifact source and naming. The SelfAware-named builder now consumes only SelfAware row-level eval scored_rows artifacts and materializes a frozen SelfAware manifest keyed by eval_set, row_index, and raw id. The prior probe_pool_row_key smoke helper was retained under a probe-smoke-specific name and the stale ignored smoke output under the misleading SelfAware path was removed.
- evidence:
  - `experiment/phase1/probe/phase3_selfaware_stratified_row_manifest.py`
  - `experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json`
  - `experiment/phase1/probe/phase3_probe_smoke_stratified_row_manifest.py`
- commands:
  - `python experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py`
- decisions:
  - The core manifest is not runner-ready for the current probe_pool_row_key causal-pilot runner; it is a frozen input for future dedicated SelfAware hidden-state extraction.
- next steps:
  - Create a dedicated SelfAware extraction config/loader that reads experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json, renders prompts from its question/prompt fields, and emits hidden-state rows preserving row_key and strata.
### 005-validation - Corrected SelfAware Manifest Validation Passed

- at: `2026-06-19T10:29:42Z`
- kind: `validation`
- summary: Focused validation passed after correcting the manifest source and script naming. The true frozen SelfAware manifest contains 1233 high-signal rows from nine Amendment B sequential SelfAware row-level eval arms, with stable identity format selfaware::<eval_set>::<zero_padded_row_index>::<raw_id>.
- evidence:
  - `experiment/phase1/probe/manifests/phase3_selfaware_frozen_row_manifest.json`
  - `experiment/phase1/probe/tests/test_phase3_selfaware_stratified_row_manifest.py`
  - `experiment/phase1/probe/tests/test_phase3_probe_smoke_stratified_row_manifest.py`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_selfaware_stratified_row_manifest.py experiment\\phase1\\probe\\tests\\test_phase3_probe_smoke_stratified_row_manifest.py -q`
  - `python -m py_compile experiment\\phase1\\probe\\phase3_selfaware_stratified_row_manifest.py experiment\\phase1\\probe\\phase3_probe_smoke_stratified_row_manifest.py`
  - `python .skills\experiment-runner\scripts\research_session.py validate "docs\sessions\0007 - phase-3-selfaware-stratified-row-manifest.md"`
### 006-infrastructure - SelfAware Extraction Prep Path Added

- at: `2026-06-19T10:34:43Z`
- kind: `infrastructure`
- summary: Prepared a no-GPU dedicated hidden-state extraction path for the frozen SelfAware manifest. hidden_state_probe.py now supports selection.source=selfaware_manifest, converts frozen SelfAware rows into extraction rows while preserving row_key, stable_identity, strata, label, question/prompt, answer metadata, and source-arm evidence, and leaves the existing probe_pool selection path as the default. Added a concrete prep config for sft_dpo_seed1 selecting 128 rows from the frozen manifest without running model extraction.
- evidence:
  - `experiment/phase1/probe/hidden_state_probe.py`
  - `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml`
  - `experiment/phase1/probe/tests/test_hidden_state_probe.py`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_hidden_state_probe.py -q`
  - `python -m py_compile experiment\\phase1\\probe\\hidden_state_probe.py`
  - `python -c parse_config_and_select_hidden_state_selfaware_manifest_sft_dpo_seed1`
- decisions:
  - Do not run extraction until an explicit GPU gate is approved; the future command is python experiment/phase1/probe/hidden_state_probe.py --config experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml after verifying local model/adapter paths, disk budget, and whether max_rows should stay 128 or be raised.
- next steps:
  - Open the GPU gate only after confirming the seed1 merged model and DPO adapter paths exist on the execution host, the frozen manifest is unchanged, and output space is sufficient for 128 rows x all layers x h_base/h_lora/delta.
### 007-bugfix - SelfAware Extraction Provenance Finalization Fixed

- at: `2026-06-19T11:10:00Z`
- kind: `checkpoint`
- summary: Fixed the SelfAware hidden-state extraction finalization bug where aligned_probe_config_sha remained null for selection.source=selfaware_manifest. SelfAware manifest rows now carry a deterministic tagged frozen-manifest SHA256 value, and static provenance falls back to the same source identity before the strict Decision-D finalize gate. No GPU extraction was rerun.
- evidence:
  - `experiment/phase1/probe/hidden_state_probe.py`
  - `experiment/phase1/probe/tests/test_hidden_state_probe.py`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_hidden_state_probe.py -q`
  - `python -m py_compile experiment\phase1\probe\hidden_state_probe.py`
- decisions:
  - Preserve the strict finalization gate and use `selfaware-manifest-sha256:<digest>` as the aligned_probe_config_sha equivalent for frozen SelfAware manifest selection.
- next steps:
  - The existing completed Docker artifacts can be finalized by rerunning the extraction command in resume mode only if an explicit GPU/Docker gate is opened later; the model forward does not need to be repeated.
### 008-validation - SelfAware Extraction Finalized

- at: `2026-06-19T12:35:00Z`
- kind: `validation`
- summary: Docker resume rerun completed in 114s with exit code 0 and finalized the existing 128-row SelfAware hidden-state extraction output. Manifest status is ok, verified is true, aligned_probe_config_sha is selfaware-manifest-sha256:8dc5e509f2f4ba27fb90c48c768eb28548b0872b119f402d2f90ef11741a5bc4, rows.jsonl was backfilled so 128/128 row-level aligned_probe_config_sha values match the manifest, bad rows are 0, 384 safetensors are present, and sampled delta tensors are nonzero.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware/extraction__c34432cdf3cc`
- decisions:
  - Treat this extraction as verified and finalized for downstream analysis.
- next steps:
  - Analyze the verified extraction; do not rerun extraction unless analysis finds a new concrete defect.
- signals:
  - rows: `128`
  - safetensors: `384`
  - bad rows: `0`
  - manifest status: `ok`
  - verified: `true`
  - strata: `stable_known_correct=86`, `known_recovery_transition=29`, `known_corruption_transition=13`

### 009-validation - Full SelfAware Extraction Finalized

- at: `2026-06-19T17:10:30Z`
- kind: `validation`
- summary: Full frozen-manifest SelfAware extraction completed and finalized for the seed1 SFT->DPO artifact. The full config selects all 1233 frozen SelfAware manifest rows into hidden_states_selfaware_full with extraction config sha d3d0e6d19c0eddb4. The first full run produced all rows and tensors but failed finalization because Git provenance fields were null; Docker resume with safe.directory configured for both /workspace/repo and /workspace/repo/synaptic-tuner fixed provenance operationally, wrote 0 new rows, skipped 1233 existing rows, and finalized the manifest in 152.1s.
- evidence:
  - `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1_full.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e`
- decisions:
  - Treat the full extraction artifact as verified and finalized for downstream full-run analysis.
  - Record torchao cpp extension, tokenizer regex, and torch_dtype deprecation messages as runtime warnings, not blockers.
- next steps:
  - Run full-run analysis over the verified hidden_states_selfaware_full artifact.
- signals:
  - rows: `1233`
  - safetensors: `3699`
  - manifest status: `ok`
  - verified: `true`
  - config sha: `d3d0e6d19c0eddb4`
  - output subdir: `hidden_states_selfaware_full`
  - resume: `152.1s`, `0` rows written, `1233` existing rows skipped
  - research repo commit: `13075d10f610edd0375147e9ecc0b827dd755783`
  - submodule commit: `3a3d7a26e976e70d095c7f965e7d6e7b210843f7`
  - aligned probe config sha: `selfaware-manifest-sha256:8dc5e509f2f4ba27fb90c48c768eb28548b0872b119f402d2f90ef11741a5bc4`
  - strata: `known_recovery_transition=120`, `stable_known_correct=368`, `known_corruption_transition=68`, `kto_unknown_refusal_loss_transition=137`, `dpo_unknown_refusal_loss_transition=447`, `stable_unknown_refusal=227`
  - runtime warnings: `torchao cpp extension skipped due torch/torchao version`, `tokenizer regex warning`, `torch_dtype deprecated`

### 010-analysis - Full SelfAware Hidden-State Analysis Materialized

- at: `2026-06-19T17:30:00Z`
- kind: `result`
- summary: Fixed downstream analysis shard lookup for SelfAware row keys by mirroring the extraction writer's filesystem-safe tensor key behavior in the linear-probe and direction scripts. Full 1233-row k-fold linear-probe analysis and candidate-direction derivation now read the colon-keyed SelfAware shards. Best balanced accuracy by role was h_base layer 18 = 0.9723175669213522, h_lora layer 23 = 0.9745332242330212, and delta layer 24 = 0.9793510833873522. Direction derivation produced 222 ok manifest rows with 222 materialized vector shards.
- evidence:
  - `experiment/phase1/probe/hidden_state_linear_probe.py`
  - `experiment/phase1/probe/hidden_state_directions.py`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e/selfaware_full_linear_probe_kfold5.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/hidden_states_selfaware_full/extraction__d3d0e6d19c0e/selfaware_full_candidate_directions.manifest.json`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_hidden_state_linear_probe.py experiment\phase1\probe\tests\test_hidden_state_directions.py -q`
  - `python experiment\phase1\probe\hidden_state_linear_probe.py experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\hidden_states_selfaware_full\extraction__d3d0e6d19c0e --cv stratified_kfold --cv-folds 5 --prefix selfaware_full_linear_probe_kfold5`
  - `python experiment\phase1\probe\hidden_state_directions.py experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\hidden_states_selfaware_full\extraction__d3d0e6d19c0e --prefix selfaware_full_candidate_directions`
- decisions:
  - Treat the skipped analysis outputs from the pre-fix colon-key mismatch as superseded by the materialized k-fold and direction outputs.
- next steps:
  - Use delta layer 24 as the top full-run diagnostic candidate if a later causal pilot needs one candidate from this analysis; keep the result labeled diagnostic/exploratory, not pre-registered headline evidence.
- signals:
  - rows: `1233`
  - linear probe ok rows: `111`
  - cv: `stratified_kfold`, folds: `5`
  - best balanced accuracy: `h_base L18=0.9723175669213522`, `h_lora L23=0.9745332242330212`, `delta L24=0.9793510833873522`
  - directions ok: `222`
  - direction vector files: `222`
