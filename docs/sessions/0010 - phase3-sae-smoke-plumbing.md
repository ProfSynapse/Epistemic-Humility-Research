---
schema_version: research-session/v1
session_id: phase3-sae-smoke-plumbing
title: Phase 3 SAE Smoke Plumbing
status: active
created_at: '2026-06-19T19:52:17Z'
updated_at: '2026-06-19T20:11:10Z'
phase: phase3
question: Add a CPU-only SAE-shaped plumbing smoke for verified SelfAware hidden-state extraction artifacts without making trained-SAE claims.
tags:
- phase3
- mech-interp
- sae-smoke
- plumbing
- cpu-only
run_ids: []
trajectory:
  anchor: experiment/protocol/research-trajectory.md
  current_position: Phase 3 has verified SelfAware hidden-state extraction artifacts and logit-diagnostic configs; SAE work remains future/governed.
  changed_by_session: Adds deterministic plumbing-only validation for extraction manifests, row selection, safetensor loading, and SAE-shaped output writing.
checkpoints:
- id: 001-implementation
  at: '2026-06-19T19:52:17Z'
  kind: infrastructure
  title: CPU-Only SAE Plumbing Smoke Added
  summary: Added a deterministic numpy-only script and config that load verified SelfAware DPO/KTO delta extraction artifacts, select a balanced known/unknown row slice, load role/layer safetensors, run a seeded random encoder/top-k/decode path, and write claim-safe smoke manifests and metrics.
  evidence:
  - experiment/phase1/probe/phase3_sae_smoke.py
  - experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml
  run_ids: []
  commands: []
  decisions:
  - Mark outputs with `SAE_PLUMBING_SMOKE_ONLY` and `phase3_sae_plumbing_smoke_only`.
  - Keep the smoke independent of Docker, GPU, full SAE training, and external SAE libraries.
  - Fail closed for unverified manifests, invalid labels, insufficient balance, missing shards/layers, tensor shape mismatches, and output roots inside source extraction dirs.
  next_steps:
  - Use this smoke as a plumbing gate before any governed real SAE training implementation.
  signals:
    seed: 20260619
    max_rows_per_label: 8
    bottleneck_dim: 16
    top_k: 4
    candidate_count: 2
- id: 002-validation
  at: '2026-06-19T19:52:17Z'
  kind: validation
  title: Focused Non-GPU Validation Planned
  summary: Focused validation should run the new pytest file, py_compile the smoke script, run skill sync checks, and optionally run the checked-in smoke config to create isolated outputs under `sae_smokes`.
  evidence:
  - experiment/phase1/probe/tests/test_phase3_sae_smoke.py
  - .skills/mech-interp-runner/SKILL.md
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/probe/tests/test_phase3_sae_smoke.py -q
  - python -m py_compile experiment/phase1/probe/phase3_sae_smoke.py
  - python bin/sync_skills.py --check
  decisions:
  - Keep generated smoke output isolated under the configured `sae_smokes` root when the smoke is run.
  - Do not promote smoke metrics to mechanism evidence.
  next_steps:
  - Record command outcomes after validation.
  signals:
    gpu_required: false
    docker_required: false
    trained_sae: false
- id: 003-result
  at: '2026-06-19T20:11:10Z'
  kind: result
  title: SelfAware DPO/KTO SAE Plumbing Smoke Passed
  summary: CPU-only SAE-shaped plumbing smoke completed against both verified full
    SelfAware extraction artifacts. The script loaded DPO delta L24 and KTO delta
    L25, selected 8 known and 8 unknown rows per candidate, built 16 x 2560 input
    matrices, applied the deterministic top-k bottleneck path, and wrote claim-safe
    manifests and metrics under the local ignored `sae_smokes` output root.
  evidence:
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_dpo_selfaware_full_delta_l24/run_manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_kto_selfaware_full_delta_l25/run_manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_dpo_selfaware_full_delta_l24/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_kto_selfaware_full_delta_l25/metrics.json
  run_ids: []
  commands:
  - python experiment\phase1\probe\phase3_sae_smoke.py --config experiment\phase1\probe\config\phase3_selfaware_sae_smoke.yaml
  decisions:
  - Treat `sae_smokes` outputs as local generated artifacts and keep tensor slices
    out of git by default.
  - Do not interpret reconstruction metrics as SAE quality; they only show that
    the data path and output writing completed.
  next_steps:
  - Use this passing smoke as the gate before designing governed real SAE training
    objectives, splits, normalization, dictionary size, sparsity, and storage policy.
  signals:
    candidate_count: 2
    row_count_per_candidate: 16
    known_per_candidate: 8
    unknown_per_candidate: 8
    hidden_dim: 2560
    dpo_layer: 24
    kto_layer: 25
    bottleneck_dim: 16
    top_k: 4
    dpo_mean_mse: 0.8565788269042969
    kto_mean_mse: 0.27408140897750854
    dpo_code_density: 0.25
    kto_code_density: 0.25
