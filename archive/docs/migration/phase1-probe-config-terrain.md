# Phase 1 Probe Config Terrain

Generated inventory for the tracked legacy config surface under `experiment/phase1/probe/config/`.

## Summary

- Total tracked config files: **251**
- Files with internal config references: **94**
- Files referenced by other tracked text/code: **212**
- Parse errors: **0**

### By Migration Class

| class | count | meaning |
|---|---:|---|
| `P2-has-config-graph-dependencies` | 84 | Part of internal config graph; move as a connected component. |
| `P3-archive-candidate-after-owner-review` | 79 | Likely historical standalone config; archive only after owner review. |
| `P1-has-live-code-skill-test-reference` | 67 | Referenced by live code, tests, or skills; needs targeted rewrite and tests. |
| `P2-move-only-with-owning-config-family` | 15 | Generated row/panel artifact; keep with owning config family. |
| `P0-keep-until-code-defaults-migrate` | 3 | Live default entrypoints; move only with code/test/skill default updates. |
| `P1-migrate-with-runner-template-and-skills` | 3 | Runner templates; move with runner docs and skill command updates. |

### By Category

| category | count |
|---|---:|
| `phase3-legacy-config` | 34 |
| `logit-diagnostic-config` | 33 |
| `logit-sweep-config` | 33 |
| `direction-build-config` | 32 |
| `generation-replay-config` | 24 |
| `runner-config` | 20 |
| `hidden-state-extraction-config` | 17 |
| `generated-row-panel-artifact` | 15 |
| `logit-candidate-config` | 13 |
| `axis-scan-config` | 12 |
| `wrapper-config` | 6 |
| `sae-config` | 5 |
| `live-default-entrypoint` | 3 |
| `legacy-runner-template` | 3 |
| `causal-pilot-runner-config` | 1 |

### By Theme

| theme | count |
|---|---:|
| `selfaware` | 87 |
| `current-clean-grpo-v2` | 67 |
| `gold-kto` | 23 |
| `gold-kto-targeted` | 16 |
| `uncategorized` | 13 |
| `sycophancy-answer` | 9 |
| `current-clean-kto` | 7 |
| `causal-pilot` | 5 |
| `gold-answer` | 5 |
| `current-clean-dpo-grpo` | 4 |
| `current-clean-grpo-dpo` | 4 |
| `current-clean-kto-grpo` | 4 |
| `ac-doubt` | 3 |
| `kuq` | 2 |
| `phase1-probe` | 2 |

## P0/P1 Entry Points

- `experiment/phase1/probe/config/hidden_state_probe.yaml` - live-default-entrypoint; refs=24; internal_deps=2
  Referenced by: `.agents/skills/experiment-runner/SKILL.md`, `.agents/skills/experiment-runner/reference/hidden-state-probe-smoke.md`, `.agents/skills/experiment-runner/scripts/prepare_extraction_cell.py`, `.agents/skills/experiment-runner/tests/test_extraction_gate.py`, `.agents/skills/experiment-runner/tests/test_prepare_extraction_cell.py`, `.claude/skills/experiment-runner/SKILL.md` ...
- `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml` - live-default-entrypoint; refs=12; internal_deps=2
  Referenced by: `.agents/skills/experiment-runner/SKILL.md`, `.agents/skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`, `.agents/skills/mech-interp-runner/references/sweep-workflow.md`, `.claude/skills/experiment-runner/SKILL.md`, `.claude/skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`, `.claude/skills/mech-interp-runner/references/sweep-workflow.md` ...
- `experiment/phase1/probe/config/probe.yaml` - live-default-entrypoint; refs=29; internal_deps=1
  Referenced by: `.agents/skills/experiment-runner/SKILL.md`, `.agents/skills/experiment-runner/reference/hidden-state-probe-smoke.md`, `.agents/skills/experiment-runner/scripts/prepare_extraction_cell.py`, `.agents/skills/experiment-runner/tests/test_extraction_gate.py`, `.agents/skills/experiment-runner/tests/test_prepare_extraction_cell.py`, `.claude/skills/experiment-runner/SKILL.md` ...
