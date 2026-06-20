---
schema_version: research-session/v1
session_id: phase3-sae-smoke-plumbing
title: Phase 3 SAE Smoke Plumbing
status: active
created_at: '2026-06-19T19:52:17Z'
updated_at: '2026-06-20T00:40:00Z'
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
- id: 004-result
  at: '2026-06-19T21:05:00Z'
  kind: result
  title: First Trained SAE Pilot Completed
  summary: >-
    Added and ran a bounded PyTorch SAE training pilot over both verified
    SelfAware delta extraction slices. The pilot trained 128-feature ReLU SAEs
    for 80 epochs on CPU with deterministic train/validation splits. Training
    completed for DPO L24 and KTO L25, and local L1 sensitivity showed the
    simple ReLU+L1 setup trains but remains dense: L1 1e-4 and 1e-2 produced
    roughly 69-74 active features per validation row, while L1 1e-1 improved
    only to roughly 58-59 active features per validation row.
  evidence:
  - experiment/phase1/probe/phase3_sae_train.py
  - experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_l1_0_1/sft_dpo_selfaware_full_delta_l24/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_l1_0_1/sft_kto_selfaware_full_delta_l25/metrics.json
  run_ids: []
  commands:
  - python experiment\phase1\probe\phase3_sae_train.py --config experiment\phase1\probe\config\phase3_selfaware_sae_pilot.yaml
  - python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_l1_0_01.yaml
  - python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_l1_0_1.yaml
  decisions:
  - Treat the trained SAE outputs as `SAE_TRAINING_PILOT_ONLY`; they prove the real
    training path works but do not yet establish interpretable feature recovery.
  - Update the checked-in pilot config to the stronger L1 0.1 local default because
    1e-4 and 1e-2 were clearly too dense.
  next_steps:
  - Design the next governed SAE run around explicit target sparsity, top-k or
    JumpReLU-style constraints, dead-feature handling, and a reconstruction/sparsity
    sweep before making feature-level claims.
  signals:
    device: cpu
    row_count_per_candidate: 1233
    hidden_dim: 2560
    dictionary_size: 128
    epochs: 80
    selected_l1_coefficient: 0.1
    dpo_l1_0_1_validation_mse: 0.5074488520622253
    kto_l1_0_1_validation_mse: 0.5550731420516968
    dpo_l1_0_1_validation_mean_active_features: 58.065040588378906
    kto_l1_0_1_validation_mean_active_features: 59.03658676147461
- id: 005-result
  at: '2026-06-19T21:35:00Z'
  kind: result
  title: Top-K SAE Sensitivity Completed
  summary: >-
    Added top-k ReLU activation support to the SAE pilot and ran local k=8, k=16,
    and k=32 sensitivity points over the same full DPO L24 and KTO L25 SelfAware
    delta slices. Top-k produced exact sparse codes. k=16 is now the checked-in
    interpretability pilot default because it gives exact 16/128 active features
    with moderate reconstruction cost, while k=32 is the softer reconstruction
    compromise.
  evidence:
  - experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk16/sft_dpo_selfaware_full_delta_l24/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk16/sft_kto_selfaware_full_delta_l25/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk32/sft_dpo_selfaware_full_delta_l24/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk32/sft_kto_selfaware_full_delta_l25/metrics.json
  run_ids: []
  commands:
  - python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk8.yaml
  - python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk16.yaml
  - python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk32.yaml
  decisions:
  - Keep top-k k=16 as the checked-in interpretability pilot default.
  - Keep k=32 in the session record as the lower-reconstruction comparison point.
  next_steps:
  - Inspect learned top-k feature activations by label and candidate, then design
    feature-level logit/intervention diagnostics only after selecting stable features.
  signals:
    dictionary_size: 128
    epochs: 80
    topk8_dpo_validation_mse: 0.5614777207374573
    topk8_kto_validation_mse: 0.6116589307785034
    topk8_validation_active_features: 8
    topk16_dpo_validation_mse: 0.5362363457679749
    topk16_kto_validation_mse: 0.5912008881568909
    topk16_validation_active_features: 16
    topk32_dpo_validation_mse: 0.5151500701904297
    topk32_kto_validation_mse: 0.5658350586891174
    topk32_validation_active_features: 32