---
# 0010 - Phase 3 SAE Smoke Plumbing

## Status

This session adds a plumbing-only validation path. It does not train an SAE,
change the protocol, run Docker/GPU work, or produce mechanism evidence for
paper claims.

## Summary

The Phase 3 SelfAware hidden-state extraction artifacts now have a small
CPU-only smoke path for validating the future SAE data flow. The smoke loads the
verified DPO delta L24 and KTO delta L25 extraction manifests, checks `rows.jsonl`
labels, selects a deterministic balanced known/unknown slice, loads
`<safe_row_key>__delta.safetensors`, reads `L<layer>`, runs a seeded random
encoder with top-k sparse code and decoder, then writes claim-safe manifests and
metrics under the configured `sae_smokes` root.

Every output is labeled `SAE_PLUMBING_SMOKE_ONLY` and
`phase3_sae_plumbing_smoke_only`. These outputs are only evidence that the
plumbing can read and write the expected artifacts.

## Checkpoints

### 001-implementation - CPU-Only SAE Plumbing Smoke Added

- at: `2026-06-19T19:52:17Z`
- kind: `implementation`
- summary: Added deterministic numpy-only script/config plumbing for verified SelfAware extraction artifacts.
- evidence:
  - `experiment/phase1/probe/phase3_sae_smoke.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml`
- decisions:
  - Mark outputs with `SAE_PLUMBING_SMOKE_ONLY` and `phase3_sae_plumbing_smoke_only`.
  - Keep the smoke independent of Docker, GPU, full SAE training, and external SAE libraries.
  - Fail closed for source and tensor plumbing defects.
- next steps:
  - Use this smoke as a plumbing gate before any governed real SAE training implementation.
- signals:
  - seed: `20260619`
  - max rows per label: `8`
  - bottleneck dimension: `16`
  - top-k: `4`
  - candidate count: `2`

### 002-validation - Focused Non-GPU Validation Planned

- at: `2026-06-19T19:52:17Z`
- kind: `validation`
- summary: Focused validation should run the new pytest file, py_compile the smoke script, run skill sync checks, and optionally run the checked-in smoke config to create isolated outputs under `sae_smokes`.
- evidence:
  - `experiment/phase1/probe/tests/test_phase3_sae_smoke.py`
  - `.skills/mech-interp-runner/SKILL.md`
- commands:
  - `python -m pytest experiment/phase1/probe/tests/test_phase3_sae_smoke.py -q`
  - `python -m py_compile experiment/phase1/probe/phase3_sae_smoke.py`
  - `python bin/sync_skills.py --check`
- decisions:
  - Keep generated smoke output isolated under the configured `sae_smokes` root when the smoke is run.
  - Do not promote smoke metrics to mechanism evidence.
- next steps:
  - Record command outcomes after validation.
- signals:
  - GPU required: `false`
  - Docker required: `false`
  - trained SAE: `false`

### 003-result - SelfAware DPO/KTO SAE Plumbing Smoke Passed

- at: `2026-06-19T20:11:10Z`
- kind: `result`
- summary: CPU-only SAE-shaped plumbing smoke completed against both verified full SelfAware extraction artifacts. The script loaded DPO delta L24 and KTO delta L25, selected 8 known and 8 unknown rows per candidate, built 16 x 2560 input matrices, applied the deterministic top-k bottleneck path, and wrote claim-safe manifests and metrics under the local ignored `sae_smokes` output root.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_dpo_selfaware_full_delta_l24/run_manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_kto_selfaware_full_delta_l25/run_manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_dpo_selfaware_full_delta_l24/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_smokes/phase3_selfaware_delta_plumbing_smoke/sft_kto_selfaware_full_delta_l25/metrics.json`
- commands:
  - `python experiment\phase1\probe\phase3_sae_smoke.py --config experiment\phase1\probe\config\phase3_selfaware_sae_smoke.yaml`
- decisions:
  - Treat `sae_smokes` outputs as local generated artifacts and keep tensor slices out of git by default.
  - Do not interpret reconstruction metrics as SAE quality; they only show that the data path and output writing completed.
- next steps:
  - Use this passing smoke as the gate before designing governed real SAE training objectives, splits, normalization, dictionary size, sparsity, and storage policy.
- signals:
  - candidates: `2`
  - rows per candidate: `16`, with `8` known and `8` unknown
  - hidden dim: `2560`
  - DPO layer: `24`
  - KTO layer: `25`
  - bottleneck dimension: `16`
  - top-k: `4`
  - DPO mean MSE: `0.8565788269042969`
  - KTO mean MSE: `0.27408140897750854`
  - code density: `0.25` for both candidates