- `experiment/phase1/probe/config/hidden_state_kuq_manifest_clean_sft_grpo_v2_seed1_full.yaml` - hidden-state-extraction-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/cross-dataset-transfer.md`, `.claude/skills/mech-interp-runner/references/cross-dataset-transfer.md`, `.skills/mech-interp-runner/references/cross-dataset-transfer.md`, `experiment/phase1/probe/tests/test_hidden_state_probe.py`
- `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched.yaml` - hidden-state-extraction-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched_attention_head.yaml`
- `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml` - hidden-state-extraction-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260619T101926Z-phase-3-selfaware-stratified-row-manifest.md`, `experiment/phase1/probe/tests/test_hidden_state_probe.py`
- `experiment/phase1/probe/config/hidden_state_sycophancy_answer_kto_seed1.yaml` - hidden-state-extraction-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T145500Z-sycophancy-helpfulness-probe.md`, `experiment/phase1/probe/tests/test_phase3_sycophancy_answer_row_manifest.py`
- `experiment/phase1/probe/config/hidden_state_sycophancy_answer_sft_seed1.yaml` - hidden-state-extraction-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T145500Z-sycophancy-helpfulness-probe.md`, `experiment/phase1/probe/tests/test_phase3_sycophancy_answer_row_manifest.py`
- `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention.yaml` - runner-config; refs=13; internal_deps=0
  Referenced by: `experiment/phase1/probe/amendment_af_base_pregen_extract.py`, `experiment/phase1/probe/amendment_af_generate.py`, `experiment/phase1/probe/amendment_ag_generate.py`, `experiment/phase1/probe/amendment_ag_neutral_control.py`, `experiment/phase1/probe/amendment_ag_primed_extract.py`, `experiment/phase1/probe/amendment_ah_main_generate.py` ...
- `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention_smoke.yaml` - runner-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention_smoke_batched.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_scan.yaml` - axis-scan-config; refs=6; internal_deps=0
  Referenced by: `archive/notes/experiments/mech-interp-model-variation-panel.md`, `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_directions.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_protect_directions.yaml`, `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_normed_directions.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_caution_residual_read_trajectory.yaml` - runner-config; refs=3; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/read-trajectory-timing.md`, `.claude/skills/mech-interp-runner/references/read-trajectory-timing.md`, `.skills/mech-interp-runner/references/read-trajectory-timing.md`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_candidates.yaml` - phase3-legacy-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_generation.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_candidates.yaml` - phase3-legacy-config; refs=5; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_generation.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_shifted_layer_candidates.yaml` - phase3-legacy-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_shifted_layer_generation_control.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_candidates.yaml` - phase3-legacy-config; refs=5; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_a_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_b_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_c_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_d_generation.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_candidates.yaml` - phase3-legacy-config; refs=4; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_d_coeff_placement_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_c_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_d_generation.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_candidates.yaml` - phase3-legacy-config; refs=3; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_panel_a_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_panel_b_generation.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_multi_protect_scan.yaml` - phase3-legacy-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_multi_protect_directions.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_behavior_axis_scan.yaml` - axis-scan-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_directions.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_candidates.yaml` - logit-candidate-config; refs=2; internal_deps=1
  Referenced by: `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_l16_generation_replay.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan.yaml` - axis-scan-config; refs=3; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_directions.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_multicell_directions.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_candidates.yaml` - phase3-legacy-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_candidates.yaml` - logit-candidate-config; refs=4; internal_deps=1
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_generation_replay.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_logit_diagnostic.yaml` - logit-diagnostic-config; refs=20; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_generation.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`, `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep.yaml` ...
- `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan.yaml` - axis-scan-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_directions.yaml`
- `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_candidates.yaml` - runner-config; refs=2; internal_deps=1
  Referenced by: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_generation_replay.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_behavior_panel.yaml` - phase3-legacy-config; refs=3; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`
- `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_scan.yaml` - axis-scan-config; refs=2; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_directions.yaml`, `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_axis_directions.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_multicell_readout.yaml` - phase3-legacy-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_axis_scan.yaml` - axis-scan-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_axis_directions.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_logit_candidates.yaml` - logit-candidate-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_targeted_candidates.yaml` - phase3-legacy-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_gold_kto_targeted_baseline_generation_replay.yaml`
- `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.yaml` - phase3-legacy-config; refs=5; internal_deps=3
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/hidden_state_gold_kto_targeted_rare_cells.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml` - direction-build-config; refs=4; internal_deps=1
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_directions.yaml` - direction-build-config; refs=2; internal_deps=1
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml` - logit-diagnostic-config; refs=3; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml` - axis-scan-config; refs=7; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `archive/notes/experiments/mech-interp-model-variation-panel.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml` ...
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_scan.yaml` - axis-scan-config; refs=4; internal_deps=0
  Referenced by: `archive/notes/experiments/mech-interp-model-variation-panel.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_directions.yaml`, `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_hlora_window_directions.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_candidates.yaml` - logit-candidate-config; refs=2; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay.yaml`, `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_candidates.yaml` - logit-candidate-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml` - logit-diagnostic-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_candidates.yaml` - logit-candidate-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_plane.yaml` - phase3-legacy-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic.yaml` - logit-diagnostic-config; refs=6; internal_deps=0
  Referenced by: `docs/sessions/20260619T101926Z-phase-3-selfaware-stratified-row-manifest.md`, `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1.yaml` - logit-diagnostic-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2.yaml` - logit-diagnostic-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1.yaml` - logit-diagnostic-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2.yaml` - logit-diagnostic-config; refs=1; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_kto_cell_sign_score.yaml` - phase3-legacy-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/behavior-axis-path.md`, `.claude/skills/mech-interp-runner/references/behavior-axis-path.md`, `.skills/mech-interp-runner/references/behavior-axis-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_analysis.yaml` - sae-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/sae-path.md`, `.claude/skills/mech-interp-runner/references/sae-path.md`, `.skills/mech-interp-runner/references/sae-path.md`, `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`