- id: 006-result
  at: '2026-06-19T22:25:00Z'
  kind: result
  title: Top-K SAE Feature Screen Completed
  summary: >-
    Added and ran a feature-analysis runner that reloads trained SAE weights,
    saved normalization tensors, selected rows, and verified hidden-state shards
    to recompute codes and rank SAE features by known/unknown activation
    separation. The checked-in analysis targets the current top-k16 DPO L24 and
    KTO L25 SelfAware delta SAE pilots. DPO showed stronger top feature
    separation than KTO in this screen, but these are candidate features only
    and require row-level inspection plus causal/logit interventions before
    mechanism claims.
  evidence:
  - experiment/phase1/probe/phase3_sae_feature_analysis.py
  - experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_analysis/phase3_selfaware_delta_topk16_features/sft_dpo_selfaware_full_delta_l24_topk16/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_analysis/phase3_selfaware_delta_topk16_features/sft_kto_selfaware_full_delta_l25_topk16/summary.json
  run_ids: []
  commands:
  - python experiment\phase1\probe\phase3_sae_feature_analysis.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_analysis.yaml
  decisions:
  - Treat feature screen outputs as `SAE_FEATURE_ANALYSIS_ONLY`; do not promote
    them to causal or monosemantic-feature evidence.
  - Use the top separated features as a queue for the next controlled logit or
    activation-intervention pass.
  next_steps:
  - Inspect top activating examples for the strongest known-skewed and
    unknown-skewed features, then design feature-level causal diagnostics.
  signals:
    dictionary_size: 128
    top_k: 16
    row_count_per_candidate: 1233
    dpo_mean_active_features: 15.968369829683699
    kto_mean_active_features: 15.94809407948094
    dpo_top_feature: 64
    dpo_top_feature_abs_cohen_d: 1.2849521566888198
    dpo_top_feature_direction: known_skewed
    dpo_top_feature_known_activation_frequency: 0.5737410071942446
    dpo_top_feature_unknown_activation_frequency: 0.022156573116691284
    kto_top_feature: 110
    kto_top_feature_abs_cohen_d: 0.8848182554650794
    kto_top_feature_direction: unknown_skewed
    kto_top_feature_known_activation_frequency: 0.02697841726618705
    kto_top_feature_unknown_activation_frequency: 0.35893648449039883
- id: 007-result
  at: '2026-06-19T22:55:00Z'
  kind: result
  title: SAE Feature Direction Export Completed
  summary: >-
    Added and ran a bridge exporter that converts selected SAE decoder columns
    from standardized SAE space back into raw hidden-state direction candidates
    by multiplying decoder columns by the saved training normalization scale.
    The checked-in config exports the top two unknown-skewed and top two
    known-skewed features for each DPO/KTO top-k16 SAE. These local artifacts
    are ready to feed the existing logit-diagnostic runner, but remain
    candidate directions only until controlled interventions are run.
  evidence:
  - experiment/phase1/probe/phase3_sae_feature_directions.py
  - experiment/phase1/probe/config/phase3_selfaware_sae_feature_directions.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_directions/phase3_selfaware_delta_topk16_feature_directions/sae_feature_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_directions/phase3_selfaware_delta_topk16_feature_directions/sae_feature_directions.csv
  run_ids: []
  commands:
  - python experiment\phase1\probe\phase3_sae_feature_directions.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_directions.yaml
  decisions:
  - Keep exported feature directions labeled `SAE_FEATURE_DIRECTION_CANDIDATES_ONLY`.
  - Preserve feature polarity instead of flipping all vectors to an
    unknown-positive convention; addition/subtraction controls must be
    interpreted relative to `feature_skew_label`.
  - Do not reuse the old broad-direction coefficient grid blindly; SAE feature
    vectors have smaller norms and need their own coefficient smoke.
  next_steps:
  - Build a small logit-diagnostic config over these 8 feature directions with a
    feature-specific coefficient grid and no-vector, sign, wrong-layer, and
    random matched-norm controls.
  signals:
    direction_count: 8
    dpo_unknown_features: [51, 47]
    dpo_known_features: [64, 65]
    kto_unknown_features: [110, 62]
    kto_known_features: [43, 58]
    dpo_feature_direction_norm_range: [1.173532247543335, 1.249133825302124]
    kto_feature_direction_norm_range: [0.7090413570404053, 0.72569739818573]
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

### 004-result - First Trained SAE Pilot Completed

- at: `2026-06-19T21:05:00Z`
- kind: `result`
- summary: Added and ran a bounded PyTorch SAE training pilot over both verified SelfAware delta extraction slices. The pilot trained 128-feature ReLU SAEs for 80 epochs on CPU with deterministic train/validation splits. Training completed for DPO L24 and KTO L25, and local L1 sensitivity showed the simple ReLU+L1 setup trains but remains dense.
- evidence:
  - `experiment/phase1/probe/phase3_sae_train.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_l1_0_1/sft_dpo_selfaware_full_delta_l24/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_l1_0_1/sft_kto_selfaware_full_delta_l25/metrics.json`
- commands:
  - `python experiment\phase1\probe\phase3_sae_train.py --config experiment\phase1\probe\config\phase3_selfaware_sae_pilot.yaml`
  - `python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_l1_0_01.yaml`
  - `python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_l1_0_1.yaml`
- decisions:
  - Treat the trained SAE outputs as `SAE_TRAINING_PILOT_ONLY`; they prove the real training path works but do not yet establish interpretable feature recovery.
  - Update the checked-in pilot config to the stronger L1 `0.1` local default because `1e-4` and `1e-2` were clearly too dense.
