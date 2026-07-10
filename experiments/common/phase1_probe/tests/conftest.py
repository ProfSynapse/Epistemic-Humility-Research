"""Test import aliases for the migrated Phase 1 probe/mechinterp layout."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PHASE1_PROBE = ROOT / "experiments/common/phase1_probe"
MECHINTERP = ROOT / "experiments/common/mechinterp"
COMMON_READOUTS = ROOT / "experiments/common/readouts"
DOUBT_REGULATED = ROOT / "experiments/doubt-regulated-caution"
SELFAWARE_CONTROLS = ROOT / "experiments/selfaware-latent-knowledge-controls"

for path in (
    PHASE1_PROBE,
    MECHINTERP,
    COMMON_READOUTS,
    DOUBT_REGULATED,
    SELFAWARE_CONTROLS,
    ROOT / "experiment/phase1/eval",
):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)


ALIASES = {
    "phase3_behavior_axis_scan": "behavior_axis_scan",
    "phase3_behavior_axis_directions": "behavior_axis_directions",
    "phase3_behavior_panel_row_keys": "behavior_panel_row_keys",
    "phase3_calibrated_expression_plane": "calibrated_expression_plane",
    "phase3_causal_pilot_aggregate": "causal_pilot_aggregate",
    "phase3_causal_pilot_dry_run": "causal_pilot_dry_run",
    "phase3_causal_pilot_runner": "causal_pilot_runner",
    "phase3_causal_pilot_sweep": "causal_pilot_sweep",
    "phase3_direction_geometry": "direction_geometry",
    "phase3_direction_transforms": "direction_transforms",
    "phase3_generation_replay_analysis": "generation_replay_analysis",
    "phase3_gold_behavior_panel": "gold_behavior_panel",
    "phase3_head_axis_geometry": "head_axis_geometry",
    "phase3_head_intervention": "head_intervention",
    "phase3_head_intervention_runner": "head_intervention_runner",
    "phase3_head_intervention_sign_curve": "head_intervention_sign_curve",
    "phase3_head_localization_scan": "head_localization_scan",
    "phase3_head_read_projection": "head_read_projection",
    "phase3_head_read_sign_consistency": "head_read_sign_consistency",
    "phase3_head_read_trajectory": "head_read_trajectory",
    "phase3_head_steering_directions": "head_steering_directions",
    "phase3_knowledge_boundary_steer_readout": "knowledge_boundary_steer_readout",
    "phase3_logit_cell_analysis": "logit_cell_analysis",
    "phase3_logit_cell_sign_score": "logit_cell_sign_score",
    "phase3_multicell_readout": "multicell_readout",
    "phase3_probe_smoke_stratified_row_manifest": "probe_smoke_stratified_row_manifest",
    "phase3_residual_caution_direction": "residual_caution_direction",
    "phase3_residual_intervention": "residual_intervention",
    "phase3_residual_intervention_runner": "residual_intervention_runner",
    "phase3_residual_read_trajectory": "residual_read_trajectory",
    "phase3_sae_behavior_feature_analysis": "sae_behavior_feature_analysis",
    "phase3_sae_feature_analysis": "sae_feature_analysis",
    "phase3_sae_feature_composites": "sae_feature_composites",
    "phase3_sae_feature_directions": "sae_feature_directions",
    "phase3_sae_smoke": "sae_smoke",
    "phase3_sae_train": "sae_train",
    "phase3_selfaware_behavior_manifest": "selfaware_behavior_manifest",
    "phase3_selfaware_stratified_row_manifest": "selfaware_stratified_row_manifest",
    "phase3_sycophancy_answer_row_manifest": "sycophancy_answer_row_manifest",
    "phase3_sycophancy_generation_analysis": "sycophancy_generation_analysis",
    "phase3_targeted_row_keys": "targeted_row_keys",
    "phase3_xdataset_behavior_from_generation": "xdataset_behavior_from_generation",
    "phase3_xdataset_build_panel": "xdataset_build_panel",
    "phase3_ac_doubt_coupled_analysis": "phase3_ac_doubt_coupled_analysis",
    "phase3_caution_axis_transfer": "phase3_caution_axis_transfer",
    "phase3_latent_knowledge_controls": "phase3_latent_knowledge_controls",
    "phase3_latent_knowledge_probe": "phase3_latent_knowledge_probe",
}

for old_name, new_name in ALIASES.items():
    sys.modules[old_name] = importlib.import_module(new_name)
