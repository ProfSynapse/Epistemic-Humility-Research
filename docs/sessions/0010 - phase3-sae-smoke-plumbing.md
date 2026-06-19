---
schema_version: research-session/v1
session_id: phase3-sae-smoke-plumbing
title: Phase 3 SAE Smoke Plumbing
status: active
created_at: '2026-06-19T19:52:17Z'
updated_at: '2026-06-19T22:55:00Z'
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