- next steps:
  - Design the next governed SAE run around explicit target sparsity, top-k or JumpReLU-style constraints, dead-feature handling, and a reconstruction/sparsity sweep before making feature-level claims.
- signals:
  - device: `cpu`
  - rows per candidate: `1233`
  - hidden dim: `2560`
  - dictionary size: `128`
  - epochs: `80`
  - selected L1 coefficient: `0.1`
  - DPO validation MSE at L1 0.1: `0.5074488520622253`
  - KTO validation MSE at L1 0.1: `0.5550731420516968`
  - DPO validation mean active features at L1 0.1: `58.065040588378906`
  - KTO validation mean active features at L1 0.1: `59.03658676147461`

### 005-result - Top-K SAE Sensitivity Completed

- at: `2026-06-19T21:35:00Z`
- kind: `result`
- summary: Added top-k ReLU activation support to the SAE pilot and ran local k=8, k=16, and k=32 sensitivity points over the same full DPO L24 and KTO L25 SelfAware delta slices. Top-k produced exact sparse codes. k=16 is now the checked-in interpretability pilot default because it gives exact 16/128 active features with moderate reconstruction cost, while k=32 is the softer reconstruction compromise.
- evidence:
  - `experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk16/sft_dpo_selfaware_full_delta_l24/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk16/sft_kto_selfaware_full_delta_l25/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk32/sft_dpo_selfaware_full_delta_l24/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_runs/phase3_selfaware_delta_sae_pilot_topk32/sft_kto_selfaware_full_delta_l25/metrics.json`
- commands:
  - `python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk8.yaml`
  - `python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk16.yaml`
  - `python experiment\phase1\probe\phase3_sae_train.py --config .tmp\phase3_selfaware_sae_pilot_topk32.yaml`
- decisions:
  - Keep top-k k=16 as the checked-in interpretability pilot default.
  - Keep k=32 in the session record as the lower-reconstruction comparison point.
- next steps:
  - Inspect learned top-k feature activations by label and candidate, then design feature-level logit/intervention diagnostics only after selecting stable features.
- signals:
  - dictionary size: `128`
  - epochs: `80`
  - top-k 8 validation MSE: DPO `0.5614777207374573`, KTO `0.6116589307785034`, active features `8`
  - top-k 16 validation MSE: DPO `0.5362363457679749`, KTO `0.5912008881568909`, active features `16`
  - top-k 32 validation MSE: DPO `0.5151500701904297`, KTO `0.5658350586891174`, active features `32`

### 006-result - Top-K SAE Feature Screen Completed

- at: `2026-06-19T22:25:00Z`
- kind: `result`
- summary: Added and ran a feature-analysis runner that reloads trained SAE weights, saved normalization tensors, selected rows, and verified hidden-state shards to recompute codes and rank SAE features by known/unknown activation separation. The checked-in analysis targets the current top-k16 DPO L24 and KTO L25 SelfAware delta SAE pilots.
- evidence:
  - `experiment/phase1/probe/phase3_sae_feature_analysis.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_analysis/phase3_selfaware_delta_topk16_features/sft_dpo_selfaware_full_delta_l24_topk16/summary.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_analysis/phase3_selfaware_delta_topk16_features/sft_kto_selfaware_full_delta_l25_topk16/summary.json`
- commands:
  - `python experiment\phase1\probe\phase3_sae_feature_analysis.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_analysis.yaml`
- decisions:
  - Treat feature screen outputs as `SAE_FEATURE_ANALYSIS_ONLY`; they are candidate-feature prioritization, not causal or monosemantic-feature evidence.
  - Use the top separated features as a queue for controlled logit or activation-intervention diagnostics.
- next steps:
  - Inspect top activating examples for the strongest known-skewed and unknown-skewed features, then design feature-level causal diagnostics.
- signals:
  - dictionary size: `128`
  - top-k: `16`
  - rows per candidate: `1233`
  - mean active features: DPO `15.968369829683699`, KTO `15.94809407948094`
  - DPO top feature: `64`, known-skewed, |d| `1.2849521566888198`, known activation frequency `0.5737410071942446`, unknown activation frequency `0.022156573116691284`
  - KTO top feature: `110`, unknown-skewed, |d| `0.8848182554650794`, known activation frequency `0.02697841726618705`, unknown activation frequency `0.35893648449039883`

### 007-result - SAE Feature Direction Export Completed

- at: `2026-06-19T22:55:00Z`
- kind: `result`
- summary: Added and ran a bridge exporter that converts selected SAE decoder columns from standardized SAE space back into raw hidden-state direction candidates by multiplying decoder columns by the saved training normalization scale. The checked-in config exports the top two unknown-skewed and top two known-skewed features for each DPO/KTO top-k16 SAE.
- evidence:
  - `experiment/phase1/probe/phase3_sae_feature_directions.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_directions.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_directions/phase3_selfaware_delta_topk16_feature_directions/sae_feature_directions.manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_directions/phase3_selfaware_delta_topk16_feature_directions/sae_feature_directions.csv`