- `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`, `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml` - sae-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/sae-path.md`, `.claude/skills/mech-interp-runner/references/sae-path.md`, `.skills/mech-interp-runner/references/sae-path.md`, `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`
- `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`, `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`, `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic.yaml` - logit-diagnostic-config; refs=2; internal_deps=0
  Referenced by: `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`, `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml` - sae-config; refs=4; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/sae-path.md`, `.claude/skills/mech-interp-runner/references/sae-path.md`, `.skills/mech-interp-runner/references/sae-path.md`, `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`
- `experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml` - sae-config; refs=5; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/sae-path.md`, `.claude/skills/mech-interp-runner/references/sae-path.md`, `.skills/mech-interp-runner/references/sae-path.md`, `archive/notes/experiments/mech-interp-model-variation-panel.md`, `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`
- `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic.yaml` - logit-diagnostic-config; refs=5; internal_deps=0
  Referenced by: `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`, `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic_sweep.yaml`
- `experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_scan.yaml` - axis-scan-config; refs=5; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/sycophancy-probe-path.md`, `.claude/skills/mech-interp-runner/references/sycophancy-probe-path.md`, `.skills/mech-interp-runner/references/sycophancy-probe-path.md`, `docs/sessions/20260620T145500Z-sycophancy-helpfulness-probe.md`, `experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_directions.yaml`
- `experiment/phase1/probe/config/phase3_sycophancy_answer_logit_candidates.yaml` - logit-candidate-config; refs=2; internal_deps=0
  Referenced by: `experiment/phase1/probe/config/phase3_sycophancy_answer_kto_wrong_hint_generation_replay.yaml`, `experiment/phase1/probe/config/phase3_sycophancy_answer_logit_sweep.yaml`
- `experiment/phase1/probe/config/phase3_xdataset_kuq_baseline_generation.yaml` - generation-replay-config; refs=3; internal_deps=0
  Referenced by: `.agents/skills/mech-interp-runner/references/cross-dataset-transfer.md`, `.claude/skills/mech-interp-runner/references/cross-dataset-transfer.md`, `.skills/mech-interp-runner/references/cross-dataset-transfer.md`
- `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml` - legacy-runner-template; refs=12; internal_deps=0
  Referenced by: `.agents/skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`, `.claude/skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`, `.skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`, `docs/sessions/20260618T200945Z-phase3-causal-pilot-start.md`, `experiment/phase1/probe/README.md`, `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml` ...
- `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml` - legacy-runner-template; refs=24; internal_deps=0
  Referenced by: `docs/plans/phase3-causal-pilot-smoke-results.md`, `docs/sessions/20260618T200945Z-phase3-causal-pilot-start.md`, `experiment/phase1/probe/README.md`, `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml`, `experiment/phase1/probe/config/phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml`, `experiment/phase1/probe/config/phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml` ...
- `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml` - legacy-runner-template; refs=7; internal_deps=1
  Referenced by: `docs/plans/phase3-causal-pilot-readiness.md`, `docs/plans/phase3-hidden-state-diagnostic-summary.md`, `docs/plans/phase3-interpretability-research-process.md`, `docs/sessions/20260618T192924Z-phase1-writeup-and-mech-interp-start.md`, `docs/sessions/20260618T200945Z-phase3-causal-pilot-start.md`, `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml` ...

## Internal Dependency Components

Connected components are built from config-to-config references only. Move these as units if they leave the legacy tree.

- Components with more than one file: **26**