- commands:
  - `python experiment\phase1\probe\phase3_sae_feature_directions.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_directions.yaml`
- decisions:
  - Keep exported feature directions labeled `SAE_FEATURE_DIRECTION_CANDIDATES_ONLY`.
  - Preserve feature polarity instead of flipping all vectors to unknown-positive; addition/subtraction controls must be interpreted relative to `feature_skew_label`.
  - Do not reuse the old broad-direction coefficient grid blindly; SAE feature vectors have smaller norms and need their own coefficient smoke.
- next steps:
  - Build a small logit-diagnostic config over these 8 feature directions with a feature-specific coefficient grid and no-vector, sign, wrong-layer, and random matched-norm controls.
- signals:
  - direction count: `8`
  - DPO unknown-skewed features: `51`, `47`; DPO known-skewed features: `64`, `65`
  - KTO unknown-skewed features: `110`, `62`; KTO known-skewed features: `43`, `58`
  - DPO feature direction norm range: `1.173532247543335` to `1.249133825302124`
  - KTO feature direction norm range: `0.7090413570404053` to `0.72569739818573`

### 008-planned - SAE Feature Logit Diagnostic Ready

- at: `2026-06-20T03:20:00Z`
- kind: `plan`
- summary: Added a bounded logit-diagnostic config and Docker sweep over the 8 exported top-k16 SAE feature directions. The first live pass is a coefficient smoke, not a generation intervention: 4 top-activating rows per feature, coefficients `10.0` and `50.0`, and required controls for no-vector baseline, addition/subtraction, wrong-layer addition/subtraction, and deterministic random matched-norm.
- evidence:
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_logit_diagnostic/sweep_manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_logit_diagnostic/planned_commands.jsonl`
- commands:
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs`
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment\phase1\probe\phase3_causal_pilot_sweep.py experiment\phase1\probe\phase3_causal_pilot_runner.py`
- decisions:
  - Keep this as `tier2_exploratory_local` only if the live diagnostic runs; planned/materialized commands alone remain readiness evidence.
  - Use refusal-opener probability slices and top-k token movement first. Do not use row-specific answer aliases in this pass because the SelfAware extraction rows do not carry clean gold aliases, and prior model output text should not be silently promoted to ground truth.
  - Interpret activation addition/subtraction relative to each feature's `feature_skew_label`; unknown-skewed and known-skewed features have opposite semantic polarity.
- next steps:
  - Run the live Docker logit-diagnostic sweep serially and inspect `_execution_logs/execution_results.jsonl` plus per-candidate output manifests before making any mechanism claim.
- signals:
  - executable candidates: `8`
  - planned jobs: `8`
  - rows per candidate: `4`
  - coefficient grid: `10.0`, `50.0`
  - required controls: `no_vector_baseline`, `activation_addition`, `activation_subtraction`, `wrong_layer`, `wrong_layer_subtraction`, `random_matched_norm`

### 009-result - SAE Feature Logit Diagnostic Completed

- at: `2026-06-19T23:15:00Z`
- kind: `result`
- summary: Ran the 8-candidate SAE feature logit-diagnostic sweep in Docker/GPU, then patched the runner so configured logit-target probability slices persist into `logit_metrics.json` summaries. Reran the sweep after the patch; all 8 candidates completed successfully. The strongest movement was DPO unknown-skewed feature 47 at coefficient `50.0`, but the adjacent wrong-layer control nearly matched the source-layer effect, so this is a non-localized steering signal rather than a clean feature mechanism.
- evidence:
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_logit_diagnostic/_execution_logs/execution_results.jsonl`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_logit_diagnostic/sft_dpo_selfaware_full_delta_l24_topk16__f047_unknown/logit_diagnostic/run_20260619T230129Z/logit_metrics.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_logit_diagnostic/summary.csv`
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
- commands:
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_feature_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_feature_logit_diagnostic\summary.csv`
- decisions:
  - Treat this as `tier2_exploratory_local` screening evidence only.
  - Do not claim a localized SAE feature mechanism for feature 47 because the `wrong_layer` coefficient-50 control also shifted the same refusal-opener slice strongly.
  - Keep the row-level and summary target-slice metrics because they are more informative than top-1 changes alone.
  - Use latest successful run directories per candidate when summarizing this sweep root; an initial sandbox-blocked Docker attempt and an earlier pre-summary rerun remain in the append-only execution log.
- next steps:
  - Add a nearby-layer panel around DPO feature 47 and a broader row panel before making any layer- or feature-specific claim.
  - Add row-specific answer/refusal target slices once the diagnostic has clean single-token aliases or an explicit sequence-probability path.
  - If the nearby-layer panel still fails localization, shift from single SAE features toward multi-feature or subspace interventions.
- signals:
  - executable candidates completed in the rerun: `8/8`
  - rows per candidate: `4`
  - DPO feature 47 coefficient-50 source-layer addition: refusal-opener probability delta mean `+0.268498`, top-1 changed rate `100.0%`
  - DPO feature 47 coefficient-50 wrong-layer addition: refusal-opener probability delta mean `+0.244882`, top-1 changed rate `75.0%`
  - DPO feature 47 coefficient-50 source-layer subtraction: refusal-opener probability delta mean `-0.101644`, top-1 changed rate `25.0%`
  - DPO feature 47 coefficient-50 random matched-norm: refusal-opener probability delta mean `-0.079778`, top-1 changed rate `0.0%`
  - KTO feature directions were weaker in the same smoke; the largest KTO refusal-opener source-layer delta in the top summary was around `0.037823` absolute mean.

### 010-result - DPO Feature 47 Nearby-Layer Panel Completed

- at: `2026-06-19T23:25:00Z`
- kind: `result`
- summary: Added reusable multi-offset wrong-layer support and ran a one-candidate nearby-layer panel for DPO unknown-skewed SAE feature 47. The panel used the same 4 top-activating rows and coefficient `50.0`, comparing source-layer addition/subtraction against wrong-layer offsets `-2`, `-1`, `+1`, and `+2`. The source layer did not stand apart; nearby layers also moved refusal-opener probabilities strongly.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic/sft_dpo_selfaware_full_delta_l24_topk16__f047_unknown/logit_diagnostic/run_20260619T231849Z/logit_metrics.json`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
- decisions:
  - Treat feature 47 as a broad/non-local steering direction candidate, not a localized SAE feature knob.
  - Keep `control_settings.wrong_layer.layer_offsets` as reusable runner infrastructure for nearby-layer panels.
  - Do not promote this to mechanism evidence without a broader row panel and stronger controls.
- next steps:
  - Test whether multi-feature/subspace directions are more stable than single SAE decoder columns.
  - Add row-specific answer/refusal target slices or sequence-probability diagnostics before interpreting content-specific effects.
  - Consider activation patching or path-level attribution if the goal remains layer localization.
- signals:
  - source layer 24 addition: refusal-opener probability delta mean `+0.268498`, top-1 changed rate `100.0%`
  - wrong-layer offset `-1`: refusal-opener probability delta mean `+0.253672`, top-1 changed rate `100.0%`
  - wrong-layer offset `+1`: refusal-opener probability delta mean `+0.244882`, top-1 changed rate `75.0%`
  - wrong-layer offset `-2`: refusal-opener probability delta mean `+0.219151`, top-1 changed rate `75.0%`
  - wrong-layer offset `+2`: refusal-opener probability delta mean `+0.145846`, top-1 changed rate `75.0%`
  - source-layer subtraction: refusal-opener probability delta mean `-0.101644`, top-1 changed rate `25.0%`

### 011-result - DPO SAE Composite Direction Screen Completed

- at: `2026-06-19T23:40:00Z`
- kind: `result`
- summary: Added a reusable composite-direction exporter for SAE feature directions and ran a two-candidate DPO composite logit diagnostic. The screen compared an unknown-feature pair (`f47 + f51`) against an unknown-minus-known contrast (`f47 + f51 - f64 - f65`) on the 8-row union of top f47/f51 activating examples. The pair was weaker and no cleaner than feature 47 alone. The contrast had stronger signed structure but still failed clean locality: wrong-layer controls and random matched-norm remained substantial.
- evidence:
  - `experiment/phase1/probe/phase3_sae_feature_composites.py`
  - `experiment/phase1/probe/tests/test_phase3_sae_feature_composites.py`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composites.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_composites/phase3_selfaware_delta_topk16_feature_composites/sae_feature_composite_directions.manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_feature_composite_logit_diagnostic/summary.csv`