| component | size | dominant theme | dominant category | migration pressure | suggested destination |
|---|---:|---|---|---|---|
| `C001` | 43 | `selfaware` | `logit-sweep-config` | `P2-has-config-graph-dependencies` | keep in place until legacy runner defaults move |
| `C005` | 31 | `current-clean-grpo-v2` | `generation-replay-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C008` | 10 | `current-clean-grpo-v2` | `generation-replay-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C020` | 10 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C002` | 5 | `uncategorized` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C025` | 5 | `selfaware` | `logit-sweep-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C012` | 4 | `current-clean-kto` | `runner-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C009` | 3 | `current-clean-grpo-v2` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C013` | 3 | `gold-kto` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C015` | 3 | `selfaware` | `direction-build-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C016` | 3 | `selfaware` | `logit-sweep-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C019` | 3 | `selfaware` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C003` | 2 | `current-clean-dpo-grpo` | `phase3-legacy-config` | `P2-has-config-graph-dependencies` | archive/experiment/phase1/probe/config/current-clean-dpo-grpo/ or owning experiments/<slug>/artifacts/configs/ after owner review |
| `C004` | 2 | `current-clean-grpo-dpo` | `phase3-legacy-config` | `P2-has-config-graph-dependencies` | archive/experiment/phase1/probe/config/current-clean-grpo-dpo/ or owning experiments/<slug>/artifacts/configs/ after owner review |
| `C006` | 2 | `current-clean-grpo-v2` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C007` | 2 | `current-clean-grpo-v2` | `axis-scan-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C010` | 2 | `current-clean-kto-grpo` | `phase3-legacy-config` | `P2-has-config-graph-dependencies` | archive/experiment/phase1/probe/config/current-clean-kto-grpo/ or owning experiments/<slug>/artifacts/configs/ after owner review |
| `C011` | 2 | `current-clean-kto` | `axis-scan-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C014` | 2 | `gold-kto-targeted` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |
| `C017` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C018` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C021` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C022` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C023` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C024` | 2 | `selfaware` | `logit-diagnostic-config` | `P1-has-live-code-skill-test-reference` | migrate with code/skills/tests that reference the component |
| `C026` | 2 | `sycophancy-answer` | `direction-build-config` | `P2-has-config-graph-dependencies` | migrate with code/skills/tests that reference the component |

### Largest Components

- `C001` (43 files): themes={'selfaware': 12, 'gold-kto-targeted': 9, 'gold-kto': 9, 'gold-answer': 5, 'sycophancy-answer': 5, 'causal-pilot': 3}; classes={'P2-has-config-graph-dependencies': 21, 'P1-has-live-code-skill-test-reference': 13, 'P2-move-only-with-owning-config-family': 6, 'P1-migrate-with-runner-template-and-skills': 2, 'P0-keep-until-code-defaults-migrate': 1}
  - `experiment/phase1/probe/config/hidden_state_gold_kto_targeted_rare_cells.yaml`
  - `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`
  - `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_gold_answer_kto_random_seed_panel.yaml`
  - `experiment/phase1/probe/config/phase3_gold_answer_kto_unknown_generation_replay.yaml`
  - `experiment/phase1/probe/config/phase3_gold_answer_unknown_coeff_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_gold_kto_baseline_generation_replay.yaml`
  - ... 33 more
- `C005` (31 files): themes={'current-clean-grpo-v2': 28, 'uncategorized': 3}; classes={'P2-has-config-graph-dependencies': 20, 'P1-has-live-code-skill-test-reference': 7, 'P2-move-only-with-owning-config-family': 4}
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_generation.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_generation.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_generation.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.txt`
  - ... 21 more
- `C008` (10 files): themes={'current-clean-grpo-v2': 10}; classes={'P2-has-config-graph-dependencies': 6, 'P1-has-live-code-skill-test-reference': 3, 'P2-move-only-with-owning-config-family': 1}
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_l16_generation_replay.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_generation_replay.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_row_keys.txt`
- `C020` (10 files): themes={'selfaware': 10}; classes={'P1-has-live-code-skill-test-reference': 5, 'P2-has-config-graph-dependencies': 5}
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2_sweep.yaml`
- `C002` (5 files): themes={'uncategorized': 3, 'current-clean-grpo-v2': 2}; classes={'P2-has-config-graph-dependencies': 4, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_directions.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_scan.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_protect_directions.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_normed_directions.yaml`
- `C025` (5 files): themes={'selfaware': 5}; classes={'P2-has-config-graph-dependencies': 4, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic_sweep.yaml`
- `C012` (4 files): themes={'current-clean-kto': 4}; classes={'P2-has-config-graph-dependencies': 2, 'P1-has-live-code-skill-test-reference': 1, 'P2-move-only-with-owning-config-family': 1}
  - `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_generation_replay.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_selfaware_manifest.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_selfaware_row_keys.txt`
- `C009` (3 files): themes={'current-clean-grpo-v2': 3}; classes={'P2-has-config-graph-dependencies': 2, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_directions.yaml`
  - `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_multicell_directions.yaml`
- `C013` (3 files): themes={'gold-kto': 3}; classes={'P2-has-config-graph-dependencies': 2, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_directions.yaml`
  - `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_scan.yaml`
  - `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_axis_directions.yaml`
- `C015` (3 files): themes={'selfaware': 3}; classes={'P1-has-live-code-skill-test-reference': 3}
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_directions.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml`
- `C016` (3 files): themes={'selfaware': 3}; classes={'P2-has-config-graph-dependencies': 2, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic_sweep.yaml`
- `C019` (3 files): themes={'selfaware': 3}; classes={'P2-has-config-graph-dependencies': 2, 'P1-has-live-code-skill-test-reference': 1}
  - `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_directions.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_scan.yaml`
  - `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_hlora_window_directions.yaml`


## Config Graph Hotspots

These files are referenced by other configs and should not be moved alone.

| config | incoming config refs | category | theme |
|---|---:|---|---|
| `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml` | 21 | `legacy-runner-template` | `causal-pilot` |
| `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_logit_diagnostic.yaml` | 19 | `logit-diagnostic-config` | `uncategorized` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_row_keys.txt` | 9 | `generated-row-panel-artifact` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml` | 7 | `legacy-runner-template` | `causal-pilot` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_panel_b_row_keys.txt` | 5 | `generated-row-panel-artifact` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_64_row_keys.txt` | 5 | `generated-row-panel-artifact` | `selfaware` |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic.yaml` | 5 | `logit-diagnostic-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_scan.yaml` | 4 | `axis-scan-config` | `uncategorized` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_candidates.yaml` | 4 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.txt` | 4 | `generated-row-panel-artifact` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_candidates.yaml` | 4 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic.yaml` | 4 | `logit-diagnostic-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_panel_c_row_keys.txt` | 3 | `generated-row-panel-artifact` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_candidates.yaml` | 3 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_candidates.yaml` | 3 | `logit-candidate-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_row_keys.txt` | 3 | `generated-row-panel-artifact` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.txt` | 3 | `generated-row-panel-artifact` | `gold-kto-targeted` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_candidates.yaml` | 2 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_candidates.yaml` | 2 | `logit-candidate-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | 2 | `axis-scan-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_selfaware_row_keys.txt` | 2 | `generated-row-panel-artifact` | `current-clean-kto` |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_scan.yaml` | 2 | `axis-scan-config` | `gold-kto` |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml` | 2 | `logit-diagnostic-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml` | 2 | `axis-scan-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_scan.yaml` | 2 | `axis-scan-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_candidates.yaml` | 2 | `logit-candidate-config` | `selfaware` |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_logit_candidates.yaml` | 2 | `logit-candidate-config` | `sycophancy-answer` |
| `experiment/phase1/probe/config/hidden_state_probe.yaml` | 1 | `live-default-entrypoint` | `phase1-probe` |
| `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml` | 1 | `legacy-runner-template` | `causal-pilot` |
| `experiment/phase1/probe/config/phase3_current_clean_dpo_grpo_unknown_failure_selfaware_row_keys.txt` | 1 | `generated-row-panel-artifact` | `current-clean-dpo-grpo` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_dpo_unknown_failure_selfaware_row_keys.txt` | 1 | `generated-row-panel-artifact` | `current-clean-grpo-dpo` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_candidates.yaml` | 1 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_shifted_layer_candidates.yaml` | 1 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_multi_protect_scan.yaml` | 1 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_behavior_axis_scan.yaml` | 1 | `axis-scan-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_candidates.yaml` | 1 | `phase3-legacy-config` | `current-clean-grpo-v2` |
| `experiment/phase1/probe/config/phase3_current_clean_kto_grpo_unknown_failure_selfaware_row_keys.txt` | 1 | `generated-row-panel-artifact` | `current-clean-kto-grpo` |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | 1 | `axis-scan-config` | `current-clean-kto` |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_candidates.yaml` | 1 | `runner-config` | `current-clean-kto` |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_logit_candidates.yaml` | 1 | `logit-candidate-config` | `gold-kto` |

## Safe Migration Batches

1. **Do not move live defaults yet.** Keep `probe.yaml`, `hidden_state_probe.yaml`, and `phase3_causal_pilot_local_sweep.yaml` until runner defaults, tests, and skill docs are updated in the same commit.
2. **Move generated row/panel artifacts only with their owning config component.** Examples include `*_row_keys.txt`, `*_rows.jsonl`, `*.manifest.json`, and `*.summary.json`.
3. **Archive unmapped Phase 3 components as connected components.** Use `referenced_by_config_graph` and `internal_config_refs` in the JSON inventory to avoid splitting `runner_config`, `candidate_source_config`, and `source_scan_config` pairs.
4. **Promote only generic future-facing material to `experiments/common/`.** This inventory found no clean generic config template set; most files are path-pinned historical configs.

## Full Inventory

The machine-readable inventory is `docs/migration/phase1-probe-config-terrain.json`.

| path | category | theme | migration class | refs | internal deps | incoming graph refs |
|---|---|---|---|---:|---:|---:|
| `experiment/phase1/probe/config/hidden_state_gold_kto_targeted_rare_cells.yaml` | `hidden-state-extraction-config` | `gold-kto-targeted` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/hidden_state_kuq_manifest_clean_sft_grpo_v2_seed1_full.yaml` | `hidden-state-extraction-config` | `kuq` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_probe.yaml` | `live-default-entrypoint` | `phase1-probe` | `P0-keep-until-code-defaults-migrate` | 24 | 2 | 1 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_dpo_grpo_unknown_failure_panel_prompt_matched.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_dpo_seed1_full.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_dpo_unknown_failure_panel_prompt_matched.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed1_full.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched.yaml` | `hidden-state-extraction-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched_attention_head.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_kto_grpo_unknown_failure_panel_prompt_matched.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_kto_unknown_failure_panel_prompt_matched.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_clean_sft_seed1_full.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1.yaml` | `hidden-state-extraction-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_dpo_seed1_full.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_selfaware_manifest_sft_kto_seed1_full.yaml` | `hidden-state-extraction-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_sycophancy_answer_kto_seed1.yaml` | `hidden-state-extraction-config` | `sycophancy-answer` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/hidden_state_sycophancy_answer_sft_seed1.yaml` | `hidden-state-extraction-config` | `sycophancy-answer` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention.yaml` | `runner-config` | `ac-doubt` | `P1-has-live-code-skill-test-reference` | 13 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention_smoke.yaml` | `runner-config` | `ac-doubt` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_ac_doubt_coupled_intervention_smoke_batched.yaml` | `runner-config` | `ac-doubt` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml` | `causal-pilot-runner-config` | `causal-pilot` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml` | `legacy-runner-template` | `causal-pilot` | `P1-migrate-with-runner-template-and-skills` | 12 | 0 | 7 |
| `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml` | `legacy-runner-template` | `causal-pilot` | `P1-migrate-with-runner-template-and-skills` | 24 | 0 | 21 |
| `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml` | `live-default-entrypoint` | `causal-pilot` | `P0-keep-until-code-defaults-migrate` | 12 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml` | `legacy-runner-template` | `causal-pilot` | `P1-migrate-with-runner-template-and-skills` | 7 | 1 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_directions.yaml` | `direction-build-config` | `uncategorized` | `P2-has-config-graph-dependencies` | 2 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_behavior_axis_scan.yaml` | `axis-scan-config` | `uncategorized` | `P1-has-live-code-skill-test-reference` | 6 | 0 | 4 |
| `experiment/phase1/probe/config/phase3_current_clean_dpo_grpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-dpo-grpo` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_dpo_grpo_unknown_failure_prompt_matched_multicell_readout.yaml` | `phase3-legacy-config` | `current-clean-dpo-grpo` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_dpo_grpo_unknown_failure_selfaware_manifest.yaml` | `phase3-legacy-config` | `current-clean-dpo-grpo` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_dpo_grpo_unknown_failure_selfaware_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-dpo-grpo` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_dpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-grpo-dpo` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_dpo_unknown_failure_prompt_matched_multicell_readout.yaml` | `phase3-legacy-config` | `current-clean-grpo-dpo` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_dpo_unknown_failure_selfaware_manifest.yaml` | `phase3-legacy-config` | `current-clean-grpo-dpo` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_dpo_unknown_failure_selfaware_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-dpo` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_caution_perp_residual_intervention.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_caution_residual_intervention.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_caution_residual_read_trajectory.yaml` | `runner-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_knowledge_boundary_steer.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_generation_replay_96_sweep.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_layer_window_normed_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_multilayer_band_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_coeff_sweep.yaml` | `wrapper-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_coeff_sweep.yaml` | `wrapper-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_l26_panel_b_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 5 | 0 | 4 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_native_layer_window_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-v2` | `P2-move-only-with-owning-config-family` | 5 | 0 | 4 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 6 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_panel_b_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-v2` | `P2-move-only-with-owning-config-family` | 6 | 0 | 5 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_panel_c_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-v2` | `P2-move-only-with-owning-config-family` | 4 | 0 | 3 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_replay_96_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-v2` | `P2-move-only-with-owning-config-family` | 10 | 0 | 9 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_shifted_layer_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_known_overrefusal_shifted_layer_generation_control.yaml` | `wrapper-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 5 | 0 | 4 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_a_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_b_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_c_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_d_coeff_placement_sweep.yaml` | `wrapper-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_panel_d_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 3 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_c_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_double_orthogonalized_shifted_layer_panel_d_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_panel_a_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_orthogonalized_panel_b_generation.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_multi_protect_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_multi_protect_scan.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_orthogonalized_to_unknown_refusal_and_known_wrong.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_l26_repair_protect_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_answer_alias_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_l16_generation_replay.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_candidates.yaml` | `logit-candidate-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 2 | 1 | 2 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_logit_sweep.yaml` | `logit-sweep-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_answer_alias_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_generation_replay.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_intervention_sweep_randomctl_normmatched.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_localization_scan.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_read_trajectory_sft_base.yaml` | `runner-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_head_steering_directions_randomctl.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_candidates.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_generation_replay.yaml` | `generation-replay-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_constrained_unknown_repair.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_l26_multicell_directions.yaml` | `direction-build-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_candidates.yaml` | `logit-candidate-config` | `current-clean-grpo-v2` | `P1-has-live-code-skill-test-reference` | 4 | 1 | 3 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_logit_sweep.yaml` | `logit-sweep-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_prompt_matched_multicell_readout.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.yaml` | `phase3-legacy-config` | `current-clean-grpo-v2` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_grpo_v2_unknown_failure_selfaware_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-grpo-v2` | `P2-move-only-with-owning-config-family` | 4 | 0 | 3 |
| `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_generation_replay_sweep.yaml` | `generation-replay-config` | `uncategorized` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_logit_diagnostic.yaml` | `logit-diagnostic-config` | `uncategorized` | `P1-has-live-code-skill-test-reference` | 20 | 0 | 19 |
| `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `uncategorized` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_known_overrefusal_normed_directions.yaml` | `direction-build-config` | `uncategorized` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_grpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-kto-grpo` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_grpo_unknown_failure_prompt_matched_multicell_readout.yaml` | `phase3-legacy-config` | `current-clean-kto-grpo` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_grpo_unknown_failure_selfaware_manifest.yaml` | `phase3-legacy-config` | `current-clean-kto-grpo` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_grpo_unknown_failure_selfaware_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-kto-grpo` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_behavior_axis_scan.yaml` | `axis-scan-config` | `current-clean-kto` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_candidates.yaml` | `runner-config` | `current-clean-kto` | `P1-has-live-code-skill-test-reference` | 2 | 1 | 1 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_directions.yaml` | `direction-build-config` | `current-clean-kto` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_generation_replay.yaml` | `generation-replay-config` | `current-clean-kto` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_prompt_matched_multicell_readout.yaml` | `phase3-legacy-config` | `current-clean-kto` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_selfaware_manifest.yaml` | `phase3-legacy-config` | `current-clean-kto` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_current_clean_kto_unknown_failure_selfaware_row_keys.txt` | `generated-row-panel-artifact` | `current-clean-kto` | `P2-move-only-with-owning-config-family` | 2 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m1.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m2.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p1.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p2.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `gold-answer` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `gold-answer` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_answer_kto_random_seed_panel.yaml` | `wrapper-config` | `gold-answer` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_answer_kto_unknown_generation_replay.yaml` | `generation-replay-config` | `gold-answer` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_answer_unknown_coeff_sweep.yaml` | `wrapper-config` | `gold-answer` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_baseline_generation_replay.yaml` | `generation-replay-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_behavior_panel.yaml` | `phase3-legacy-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_answer_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_directions.yaml` | `direction-build-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_axis_scan.yaml` | `axis-scan-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_answer_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_directions.yaml` | `direction-build-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_logit_candidates.yaml` | `logit-candidate-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_logit_sweep.yaml` | `logit-sweep-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_composite_refusal_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_logit_candidates.yaml` | `logit-candidate-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_logit_sweep.yaml` | `logit-sweep-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_answer_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_logit_candidates.yaml` | `logit-candidate-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_logit_sweep.yaml` | `logit-sweep-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_multilayer_refusal_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_refusal_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_axis_directions.yaml` | `direction-build-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_answer_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_logit_candidates.yaml` | `logit-candidate-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_logit_sweep.yaml` | `logit-sweep-config` | `gold-kto` | `P2-has-config-graph-dependencies` | 0 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_calibrated_expression_same_layer_single_refusal_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_multicell_readout.yaml` | `phase3-legacy-config` | `gold-kto` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_baseline_generation_replay.yaml` | `generation-replay-config` | `gold-kto-targeted` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_behavior_panel.yaml` | `phase3-legacy-config` | `gold-kto-targeted` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_answer_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto-targeted` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_axis_directions.yaml` | `direction-build-config` | `gold-kto-targeted` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_axis_scan.yaml` | `axis-scan-config` | `gold-kto-targeted` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_logit_candidates.yaml` | `logit-candidate-config` | `gold-kto-targeted` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_logit_sweep.yaml` | `logit-sweep-config` | `gold-kto-targeted` | `P2-has-config-graph-dependencies` | 2 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_calibrated_expression_refusal_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `gold-kto-targeted` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_candidates.yaml` | `phase3-legacy-config` | `gold-kto-targeted` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_cell_sign_score.yaml` | `phase3-legacy-config` | `gold-kto-targeted` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_multicell_readout.yaml` | `phase3-legacy-config` | `gold-kto-targeted` | `P3-archive-candidate-after-owner-review` | 2 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.manifest.json` | `generated-row-panel-artifact` | `gold-kto-targeted` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.txt` | `generated-row-panel-artifact` | `gold-kto-targeted` | `P2-move-only-with-owning-config-family` | 4 | 0 | 3 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_row_keys.yaml` | `phase3-legacy-config` | `gold-kto-targeted` | `P1-has-live-code-skill-test-reference` | 5 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_gold_kto_targeted_rare_cell_rows.jsonl` | `generated-row-panel-artifact` | `gold-kto-targeted` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m1.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m2.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_p1.yaml` | `runner-config` | `uncategorized` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_directions.yaml` | `direction-build-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_directions.yaml` | `direction-build-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_axis_scan.yaml` | `axis-scan-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 7 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_selfaware_behavior_feature_direction_geometry.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_directions.yaml` | `direction-build-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_axis_scan.yaml` | `axis-scan-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_direction_geometry.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_hlora_window_directions.yaml` | `direction-build-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_hlora_window_geometry.yaml` | `phase3-legacy-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_64_row_keys.txt` | `generated-row-panel-artifact` | `selfaware` | `P2-move-only-with-owning-config-family` | 5 | 0 | 5 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay.yaml` | `generation-replay-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_candidates.yaml` | `logit-candidate-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_candidates.yaml` | `logit-candidate-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_logit_candidates.yaml` | `logit-candidate-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 0 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_composite_logit_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 0 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_candidates.yaml` | `logit-candidate-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_logit_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_candidates.yaml` | `logit-candidate-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_cell_analysis.yaml` | `logit-diagnostic-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_calibrated_expression_plane.yaml` | `phase3-legacy-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_direction_geometry.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_direction_geometry_all_delta_layers.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_dpo_subspace_direction_transforms.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 6 | 0 | 5 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg1_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_neg2_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos1_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_full_delta_nearby_logit_diagnostic_offset_pos2_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 2 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_kto_cell_sign_score.yaml` | `phase3-legacy-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_kto_orthogonalized_cell_sign_score.yaml` | `phase3-legacy-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_kto_subspace_direction_transforms.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_analysis.yaml` | `sae-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_behavior_feature_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_analysis.yaml` | `sae-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composite_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_composites.yaml` | `sae-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_directions.yaml` | `direction-build-config` | `selfaware` | `P3-archive-candidate-after-owner-review` | 1 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_f047_nearby_layer_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_feature_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_pilot.yaml` | `sae-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 4 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_sae_smoke.yaml` | `sae-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 5 | 0 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_known_retention_sft_runtime_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic.yaml` | `logit-diagnostic-config` | `selfaware` | `P1-has-live-code-skill-test-reference` | 5 | 0 | 4 |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_selfaware_subspace_normed_sft_runtime_logit_diagnostic_sweep.yaml` | `logit-sweep-config` | `selfaware` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_32_row_keys.txt` | `generated-row-panel-artifact` | `sycophancy-answer` | `P2-move-only-with-owning-config-family` | 1 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_directions.yaml` | `direction-build-config` | `sycophancy-answer` | `P2-has-config-graph-dependencies` | 1 | 1 | 0 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_behavior_axis_scan.yaml` | `axis-scan-config` | `sycophancy-answer` | `P1-has-live-code-skill-test-reference` | 5 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_kto_wrong_hint_followed_row_keys.txt` | `generated-row-panel-artifact` | `sycophancy-answer` | `P2-move-only-with-owning-config-family` | 2 | 0 | 1 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_kto_wrong_hint_generation_replay.yaml` | `generation-replay-config` | `sycophancy-answer` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_logit_candidates.yaml` | `logit-candidate-config` | `sycophancy-answer` | `P1-has-live-code-skill-test-reference` | 2 | 0 | 2 |
| `experiment/phase1/probe/config/phase3_sycophancy_answer_logit_sweep.yaml` | `logit-sweep-config` | `sycophancy-answer` | `P2-has-config-graph-dependencies` | 1 | 3 | 0 |
| `experiment/phase1/probe/config/phase3_xdataset_kuq_baseline_generation.yaml` | `generation-replay-config` | `kuq` | `P1-has-live-code-skill-test-reference` | 3 | 0 | 0 |
| `experiment/phase1/probe/config/probe.yaml` | `live-default-entrypoint` | `phase1-probe` | `P0-keep-until-code-defaults-migrate` | 29 | 1 | 1 |