- commands:
  - `python experiment\phase1\probe\phase3_sae_feature_composites.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_composites.yaml`
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_sae_feature_composites.py experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_sae_feature_composite_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_feature_composite_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_feature_composite_logit_diagnostic\summary.csv`
- decisions:
  - Keep composite directions as explicit bridge artifacts labeled `SAE_FEATURE_COMPOSITE_DIRECTION_CANDIDATES_ONLY`.
  - Treat the contrast direction as an entangled subspace/perturbation lead, not a localized SAE mechanism.
  - Do not scale to more composite live sweeps until we map direction geometry against the broader known/unknown direction and random controls.
- next steps:
  - Run a cheap direction-geometry map across single SAE features, composites, random matched-norm, and the broader known/unknown delta directions.
  - If geometry shows high alignment with broad deltas, prioritize subspace diagnostics over sparse feature circuits.
  - If geometry shows low alignment but effects persist, consider a sparse feature circuit/path-level attribution pass.
- signals:
  - composite unknown pair norm: `1.1850064992904663`; contrast norm: `1.2142820358276367`
  - unknown pair coefficient-50 source addition: refusal-opener probability delta mean `+0.078996`, top-1 changed rate `37.5%`
  - unknown pair coefficient-50 random matched-norm: refusal-opener probability delta mean `+0.067841`, top-1 changed rate `62.5%`
  - contrast coefficient-50 source addition: refusal-opener probability delta mean `-0.119050`, top-1 changed rate `25.0%`
  - contrast coefficient-50 source subtraction: refusal-opener probability delta mean `+0.133768`, top-1 changed rate `62.5%`
  - contrast coefficient-50 wrong-layer subtraction offset `-1`: refusal-opener probability delta mean `+0.149519`, top-1 changed rate `62.5%`
  - contrast coefficient-50 random matched-norm: refusal-opener probability delta mean `+0.058642`, top-1 changed rate `50.0%`

### 012-result - Direction Geometry Map Added

- at: `2026-06-20T00:05:00Z`
- kind: `result`
- summary: Added a reusable CPU-only direction-geometry analyzer and ran two SelfAware geometry maps. The narrow map compared DPO layer-24 and KTO layer-25 broad deltas against top-k16 SAE feature directions and DPO composites. The all-delta-layer map compared the SAE directions against DPO/KTO broad delta inventories across all layers. The main finding is that the DPO unknown-minus-known SAE composite is geometrically aligned with the broad DPO unknown-minus-known direction, especially at source layer 24 and adjacent layers. This reinforces the live causal readout: the useful lead is probably a distributed known/unknown subspace, not a clean layer-local SAE feature.
- evidence:
  - `experiment/phase1/probe/phase3_direction_geometry.py`
  - `experiment/phase1/probe/tests/test_phase3_direction_geometry.py`
  - `experiment/phase1/probe/config/phase3_selfaware_direction_geometry.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_direction_geometry_all_delta_layers.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_direction_geometry/summary.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_direction_geometry_all_delta_layers/summary.json`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_direction_geometry.py -q`
  - `python -m py_compile experiment\phase1\probe\phase3_direction_geometry.py`
  - `python experiment\phase1\probe\phase3_direction_geometry.py --config experiment\phase1\probe\config\phase3_selfaware_direction_geometry.yaml`
  - `python experiment\phase1\probe\phase3_direction_geometry.py --config experiment\phase1\probe\config\phase3_selfaware_direction_geometry_all_delta_layers.yaml`
- decisions:
  - Treat geometry output as `DIRECTION_GEOMETRY_ANALYSIS_ONLY`: useful triage, not causal evidence.
  - Prioritize subspace diagnostics over one-feature claims because the best composite aligns with broad known/unknown deltas and with adjacent layers.
  - Keep DPO contrast composite as the strongest current SAE-derived lead; do not over-interpret the unknown-only pair.
- next steps:
  - Run a broader subspace/control panel: broad DPO unknown-minus-known direction, SAE unknown-minus-known composite, PCA/logistic probe direction if available, random matched-norm, wrong-layer and sign controls on the same row panel.
  - Consider activation patching or path-level attribution only after the subspace panel identifies a stable behavioral intervention.
  - Add row-specific answer/refusal target slices once clean single-token aliases or sequence-probability diagnostics are available.
- signals:
  - narrow geometry map: `18` directions, `153` pairwise comparisons.
  - all-delta-layer geometry map: `298` directions, `44253` pairwise comparisons.
  - DPO contrast composite vs broad DPO unknown-minus-known at layer 24: cosine `0.6529`.
  - DPO contrast composite vs broad DPO unknown-minus-known at nearby layers: layer 25 cosine `0.5528`, layer 26 cosine `0.5059`, layer 23 cosine `0.5040`.
  - DPO unknown-pair composite vs broad DPO unknown-minus-known at layer 24: cosine `0.3881`.
  - single DPO unknown-skewed features vs broad DPO unknown-minus-known were weaker: feature 51 cosine `0.3259`, feature 47 cosine `0.2683`; known-skewed features were anti-aligned, feature 64 cosine `-0.5269`, feature 65 cosine `-0.3952`.

### 013-result - Same-Norm Subspace Diagnostic Completed

- at: `2026-06-20T00:20:00Z`
- kind: `result`
- summary: Added a generic direction-transform exporter, normalized broad DPO/KTO known/unknown delta directions to the SAE unknown-minus-known composite norm, and ran a 4-candidate same-scale logit diagnostic. This avoided comparing a norm-15 broad vector against a norm-1.21 SAE composite under the same coefficient grid. The same-norm panel supports the subspace hypothesis: the SAE contrast still produced the strongest signed refusal-opener movement, but wrong-layer controls remained comparable, while the normalized DPO broad direction produced a cleaner but smaller source-layer addition effect. KTO stayed weak at the same norm.
- evidence:
  - `experiment/phase1/probe/phase3_direction_transforms.py`
  - `experiment/phase1/probe/tests/test_phase3_direction_transforms.py`
  - `experiment/phase1/probe/config/phase3_selfaware_dpo_subspace_direction_transforms.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_kto_subspace_direction_transforms.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_transforms/phase3_selfaware_dpo_subspace_normed_to_sae_contrast/direction_transforms.manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_transforms/phase3_selfaware_kto_subspace_normed_to_sae_contrast/direction_transforms.manifest.json`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_subspace_normed_logit_diagnostic/_execution_logs/execution_results.jsonl`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_subspace_normed_logit_diagnostic/summary.csv`
- commands:
  - `python experiment\phase1\probe\phase3_direction_transforms.py --config experiment\phase1\probe\config\phase3_selfaware_dpo_subspace_direction_transforms.yaml`
  - `python experiment\phase1\probe\phase3_direction_transforms.py --config experiment\phase1\probe\config\phase3_selfaware_kto_subspace_direction_transforms.yaml`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_normed_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_normed_logit_diagnostic\summary.csv`
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_direction_transforms.py experiment\phase1\probe\tests\test_phase3_direction_geometry.py experiment\phase1\probe\tests\test_phase3_sae_feature_composites.py -q`
- gotchas:
  - First live attempt failed before model loading because the subspace config declared `contrast: unknown_minus_known` for the SAE composite, but the generated composite manifest row had no `contrast` field. Fixed by propagating optional `contrast` in `phase3_sae_feature_composites.py` and regenerating the local composite manifest. Keep the dry-run validator strict; fix manifests rather than bypassing provenance checks.
  - Use same-norm transforms before comparing broad deltas to SAE-derived directions under a shared coefficient grid. Otherwise vector norm confounds the interpretation.
- decisions:
  - Treat the result as `tier2_exploratory_local` only.
  - Continue describing this as distributed-subspace evidence, not a layer-local sparse feature mechanism.
  - Prefer subspace panels with norm-matched broad/SAE/cross-arm controls before investing in sparse circuit claims.
- next steps:
  - Add a broader row panel with known-retention rows, not only unknown rows, to test whether the subspace moves refusal without damaging known answers.
  - Add row-specific answer/refusal target slices or sequence-probability diagnostics so the panel can distinguish "more I-token" from better calibrated abstention.
  - If same-norm effects persist, test a learned linear probe or PCA direction alongside the SAE composite and broad mean-difference directions.
- signals:
  - live jobs completed: `4/4`; aggregate rows: `64`.
  - all normalized direction norms: about `1.21428`.
  - SAE contrast coefficient-50 activation subtraction: refusal-opener probability delta mean `+0.133768`, top-1 changed rate `62.5%`.
  - SAE contrast coefficient-50 activation addition: refusal-opener probability delta mean `-0.119050`, top-1 changed rate `25.0%`.
  - SAE contrast coefficient-50 wrong-layer subtraction offset `-1`: refusal-opener probability delta mean `+0.149519`, top-1 changed rate `62.5%`.
  - DPO broad layer-24 normalized coefficient-50 activation addition: refusal-opener probability delta mean `+0.093366`, top-1 changed rate `37.5%`.
  - DPO broad layer-25 normalized coefficient-50 activation addition: refusal-opener probability delta mean `+0.081517`, top-1 changed rate `25.0%`.
  - KTO broad layer-25 normalized coefficient-50 activation addition: refusal-opener probability delta mean `+0.043184`, top-1 changed rate `0.0%`.
  - Row-level top-1 changes were concentrated on unknown rows in this 8-row panel.

### 014-result - Known-Retention Subspace Panel Completed

- at: `2026-06-20T00:25:00Z`
- kind: `result`
- summary: Added sweep-level runner overrides and ran the same-norm subspace panel on a deterministic stable known-correct row slice. This tested whether the same candidate directions that move refusal-openers on unknown rows also damage known-answer behavior. The arm-native panel kept DPO/SAE known-row refusal-opener baseline almost zero, while KTO's arm-native runtime had a much higher known-row refusal-opener baseline. This difference traced to live runtime semantics: when `runtime_model.adapter_path` is null, the runner falls back to the candidate extraction manifest adapter, so DPO candidates run with the DPO adapter and KTO candidates run with the KTO adapter.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_sweep.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_sweep.py`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_subspace_known_retention_logit_diagnostic/summary.csv`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py -q`
  - `python -m py_compile experiment\phase1\probe\phase3_causal_pilot_sweep.py`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_known_retention_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_known_retention_logit_diagnostic\summary.csv`
- gotchas:
  - `model.model_name` is descriptive metadata for these configs; the live generator uses `runtime_model` plus candidate extraction-manifest fallbacks. If `runtime_model.adapter_path` is null and extraction fallback is enabled, each candidate runs in its own arm-native adapter runtime.
  - Arm-native DPO/KTO baseline differences are real runtime differences, not necessarily direction effects. Label these panels as arm-native unless `runtime_model` pins or disables the adapter explicitly.
- decisions:
  - Keep `runner_overrides` as generic sweep infrastructure for row slices and runtime overrides.
  - Treat the KTO known-row baseline as an arm-native adapter signal, not as evidence that the KTO direction alone raises known-row refusal.
  - Add an explicit SFT-runtime adapterless panel before comparing DPO/KTO directions inside the same model.
- next steps:
  - Run the unknown and known-retention panels in the pure SFT merged runtime with extraction adapter fallback disabled.
  - Use exact runtime labels in future summaries: arm-native adapter, pinned adapter, or adapterless SFT runtime.
- signals:
  - arm-native known rows, DPO/SAE baseline refusal-opener probability mean: about `0.000054`.
  - arm-native known rows, KTO baseline refusal-opener probability mean: about `0.053762`.
  - arm-native known rows, SAE contrast coefficient-50 activation addition: refusal-opener delta mean `+0.000377`, top-1 changed rate `25.0%`.
  - arm-native known rows, DPO broad layer-24 coefficient-50 activation addition: refusal-opener delta mean `+0.002482`, top-1 changed rate `25.0%`.
  - arm-native known rows, KTO broad layer-25 coefficient-50 activation addition: refusal-opener delta mean `+0.047058`, top-1 changed rate `0.0%`.

### 015-result - Adapterless SFT Runtime Subspace Panels Completed

- at: `2026-06-20T00:40:00Z`
- kind: `result`
- summary: Added an explicit adapterless live-runtime path and ran both unknown-row and known-retention same-norm subspace panels inside the pure SFT merged model. This provides a same-runtime comparison for DPO/KTO/SAE directions, separate from the arm-native adapter panels. In SFT runtime, unknown rows already had high refusal-opener probability, so directions mostly moved probability mass without top-1 changes. Known rows had lower but nontrivial refusal-opener baseline, and broad KTO/DPO directions could raise that slice, while the SAE DPO contrast barely moved known-row refusal at source layer.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic/summary.csv`
  - `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic/summary.csv`
- commands:
  - `python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py -q`
  - `python -m py_compile experiment\phase1\probe\phase3_causal_pilot_runner.py experiment\phase1\probe\phase3_causal_pilot_sweep.py`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic\summary.csv`
  - `python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config experiment\phase1\probe\config\phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic\summary.csv`
- gotchas:
  - Adapterless runtime is now explicit and fail-closed: set `runtime_model.use_extraction_adapter: false` and `runtime_model.allow_adapterless: true`. Without those flags, the runner keeps using candidate extraction adapters by default.
  - `model.model_name` and `runtime_model.model_name` can both appear in materialized configs. Interpret runtime from `runtime_model`; `model` remains descriptive/spec metadata.
- decisions:
  - Separate future claims into arm-native adapter effects versus same-runtime direction effects.
  - Treat current SFT-runtime effects as probability-slice steering only; top-1 did not move on the unknown panel and known-row top-1 movement was minimal.
  - Do not call the SAE contrast a clean knob: wrong-layer controls remain substantial on unknown rows even in SFT runtime.
- next steps:
  - Add row-specific answer-token target slices or sequence-probability targets, because refusal-opener probability alone can miss answer degradation.
  - Consider a small learned linear probe/PCA direction as a same-runtime subspace comparator.
  - Scale the most informative panels to more rows after target slices are less proxy-like.
- signals:
  - SFT-runtime unknown-row baseline refusal-opener probability mean: `0.607347`.
  - SFT-runtime unknown rows, SAE contrast coefficient-50 activation subtraction: refusal-opener delta mean `+0.051214`, top-1 changed `0.0%`.
  - SFT-runtime unknown rows, SAE contrast coefficient-50 activation addition: refusal-opener delta mean `-0.066321`, top-1 changed `0.0%`.
  - SFT-runtime unknown rows, SAE contrast coefficient-50 wrong-layer offset `-1`: refusal-opener delta mean `-0.097313`, top-1 changed `0.0%`.
  - SFT-runtime unknown rows, broad DPO layer-24 coefficient-50 activation addition: refusal-opener delta mean `+0.041172`, top-1 changed `0.0%`.
  - SFT-runtime known-row baseline refusal-opener probability mean: `0.094628`.
  - SFT-runtime known rows, SAE contrast coefficient-50 activation addition: refusal-opener delta mean `+0.002875`, top-1 changed `0.0%`.
  - SFT-runtime known rows, broad DPO layer-24 coefficient-50 activation addition: refusal-opener delta mean `+0.062745`, top-1 changed `0.0%`.
  - SFT-runtime known rows, broad KTO layer-25 coefficient-50 activation addition: refusal-opener delta mean `+0.113123`, top-1 changed `12.5%`.
