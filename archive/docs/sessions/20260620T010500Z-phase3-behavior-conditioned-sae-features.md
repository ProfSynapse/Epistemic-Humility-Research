---
schema_version: research-session/v1
session_id: 20260620T010500Z-phase3-behavior-conditioned-sae-features
title: Phase 3 Behavior-Conditioned SAE Features
status: active
created_at: '2026-06-20T01:05:00Z'
updated_at: '2026-06-20T16:07:00Z'
phase: phase3
question: Can trained SelfAware SAE latents identify epistemic-humility behavior features
  beyond the coarse known/unknown screen?
tags:
- phase3
- mech-interp
- sae
- behavior-features
- causal-smoke
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Phase 3 has top-k16 SAE pilots, known/unknown feature screens,
    geometry maps, and same-norm subspace diagnostics.
  changed_by_session: Adds behavior-conditioned SAE feature ranking, behavior-feature
    direction export, geometry comparison, and a four-candidate logit causal smoke.
checkpoints:
- id: 001-behavior-screen
  at: '2026-06-20T01:05:00Z'
  kind: result
  title: Behavior-Conditioned SAE Feature Screen Completed
  summary: 'Added and ran a behavior-conditioned SAE feature analysis that ranks top-k16
    SAE latents by target-arm behavior groups instead of only known/unknown labels.
    DPO seed1 had enough support for unknown refused vs answered and unknown low-confidence
    vs high-confidence, but no known refused rows. KTO seed1 supported unknown refusal/low-confidence
    screens and a known-refused overrefusal screen.

    '
  evidence:
  - experiment/phase1/probe/phase3_sae_behavior_feature_analysis.py
  - archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_behavior_feature_analysis.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_behavior_feature_analysis/phase3_selfaware_delta_topk16_behavior_features/sft_dpo_selfaware_full_delta_l24_topk16_behavior/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_behavior_feature_analysis/phase3_selfaware_delta_topk16_behavior_features/sft_kto_selfaware_full_delta_l25_topk16_behavior/summary.json
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_phase3_sae_behavior_feature_analysis.py
    -q
  - python -m py_compile experiment\phase1\probe\phase3_sae_behavior_feature_analysis.py
  - python experiment\phase1\probe\phase3_sae_behavior_feature_analysis.py --config
    archive\experiment\phase1\probe\config\selfaware-sae-screens\phase3_selfaware_sae_behavior_feature_analysis.yaml
  decisions:
  - Treat outputs as `SAE_BEHAVIOR_FEATURE_ANALYSIS_ONLY`.
  - Do not call these features monosemantic; top examples show content-family structure.
  signals:
    dpo_unknown_refused_rows: 321
    dpo_unknown_answered_rows: 356
    dpo_top_unknown_refusal_feature: 49
    dpo_top_unknown_refusal_cohen_d: 0.419820122547021
    dpo_top_low_confidence_feature: 49
    dpo_top_low_confidence_cohen_d: 0.44412994496788133
    kto_unknown_refused_rows: 585
    kto_unknown_answered_rows: 92
    kto_top_unknown_refusal_feature: 27
    kto_top_unknown_refusal_cohen_d: 0.4623376081088298
    kto_top_known_overrefusal_feature: 16
    kto_top_known_overrefusal_cohen_d: 1.289762447903884
- id: 002-direction-export-and-geometry
  at: '2026-06-20T01:05:00Z'
  kind: result
  title: Behavior Feature Directions Exported And Mapped
  summary: 'Extended the SAE feature-direction exporter so it can read both known/unknown
    and behavior-conditioned ranking CSVs, with per-candidate explicit feature selection
    and de-duplication across behavior contrasts. Exported six behavior-feature directions
    and mapped them against broad DPO/KTO deltas plus the prior SAE feature/composite
    leads.

    '
  evidence:
  - experiment/phase1/probe/phase3_sae_feature_directions.py
  - archive/experiment/phase1/probe/config/selfaware-sae-screens/phase3_selfaware_sae_behavior_feature_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-geometry-and-subspace/phase3_selfaware_behavior_feature_direction_geometry.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/sae_feature_directions/phase3_selfaware_delta_topk16_behavior_feature_directions/sae_feature_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_behavior_feature_direction_geometry/summary.json
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_phase3_sae_feature_directions.py
    experiment\phase1\probe\tests\test_phase3_sae_behavior_feature_analysis.py -q
  - python experiment\phase1\probe\phase3_sae_feature_directions.py --config archive\experiment\phase1\probe\config\selfaware-sae-screens\phase3_selfaware_sae_behavior_feature_directions.yaml
  - python experiment\phase1\probe\phase3_direction_geometry.py --config archive\experiment\phase1\probe\config\selfaware-geometry-and-subspace\phase3_selfaware_behavior_feature_direction_geometry.yaml
  gotchas:
  - Behavior ranking CSVs can contain the same feature once per contrast; explicit
    direction export must de-duplicate by feature ID or it writes duplicate vectors
    with conflicting metadata.
  decisions:
  - Export DPO features 49, 80, 125 and KTO features 12, 16, 27 as behavior-feature
    direction candidates.
  - Use geometry as triage only; it is `DIRECTION_GEOMETRY_ANALYSIS_ONLY`.
  signals:
    exported_direction_count: 6
    geometry_direction_count: 24
    geometry_pair_count: 276
    kto_f12_to_kto_unknown_minus_known_cosine: 0.368
    dpo_f125_to_dpo_unknown_minus_known_cosine: 0.263
    dpo_f49_to_dpo_unknown_minus_known_cosine: 0.157
    behavior_feature_pairwise_cosines: mostly_near_zero
- id: 003-causal-smoke
  at: '2026-06-20T01:05:00Z'
  kind: result
  title: Behavior Feature Logit Smoke Completed
  summary: 'Added and ran a four-candidate local Docker logit diagnostic over exact
    top-activating rows. DPO f49 showed the largest source-layer effect, but activation
    addition decreased refusal-opener probability while subtraction increased it,
    so the sign is inverted relative to the behavior label. KTO f12 and f16 showed
    smaller sign-consistent effects. DPO f125 was weak and wrong-layer was stronger
    than source. These are candidate axes, not clean epistemic-humility feature knobs.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-sae-feature-logit-diagnostics/phase3_selfaware_sae_behavior_feature_logit_diagnostic.yaml
  - archive/experiment/phase1/probe/config/selfaware-sae-feature-logit-diagnostics/phase3_selfaware_sae_behavior_feature_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_behavior_feature_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_sae_behavior_feature_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-sae-feature-logit-diagnostics\phase3_selfaware_sae_behavior_feature_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-sae-feature-logit-diagnostics\phase3_selfaware_sae_behavior_feature_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_behavior_feature_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_sae_behavior_feature_logit_diagnostic\summary.csv
  gotchas:
  - 'In `readiness_checks.require_extraction_manifest`, omit `label_counts` and the
    runner interprets the expected label-count map as `{}`; specify `known: 556` and
    `unknown: 677` for these SelfAware extraction manifests.

    '
  decisions:
  - Do not promote any behavior feature to a clean feature claim.
  - Treat DPO f49 as an inverted-sign steering lead requiring closer row-level replay.
  - Treat KTO f16 as an overrefusal/damage-axis lead, not a desired humility knob.
  signals:
    dpo_f49_baseline_refusal_probability: 0.439027
    dpo_f49_coef50_addition_delta: -0.206091
    dpo_f49_coef50_subtraction_delta: 0.050063
    dpo_f49_coef50_random_matched_norm_delta: -0.027108
    dpo_f125_baseline_refusal_probability: 0.143036
    dpo_f125_coef50_addition_delta: 0.020782
    dpo_f125_coef50_wrong_layer_delta: 0.066241
    kto_f12_baseline_refusal_probability: 0.491622
    kto_f12_coef50_addition_delta: 0.029567
    kto_f12_coef50_subtraction_delta: -0.047204
    kto_f16_baseline_refusal_probability: 0.580563
    kto_f16_coef50_addition_delta: 0.011517
    kto_f16_coef50_subtraction_delta: -0.058266
    completed_live_jobs: 4
    aggregate_rows: 48
- id: 004-layerwise-behavior-axis-scan
  at: '2026-06-20T09:16:00Z'
  kind: result
  title: Layerwise Behavior Axis Scan Completed
  summary: 'Added and ran a CPU-only layerwise behavior-axis scan across existing
    SelfAware hidden-state extractions. The scan compares behavior-defined row groups
    across `h_base`, `h_lora`, and `delta` roles without loading models. Broad unknown-refused
    vs known-correct separability is very strong across many layers. The subtler within-unknown
    refusal and confidence signals concentrate later, mostly around layers 24-30,
    and appear in both SFT-base activations and adapter deltas.

    '
  evidence:
  - experiment/phase1/probe/phase3_behavior_axis_scan.py
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_scan.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_behavior_axis_scan/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_behavior_axis_scan/top_layers_all.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_behavior_axis_scan/axis_scan_all.csv
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_phase3_behavior_axis_scan.py
    -q
  - python -m py_compile experiment\phase1\probe\phase3_behavior_axis_scan.py
  - python experiment\phase1\probe\phase3_behavior_axis_scan.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_scan.yaml
  gotchas:
  - Current `h_base` for DPO/KTO extractions is the SFT-merged model before the preference
    adapter, not the original Qwen base model.
  - SFT seed1 has no usable unknown-refused vs unknown-answered contrast because it
    refused 677 unknown rows and answered 0; use broad unknown-refused vs known-correct
    and known-refused vs known-correct contrasts for SFT behavior checks.
  decisions:
  - Treat outputs as `BEHAVIOR_AXIS_SCAN_ONLY`.
  - Use layerwise scan results to choose next causal/subspace directions; do not treat
    projection separability as causal evidence.
  signals:
    dpo_unknown_refused_vs_answered_best_delta_layer: 28
    dpo_unknown_refused_vs_answered_best_delta_cohen_d: 1.262
    dpo_unknown_refused_vs_answered_best_delta_auc: 0.812
    dpo_unknown_low_vs_high_confidence_best_delta_layer: 28
    dpo_unknown_low_vs_high_confidence_best_delta_cohen_d: 1.154
    dpo_unknown_refused_vs_known_correct_best_delta_layer: 33
    dpo_unknown_refused_vs_known_correct_best_delta_cohen_d: 5.367
    kto_unknown_refused_vs_answered_best_delta_layer: 25
    kto_unknown_refused_vs_answered_best_delta_cohen_d: 1.424
    kto_unknown_low_vs_high_confidence_best_delta_layer: 25
    kto_unknown_low_vs_high_confidence_best_delta_cohen_d: 1.439
    kto_known_refused_vs_known_correct_best_delta_layer: 22
    kto_known_refused_vs_known_correct_best_delta_cohen_d: 2.525
    sft_unknown_refused_vs_known_correct_best_h_base_layer: 24
    sft_unknown_refused_vs_known_correct_best_h_base_cohen_d: 4.169
    sft_known_refused_vs_known_correct_best_h_base_layer: 27
    sft_known_refused_vs_known_correct_best_h_base_cohen_d: 2.35
- id: 005-behavior-axis-direction-diagnostic
  at: '2026-06-20T09:40:00Z'
  kind: result
  title: Behavior Axis Direction Export And Same-Runtime Logit Diagnostic
  summary: 'Exported six norm-matched behavior-axis mean-difference directions from
    the layerwise scan and ran a Docker logit diagnostic in the same adapterless SFT
    runtime for all candidates. The directions are scaled to the prior SAE-composite
    comparison norm. KTO and SFT-derived axes moved refusal-opener probability more
    than DPO axes. However, wrong-layer subtraction controls were comparable to or
    stronger than source-layer effects, so this is still distributed-subspace evidence
    rather than source-layer-local mechanism evidence.

    '
  evidence:
  - experiment/phase1/probe/phase3_behavior_axis_directions.py
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_logit_diagnostic.yaml
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_directions/phase3_selfaware_behavior_axis_directions/behavior_axis_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python -m pytest experiment\phase1\probe\tests\test_phase3_behavior_axis_directions.py
    experiment\phase1\probe\tests\test_phase3_behavior_axis_scan.py -q
  - python -m py_compile experiment\phase1\probe\phase3_behavior_axis_scan.py experiment\phase1\probe\phase3_behavior_axis_directions.py
  - python experiment\phase1\probe\phase3_behavior_axis_directions.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_directions.yaml
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_logit_diagnostic\summary.csv
  decisions:
  - Use adapterless SFT runtime for the diagnostic so DPO/KTO/SFT axes share one live
    model.
  - Treat direction outputs as `BEHAVIOR_AXIS_DIRECTION_CANDIDATES_ONLY` and live
    results as Tier 2 exploratory local evidence.
  - Do not claim source-layer localization because wrong-layer controls remain competitive.
  signals:
    exported_direction_count: 6
    live_jobs_completed: 6
    aggregate_rows: 96
    baseline_refusal_probability_mean: 0.607347
    dpo_refusal_axis_l28_coef50_addition_delta: 0.001289
    dpo_refusal_axis_l28_coef50_subtraction_delta: -0.060772
    dpo_confidence_axis_l28_coef50_addition_delta: 0.015719
    dpo_confidence_axis_l28_coef50_subtraction_delta: -0.073261
    kto_refusal_axis_l25_coef50_addition_delta: 0.061073
    kto_refusal_axis_l25_coef50_subtraction_delta: -0.135532
    kto_confidence_axis_l25_coef50_addition_delta: 0.062075
    kto_confidence_axis_l25_coef50_subtraction_delta: -0.141613
    sft_broad_policy_axis_l24_coef50_addition_delta: 0.013697
    sft_broad_policy_axis_l24_coef50_subtraction_delta: -0.113933
    sft_known_overrefusal_axis_l27_coef50_addition_delta: 0.043377
    sft_known_overrefusal_axis_l27_coef50_subtraction_delta: -0.170751
    strongest_source_top1_changed_rate: 25.0
    strongest_wrong_layer_delta: -0.178085
- id: 006-nearby-layer-known-panel-diagnostic
  at: '2026-06-20T09:48:00Z'
  kind: result
  title: Nearby-Layer And Known-Panel Diagnostic Completed
  summary: 'Ran a focused follow-up over KTO L25 behavior axes and the SFT L27 known-overrefusal
    axis. KTO axes used the same unknown-row panel as the prior run, while SFT L27
    used a balanced known-row panel containing four SFT-known-refused rows and four
    SFT-known-correct rows. The SFT known panel showed stronger source-layer movement
    than the prior unknown-panel test, but lower wrong-layer offsets, especially source
    minus 2 and minus 3, were still stronger. KTO nearby-layer profiles showed the
    same pattern: source-layer subtraction moved refusal probability, but source-minus-2
    controls were stronger. This pushes the interpretation further away from a single
    source-layer knob and toward a broad late/mid-layer control direction.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic.yaml
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_nearby_known_logit_diagnostic\summary.csv
  decisions:
  - Use coefficient 50 only for this nearby-layer map because the prior diagnostic
    established it as the clearest effect size.
  - Keep the interpretation as distributed-subspace evidence because wrong-layer controls
    beat or match source-layer effects.
  signals:
    aggregate_rows: 48
    live_jobs_completed: 3
    kto_unknown_panel_baseline_refusal_probability: 0.607347
    sft_known_panel_baseline_refusal_probability: 0.345686
    kto_refusal_axis_source_subtraction_delta: -0.135532
    kto_refusal_axis_best_nearby_delta: -0.162573
    kto_refusal_axis_best_nearby_offset: -2
    kto_confidence_axis_source_subtraction_delta: -0.141613
    kto_confidence_axis_best_nearby_delta: -0.185252
    kto_confidence_axis_best_nearby_offset: -2
    sft_known_overrefusal_source_addition_delta: 0.142834
    sft_known_overrefusal_source_subtraction_delta: -0.193216
    sft_known_overrefusal_best_nearby_addition_delta: 0.249578
    sft_known_overrefusal_best_nearby_addition_offset: -3
    sft_known_overrefusal_best_nearby_subtraction_delta: -0.248668
    sft_known_overrefusal_best_nearby_subtraction_offset: -3
    sft_known_overrefusal_best_top1_changed_rate: 62.5
- id: 007-layer-window-source-axis-diagnostic
  at: '2026-06-20T10:05:00Z'
  kind: result
  title: Layer-Window Source-Axis Diagnostic Completed
  summary: 'Exported layer-specific behavior axes across the layer window implied
    by the nearby-layer controls, then reran the same-runtime adapterless SFT logit
    diagnostic. This tests whether earlier wrong-layer effects were artifacts of applying
    a late-layer vector at earlier layers or whether the behavior axis itself is stronger
    earlier. Results support a banded representation: KTO within-unknown axes are
    strongest around layers 24-25 under subtraction, while SFT known-overrefusal is
    strongest at layer 24 under addition and remains strong through layers 24-26 under
    subtraction. Random matched-norm controls are much smaller than source behavior
    axes.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_layer_window_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic.yaml
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_directions/phase3_selfaware_behavior_axis_layer_window_directions/behavior_axis_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_layer_window_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python experiment\phase1\probe\phase3_behavior_axis_directions.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_layer_window_directions.yaml
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_layer_window_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_layer_window_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_layer_window_logit_diagnostic\summary.csv
  decisions:
  - Treat the result as distributed layer-window evidence, not a localized feature
    or single-layer circuit.
  - Keep source axes norm-matched to the previous behavior-axis diagnostic so layer
    comparisons are not dominated by vector magnitude.
  signals:
    aggregate_rows: 48
    live_jobs_completed: 12
    kto_unknown_panel_baseline_refusal_probability: 0.607347
    sft_known_panel_baseline_refusal_probability: 0.345686
    kto_refusal_l22_addition_delta: 0.077752
    kto_refusal_l22_subtraction_delta: -0.111042
    kto_refusal_l23_addition_delta: 0.036612
    kto_refusal_l23_subtraction_delta: -0.104751
    kto_refusal_l24_addition_delta: 0.057775
    kto_refusal_l24_subtraction_delta: -0.138328
    kto_refusal_l25_addition_delta: 0.061073
    kto_refusal_l25_subtraction_delta: -0.135532
    kto_confidence_l22_addition_delta: 0.092542
    kto_confidence_l22_subtraction_delta: -0.116736
    kto_confidence_l23_addition_delta: 0.047857
    kto_confidence_l23_subtraction_delta: -0.125516
    kto_confidence_l24_addition_delta: 0.054779
    kto_confidence_l24_subtraction_delta: -0.147
    kto_confidence_l25_addition_delta: 0.062075
    kto_confidence_l25_subtraction_delta: -0.141613
    sft_known_l24_addition_delta: 0.27296
    sft_known_l24_subtraction_delta: -0.222947
    sft_known_l25_addition_delta: 0.243109
    sft_known_l25_subtraction_delta: -0.226923
    sft_known_l26_addition_delta: 0.1734
    sft_known_l26_subtraction_delta: -0.223142
    sft_known_l27_addition_delta: 0.142834
    sft_known_l27_subtraction_delta: -0.193216
    strongest_sft_top1_changed_rate: 50.0
- id: 008-known-panel-answer-token-follow-up
  at: '2026-06-20T10:18:00Z'
  kind: result
  title: Known-Panel Answer-Token Follow-Up Found Gold-Alias Limitation
  summary: 'Ran a focused SFT known-panel logit diagnostic with an added `answer_aliases`
    target group. The diagnostic executed successfully, but the SelfAware known rows
    do not carry `answer_value` or `normalized_aliases`, and no matching `selection.probe_results`
    file is available for these SelfAware row keys. Therefore the row-specific answer-alias
    metric was skipped and cannot answer whether reduced refusal probability moves
    toward gold answers. Raw top-k inspection is still informative: subtracting the
    SFT known-overrefusal axis often reduces the `I` refusal opener and exposes plausible
    answer-start tokens (`King`, `Board`, `C`, `Chair`, `Crypt`), but this is not
    gold-scored correctness evidence.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-behavior-axis/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_behavior_axis_known_answer_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\selfaware-behavior-axis\phase3_selfaware_behavior_axis_known_answer_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_known_answer_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-sft-merged-seed1-selfaware\causal_pilots\phase3_selfaware_behavior_axis_known_answer_logit_diagnostic\summary.csv
  decisions:
  - Do not report answer-alias movement for SelfAware rows without gold aliases.
  - Treat raw top-k answer-start movement as qualitative diagnostic evidence only.
  - Use a gold-backed TriviaQA/Cheng-known panel for the next row-specific answer-token
    probability test.
  signals:
    aggregate_rows: 16
    live_jobs_completed: 4
    selfaware_known_rows_with_aliases: 0
    answer_alias_metric_available: false
    l24_subtraction_refusal_delta: -0.222947
    l24_subtraction_top1_changed_rate: 50.0
    l25_subtraction_refusal_delta: -0.226923
    l25_subtraction_top1_changed_rate: 50.0
    l26_subtraction_refusal_delta: -0.223142
    l26_subtraction_top1_changed_rate: 50.0
    l27_subtraction_refusal_delta: -0.193216
    l27_subtraction_top1_changed_rate: 50.0
- id: 009-gold-backed-first-token-answer-slice
  at: '2026-06-20T10:24:00Z'
  kind: result
  title: Gold-Backed First-Token Answer Slice Re-Aggregated
  summary: 'Refreshed stale logit metric artifacts for the existing `phase3_changed_row_probability_slice`
    runs, patched the slice config so `answer_aliases` uses first tokens for multi-token
    aliases, and reran the two focused DPO/KTO candidates in Docker. This gives a
    gold-backed first-token answer-start diagnostic on a tiny changed-row slice. KTO
    `h_lora` subtraction is the cleanest directional signal: refusal-opener probability
    decreases while answer-alias first-token probability increases. DPO `delta` addition
    decreases refusal but also decreases answer-alias probability, and the DPO wrong-layer
    control is competitive, so DPO remains confounded.

    '
  evidence:
  - archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_changed_row_probability_slice.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260620T101428Z/run_manifest.json
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260620T101554Z/run_manifest.json
  commands:
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_changed_row_probability_slice
    --out experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_changed_row_probability_slice\summary.csv
  - docker run --rm --gpus all --ipc=host --entrypoint python -e HF_HOME=/workspace/repo/.cache/hf
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v F:\Code\Epistemic-Humility-Research:/workspace/repo
    -w /workspace/repo unsloth/unsloth:latest /workspace/repo/experiment/phase1/probe/phase3_causal_pilot_runner.py
    --mode logit_diagnostic --config /workspace/repo/archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_changed_row_probability_slice.yaml
    --candidate sft_dpo_delta_l35 --coefficients 50.0 --controls no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm
    --max-rows 16 --allow-logit-diagnostic
  - docker run --rm --gpus all --ipc=host --entrypoint python -e HF_HOME=/workspace/repo/.cache/hf
    -e HUGGINGFACE_HUB_CACHE=/workspace/repo/.cache/hf/hub -v F:\Code\Epistemic-Humility-Research:/workspace/repo
    -w /workspace/repo unsloth/unsloth:latest /workspace/repo/experiment/phase1/probe/phase3_causal_pilot_runner.py
    --mode logit_diagnostic --config /workspace/repo/archive/experiment/phase1/probe/config/causal-pilot-core/phase3_causal_pilot_changed_row_probability_slice.yaml
    --candidate sft_kto_h_lora_l35 --coefficients 50.0 --controls no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm
    --max-rows 16 --allow-logit-diagnostic
  decisions:
  - Use first-token answer-alias probability as a diagnostic of answer-start movement,
    not exact multi-token correctness.
  - Treat this as tiny-slice Tier 2 exploratory evidence only.
  - Keep DPO claims guarded because wrong-layer controls are competitive.
  signals:
    latest_dpo_rows: 4
    latest_kto_rows: 2
    dpo_addition_refusal_delta: -0.049596
    dpo_addition_answer_alias_delta: -0.015177
    dpo_wrong_layer_refusal_delta: -0.045936
    dpo_wrong_layer_answer_alias_delta: 0.01708
    kto_subtraction_refusal_delta: -0.043785
    kto_subtraction_answer_alias_delta: 0.019574
    kto_subtraction_top1_changed_rate: 100.0
    kto_wrong_layer_refusal_delta: 0.057611
    kto_wrong_layer_answer_alias_delta: -0.007242
- id: 010-scaled-gold-backed-answer-slice
  at: '2026-06-20T10:31:00Z'
  kind: result
  title: Scaled Gold-Backed Answer Slice Weakens Tiny KTO Signal
  summary: 'Added and executed a scaled Docker sweep over the same DPO/KTO directions
    on the balanced 16-row gold-backed slice with first-token answer aliases. The
    tiny changed-row KTO pattern did not replicate at this scale: KTO subtraction
    still reduced refusal-openers, but answer-alias first-token probability decreased
    slightly rather than increasing. DPO remained non-specific: source addition reduced
    refusal modestly with near-zero answer movement, while wrong-layer controls were
    comparable on refusal and sometimes better on answer movement. This reinforces
    the view that these broad late-layer directions modulate refusal/answer style
    more reliably than they recover correct answers.

    '
  evidence:
  - archive/experiment/phase1/probe/config/gold-answer-kto-panels/phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_scaled_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_scaled_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python experiment\phase1\probe\phase3_causal_pilot_sweep.py --config archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_first_token_scaled_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_first_token_scaled_logit_diagnostic
    --out experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_first_token_scaled_logit_diagnostic\summary.csv
  decisions:
  - Do not treat the tiny changed-row KTO answer-alias increase as robust.
  - Prefer scaled gold-backed panels before claiming answer-recovery behavior from
    refusal-axis interventions.
  - Keep interpreting current broad directions as refusal/style controls, not correctness-recovery
    mechanisms.
  signals:
    dpo_scaled_rows: 16
    kto_scaled_rows: 16
    dpo_addition_refusal_delta: -0.015323
    dpo_addition_answer_alias_delta: 0.000239
    dpo_wrong_layer_refusal_delta: -0.014841
    dpo_wrong_layer_answer_alias_delta: 0.003427
    kto_subtraction_refusal_delta: -0.025373
    kto_subtraction_answer_alias_delta: -0.000991
    kto_random_refusal_delta: -0.013346
    kto_wrong_layer_refusal_delta: 0.031008
    kto_wrong_layer_answer_alias_delta: 0.005318
- id: 011-scaled-answer-slice-row-stratification
  at: '2026-06-20T10:42:00Z'
  kind: result
  title: Scaled Gold-Backed Slice Stratified By Known Unknown Labels
  summary: 'Split the scaled gold-backed logit JSONL by known vs unknown labels to
    check whether the aggregate masked different behavior. It did: KTO subtraction
    reduced refusal mostly on unknown rows, but answer-start probability also dropped
    on those unknown rows. Known rows had a small answer-start increase under KTO
    subtraction. DPO source addition lowered refusal on unknown rows, but wrong-layer
    showed a similar unknown-row refusal drop and better answer-start movement, so
    DPO remains non-specific. This strengthens the current interpretation that the
    tested directions steer refusal/style more than reliable answer recovery.

    '
  evidence:
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_scaled_logit_diagnostic/sft_dpo_delta_l35/logit_diagnostic/run_20260620T101953Z/logit_diagnostics.jsonl
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_scaled_logit_diagnostic/sft_kto_h_lora_l35/logit_diagnostic/run_20260620T102104Z/logit_diagnostics.jsonl
  commands:
  - inline Python row-level summary over latest phase3_gold_answer_first_token_scaled_logit_diagnostic
    logit_diagnostics.jsonl files
  - python -m pytest .\experiment\phase1\probe\tests\test_phase3_behavior_axis_scan.py
    .\experiment\phase1\probe\tests\test_phase3_behavior_axis_directions.py .\experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py
    .\experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py -q
  - python -m py_compile .\experiment\phase1\probe\phase3_behavior_axis_scan.py .\experiment\phase1\probe\phase3_behavior_axis_directions.py
    .\experiment\phase1\probe\phase3_causal_pilot_runner.py .\experiment\phase1\probe\phase3_causal_pilot_sweep.py
  - python .\bin\sync_skills.py --check
  decisions:
  - Report scaled answer-start diagnostics by label group before interpreting aggregate
    averages.
  - Do not treat KTO unknown-row refusal reduction as answer recovery unless answer-alias
    movement rises on the same unknown rows and beats controls.
  signals:
    dpo_unknown_addition_refusal_delta: -0.032731
    dpo_unknown_addition_answer_alias_delta: -0.001781
    dpo_unknown_wrong_layer_refusal_delta: -0.02991
    dpo_unknown_wrong_layer_answer_alias_delta: 0.006896
    kto_unknown_subtraction_refusal_delta: -0.037008
    kto_unknown_subtraction_answer_alias_delta: -0.006542
    kto_known_subtraction_refusal_delta: -0.013738
    kto_known_subtraction_answer_alias_delta: 0.00456
    validation_pytest: 69 passed
    validation_sync_skills: in_sync
- id: 012-gold-backed-answer-slice-64-row-panel
  at: '2026-06-20T10:56:00Z'
  kind: result
  title: Sixty-Four Row Gold-Backed Answer Slice Completed
  summary: 'Added and ran a larger balanced 64-row gold-backed answer-start sweep
    for the same DPO/KTO directions. The result is more stable but still not a clean
    source-layer answer-recovery mechanism. DPO addition lowered refusal on unknown
    rows and slightly increased answer-start probability, but wrong-layer produced
    nearly the same unknown-row refusal movement and similar row-count behavior. KTO
    subtraction moved unknown rows in the desired mean direction, lowering refusal
    and raising answer-start probability, but the effect was modest and random matched-norm
    control had comparable refusal movement and row-count overlap. This keeps KTO
    alive as a weak steering lead while leaving source specificity unresolved.

    '
  evidence:
  - archive/experiment/phase1/probe/config/gold-answer-kto-panels/phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_64_logit_diagnostic/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_64_logit_diagnostic/row_stratification_summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_64_logit_diagnostic/row_direction_counts.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_first_token_64_logit_diagnostic/_execution_logs/execution_results.jsonl
  commands:
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_first_token_64_logit_diagnostic_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_first_token_64_logit_diagnostic
    --out .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_first_token_64_logit_diagnostic\summary.csv
  - inline Python row-level summary and direction-count export over latest 64-row
    logit_diagnostics.jsonl files
  decisions:
  - Keep DPO source-layer claims guarded because wrong-layer remains nearly identical
    on the unknown-row target.
  - Treat KTO subtraction as a weak candidate for further coefficient/row-stratified
    tests, not as robust evidence of correctness recovery.
  - Future answer-recovery claims need per-label movement, row-count support, and
    control separation.
  signals:
    dpo_rows: 64
    dpo_unknown_addition_refusal_delta: -0.05375
    dpo_unknown_addition_answer_alias_delta: 0.000984
    dpo_unknown_addition_both_good_count: 25
    dpo_unknown_wrong_layer_refusal_delta: -0.048397
    dpo_unknown_wrong_layer_answer_alias_delta: 0.000514
    dpo_unknown_wrong_layer_both_good_count: 23
    kto_rows: 64
    kto_unknown_subtraction_refusal_delta: -0.01331
    kto_unknown_subtraction_answer_alias_delta: 0.003965
    kto_unknown_subtraction_both_good_count: 15
    kto_unknown_random_refusal_delta: -0.016527
    kto_unknown_random_answer_alias_delta: 0.000421
    kto_unknown_random_both_good_count: 17
- id: 013-unknown-row-coefficient-sweep
  at: '2026-06-20T11:05:00Z'
  kind: result
  title: Unknown-Row Coefficient Sweep Clarifies KTO And DPO Controls
  summary: 'Added and ran a fixed 32-unknown-row coefficient sweep over coefficients
    10, 20, 35, and 50. DPO addition scales monotonically in refusal reduction and
    beats random, but wrong-layer remains extremely close across coefficients, so
    DPO still looks like a non-local direction rather than source-layer-specific evidence.
    KTO subtraction also scales in the desired direction. Its wrong-layer control
    moves the opposite way (increasing refusal and decreasing answer-start probability),
    which is a better source-vs-wrong-layer sign than DPO. However, random matched-norm
    still confounds refusal reduction, especially at coefficient 50, while source
    subtraction is more favorable on answer-start probability. This makes KTO the
    better mechanistic lead, but the current claim is still "weak source direction
    with random-control caveat," not clean answer recovery.

    '
  evidence:
  - archive/experiment/phase1/probe/config/gold-answer-kto-panels/phase3_gold_answer_unknown_coeff_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_unknown_coeff_sweep/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_unknown_coeff_sweep/coefficient_curve_summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_unknown_coeff_sweep/_execution_logs/execution_results.jsonl
  commands:
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_unknown_coeff_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_unknown_coeff_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_unknown_coeff_sweep
    --out .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_unknown_coeff_sweep\summary.csv
  - inline Python coefficient-curve export over latest unknown-row sweep JSONLs
  decisions:
  - Prioritize KTO for next causal follow-up because wrong-layer has opposite sign,
    even though random still limits the claim.
  - Treat DPO as non-local until a nearby-layer/source-window or alternative control
    separates it from wrong-layer.
  - Use fixed row keys for coefficient sweeps when comparing candidate/control curves.
  signals:
    row_count: 32
    coefficients:
    - 10.0
    - 20.0
    - 35.0
    - 50.0
    dpo_addition_c10_refusal_delta: -0.015279
    dpo_addition_c50_refusal_delta: -0.05375
    dpo_addition_c50_answer_alias_delta: 0.000984
    dpo_wrong_layer_c50_refusal_delta: -0.048397
    dpo_wrong_layer_c50_answer_alias_delta: 0.000514
    kto_subtraction_c10_refusal_delta: -0.002949
    kto_subtraction_c10_answer_alias_delta: 0.00146
    kto_subtraction_c50_refusal_delta: -0.01331
    kto_subtraction_c50_answer_alias_delta: 0.003965
    kto_wrong_layer_c50_refusal_delta: 0.022849
    kto_wrong_layer_c50_answer_alias_delta: -0.003896
    kto_random_c50_refusal_delta: -0.016527
    kto_random_c50_answer_alias_delta: 0.000421
- id: 014-kto-random-seed-panel
  at: '2026-06-20T11:14:00Z'
  kind: result
  title: KTO Random Matched-Norm Seed Panel Strengthens Source Lead
  summary: 'Added generic multi-seed random matched-norm support to the causal pilot
    runner, tested it, then ran a KTO-only five-seed random-control panel on the fixed
    32 unknown rows at coefficients 35 and 50. This materially improves the KTO read.
    At both coefficients, source subtraction beats the random-seed mean on refusal
    reduction and answer-start lift, while wrong-layer moves in the opposite direction.
    One random seed at coefficient 50 lowers refusal more than source, but it does
    not reproduce the source answer-start lift; other seeds do not reproduce the combined
    pattern. This upgrades KTO from "weak source direction with random-control caveat"
    to "best current source-specific candidate, still Tier 2 and still next-token/answer-start
    only."

    '
  evidence:
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
  - archive/experiment/phase1/probe/config/gold-answer-kto-panels/phase3_gold_answer_kto_random_seed_panel.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_random_seed_panel/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_random_seed_panel/random_seed_panel_summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_random_seed_panel/_execution_logs/execution_results.jsonl
  commands:
  - python -m pytest .\experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py
    .\experiment\phase1\probe\tests\test_phase3_causal_pilot_sweep.py -q
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_kto_random_seed_panel.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_kto_random_seed_panel.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_kto_random_seed_panel
    --out .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_kto_random_seed_panel\summary.csv
  - inline Python random-seed panel summary export
  decisions:
  - Treat KTO `h_lora_l35` subtraction as the best current source-specific answer-start
    candidate.
  - Keep the evidence tier limited: this is next-token first-token answer-start movement,
      not generated-answer correctness.
  - Use the new `control_settings.random_matched_norm.seeds` runner option for future
    random-control panels instead of copying separate configs.
  signals:
    random_seed_count: 5
    coefficients:
    - 35.0
    - 50.0
    kto_c35_source_refusal_delta: -0.012078
    kto_c35_source_answer_alias_delta: 0.002037
    kto_c35_wrong_layer_refusal_delta: 0.01499
    kto_c35_wrong_layer_answer_alias_delta: -0.003866
    kto_c35_random_refusal_delta_mean: -0.000128
    kto_c35_random_refusal_delta_min: -0.007666
    kto_c35_random_refusal_delta_max: 0.003616
    kto_c35_random_answer_alias_delta_mean: 0.000278
    kto_c50_source_refusal_delta: -0.01331
    kto_c50_source_answer_alias_delta: 0.003965
    kto_c50_wrong_layer_refusal_delta: 0.022849
    kto_c50_wrong_layer_answer_alias_delta: -0.003896
    kto_c50_random_refusal_delta_mean: -0.000951
    kto_c50_random_refusal_delta_min: -0.016527
    kto_c50_random_refusal_delta_max: 0.00525
    kto_c50_random_answer_alias_delta_mean: 0.000503
- id: 015-kto-generated-answer-replay
  at: '2026-06-20T11:24:00Z'
  kind: result
  title: KTO Generated-Answer Replay Does Not Improve Correctness
  summary: 'Ran a bounded generation replay for KTO source subtraction on the same
    fixed 32 unknown rows at coefficients 35 and 50. This tested whether the next-token
    answer-start signal translated into generated-answer behavior. It did not improve
    correctness. Baseline answered 18.75% of unknown rows and had 3.125% exact correctness;
    KTO subtraction answered 21.875% and kept exact correctness at 3.125%. The one
    refusal-to-answer flip was a hallucinated answer: first Miss World country changed
    from refusal to "England" while the gold answer is Sweden. One already-answering
    row changed from "Earth" to "The Sun" but still failed exact scoring for a compound
    gold answer. This means the KTO logit signal is real enough to move surface behavior,
    but not yet useful answer recovery.

    '
  evidence:
  - archive/experiment/phase1/probe/config/gold-answer-kto-panels/phase3_gold_answer_kto_unknown_generation_replay.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_unknown_generation_replay/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_unknown_generation_replay/generation_replay_summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_unknown_generation_replay/generation_changed_rows.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_unknown_generation_replay/sft_kto_h_lora_l35/generation/run_20260620T104743Z/scored_rows.jsonl
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_answer_kto_unknown_generation_replay/_execution_logs/execution_results.jsonl
  commands:
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_kto_unknown_generation_replay.yaml
    --mode-filter generation --write-plan --materialize-configs
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\gold-answer-kto-panels\phase3_gold_answer_kto_unknown_generation_replay.yaml
    --mode-filter generation --write-plan --materialize-configs --execute --allow-generation
  - python .\experiment\phase1\probe\phase3_causal_pilot_aggregate.py --root .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_kto_unknown_generation_replay
    --out .\experiment\phase1\probe\qwen3-4b-instruct\causal_pilots\phase3_gold_answer_kto_unknown_generation_replay\summary.csv
  - inline Python generated-answer replay summary and changed-row export
  decisions:
  - Do not treat KTO answer-start movement as answer-recovery evidence.
  - Treat generated-answer replay as the stronger behavioral gate for future steering
    claims.
  - Escalate the finding as a research-direction signal: internal steering can reduce
      refusal without improving correctness, which may worsen truthfulness on unknown
      rows.
  signals:
    row_count: 32
    baseline_unknown_refusal_rate: 81.25
    kto_subtraction_unknown_refusal_rate: 78.125
    baseline_answer_on_unknown_rate: 18.75
    kto_subtraction_answer_on_unknown_rate: 21.875
    baseline_correct_rate: 3.125
    kto_subtraction_correct_rate: 3.125
    refusal_changed_count: 1
    correct_changed_count: 0
    harmful_flip_example_key: 000000001480|tc_2358
    harmful_flip_gold: Sweden
    harmful_flip_intervention_answer: England
- id: 016-calibrated-expression-axis-scan
  at: '2026-06-20T11:43:00Z'
  kind: result
  title: Calibrated-Expression Behavior Cell Scan Completed
  summary: 'Added and ran a CPU-only behavior-axis scan that explicitly separates
    calibrated-expression cells instead of treating refusal as the target. The key
    within-unknown contrast is `unknown_answered_wrong` versus `unknown_refused`;
    the paired known-damage contrast is `known_refused` versus `known_correct_answered`.
    KTO has the stronger within-unknown separation, centered around layers 24-25 across
    h_base/h_lora/delta, while DPO''s within-unknown separation is weaker and later
    around layers 26-28. Known-overrefusal damage separates strongly for KTO, peaking
    at h_lora/base layer 27 and delta layer 22. Broad unknown-vs-known contrasts remain
    much stronger, confirming that a raw refusal/unknown axis is easier to find than
    the behavior we actually want.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-axis/phase3_selfaware_calibrated_expression_axis_scan.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_calibrated_expression_axis_scan/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_calibrated_expression_axis_scan/top_layers_all.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_calibrated_expression_axis_scan/axis_scan_all.csv
  commands:
  - python .\experiment\phase1\probe\phase3_behavior_axis_scan.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-axis\phase3_selfaware_calibrated_expression_axis_scan.yaml
  decisions:
  - Use calibrated-expression cells as the primary lens going forward, not refusal
    probability alone.
  - Prioritize KTO unknown_answered_wrong-vs-unknown_refused layer 24-25 as the next
    candidate source window.
  - Treat broad unknown-vs-known axes as controls or context, not the desired target.
  signals:
    scan_rows: 851
    dpo_unknown_wrong_vs_refused_best_delta_layer: 28
    dpo_unknown_wrong_vs_refused_best_delta_cohen_d: 1.262
    dpo_unknown_wrong_vs_refused_best_delta_auc: 0.812
    kto_unknown_wrong_vs_refused_best_delta_layer: 25
    kto_unknown_wrong_vs_refused_best_delta_cohen_d: 1.424
    kto_unknown_wrong_vs_refused_best_delta_auc: 0.838
    kto_unknown_wrong_vs_refused_best_h_lora_layer: 24
    kto_unknown_wrong_vs_refused_best_h_lora_cohen_d: 1.423
    kto_known_refused_vs_correct_best_h_lora_layer: 27
    kto_known_refused_vs_correct_best_h_lora_cohen_d: 2.839
    broad_unknown_refused_vs_known_correct_remains_stronger: true
- id: 017-calibrated-expression-direction-geometry
  at: '2026-06-20T12:02:00Z'
  kind: result
  title: Calibrated-Expression Direction Geometry Shows Stable Anti-Aligned Damage
    Axes
  summary: 'Exported calibrated-expression direction candidates and mapped their geometry
    against prior behavior/refusal axes. The unknown-wrong-vs-refused directions are
    exactly sign-flipped versions of the earlier unknown-refused-vs-answered axes,
    so the relabeling clarified the behavioral target but did not reveal a new hidden
    direction by itself. The more important result is in the KTO h_lora layer window:
    both damage axes are internally stable across layers 24-27, but same-layer unknown-wrong
    damage and known-overrefusal damage are consistently anti-aligned at roughly `-0.49`
    to `-0.53`. That supports a coherent layer band with multiple opposing behavior
    axes rather than a single epistemic-humility knob.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-axis/phase3_selfaware_calibrated_expression_axis_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-geometry-and-subspace/phase3_selfaware_calibrated_expression_direction_geometry.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-axis/phase3_selfaware_calibrated_expression_hlora_window_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-geometry-and-subspace/phase3_selfaware_calibrated_expression_hlora_window_geometry.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_directions/phase3_selfaware_calibrated_expression_axis_directions/behavior_axis_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_directions/phase3_selfaware_calibrated_expression_hlora_window_directions/behavior_axis_directions.manifest.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_direction_geometry/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_hlora_window_geometry/pairwise_cosine.csv
  commands:
  - python .\experiment\phase1\probe\phase3_behavior_axis_directions.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-axis\phase3_selfaware_calibrated_expression_axis_directions.yaml
  - python .\experiment\phase1\probe\phase3_direction_geometry.py --config .\archive\experiment\phase1\probe\config\selfaware-geometry-and-subspace\phase3_selfaware_calibrated_expression_direction_geometry.yaml
  - python .\experiment\phase1\probe\phase3_behavior_axis_directions.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-axis\phase3_selfaware_calibrated_expression_hlora_window_directions.yaml
  - python .\experiment\phase1\probe\phase3_direction_geometry.py --config .\archive\experiment\phase1\probe\config\selfaware-geometry-and-subspace\phase3_selfaware_calibrated_expression_hlora_window_geometry.yaml
  decisions:
  - Treat KTO h_lora L24-L27 as the current coherent calibrated-expression layer band.
  - Do not pursue a single-vector humility knob from these axes; same-layer damage
    axes partially oppose each other.
  - Next controlled tests should evaluate both failure modes together, not only refusal
    or answer-start movement.
  signals:
    h_lora_unknown_wrong_axis_adjacent_layer_cosine_l24_l25: 0.864
    h_lora_unknown_wrong_axis_adjacent_layer_cosine_l25_l26: 0.894
    h_lora_unknown_wrong_axis_adjacent_layer_cosine_l26_l27: 0.926
    h_lora_known_overrefusal_axis_adjacent_layer_cosine_l24_l25: 0.9
    h_lora_known_overrefusal_axis_adjacent_layer_cosine_l25_l26: 0.918
    h_lora_known_overrefusal_axis_adjacent_layer_cosine_l26_l27: 0.958
    same_layer_damage_axis_cosine_l24: -0.518
    same_layer_damage_axis_cosine_l25: -0.486
    same_layer_damage_axis_cosine_l26: -0.526
    same_layer_damage_axis_cosine_l27: -0.515
- id: 018-calibrated-expression-plane-projection
  at: '2026-06-20T12:14:00Z'
  kind: result
  title: KTO h_lora Two-Axis Plane Separates Policy-Like Regions
  summary: 'Projected KTO h_lora layer 24-27 rows into a two-axis plane: the unknown-wrong
    damage axis and the known-overrefusal damage axis. The plane suggests the failure
    is not just a refusal scalar. Known-correct rows sit at high unknown-wrong-axis
    / low known-overrefusal-axis values, while unknown-refused rows sit at low unknown-wrong-axis
    / high known-overrefusal-axis values. Known-refused rows land near the unknown-refused
    region, consistent with over-refusal behaving like applying an unknown/refusal
    policy to known questions. Unknown-answered wrong rows are intermediate and closer
    to the answer side than refused unknowns. This supports a two-dimensional mapping
    problem: knowledge state and answer/refusal policy need to be aligned, not simply
    pushed toward or away from refusal.

    '
  evidence:
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_hlora_window_geometry/calibrated_expression_plane_summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_hlora_window_geometry/calibrated_expression_plane_rows.csv
  commands:
  - inline Python projection of KTO h_lora L24-L27 hidden states onto calibrated-expression
    damage axes
  decisions:
  - Treat calibrated expression as a policy-state alignment problem, not a one-axis
    refusal problem.
  - Use the h_lora L24-L27 plane to choose future interventions that test both known-overrefusal
    and unknown-hallucination behavior together.
  signals:
    l24_known_correct_u_mean: 7.736
    l24_known_correct_k_mean: -13.647
    l24_known_refused_u_mean: -6.047
    l24_known_refused_k_mean: 12.948
    l24_unknown_refused_u_mean: -16.758
    l24_unknown_refused_k_mean: 10.724
    l24_unknown_answered_wrong_u_mean: -2.776
    l24_unknown_answered_wrong_k_mean: 3.478
    l27_known_correct_u_mean: -4.747
    l27_known_correct_k_mean: -9.577
    l27_known_refused_u_mean: -27.468
    l27_known_refused_k_mean: 34.556
    l27_unknown_refused_u_mean: -45.162
    l27_unknown_refused_k_mean: 32.99
    l27_unknown_answered_wrong_u_mean: -19.198
    l27_unknown_answered_wrong_k_mean: 19.623
- id: 019-calibrated-expression-plane-script
  at: '2026-06-20T12:30:00Z'
  kind: result
  title: Reusable Calibrated-Expression Plane Analysis Completed
  summary: 'Re-ran the calibrated-expression plane analysis through the checked-in
    reusable script and config. The run projected KTO h_lora layers 24-27 into the
    paired unknown-wrong and known-overrefusal damage axes. It reproduced the earlier
    KTO h_lora pattern: known-correct answered rows and unknown-refused rows occupy
    opposite regions; known-refused rows sit close to unknown-refused rows; unknown-answered-wrong
    rows are intermediate and more answer-side than refused unknowns. Same-layer x/y
    axes remain anti-aligned, so the interpretation stays multi-axis policy-state
    alignment rather than a single humility knob.

    '
  evidence:
  - experiment/phase1/probe/phase3_calibrated_expression_plane.py
  - archive/experiment/phase1/probe/config/selfaware-geometry-and-subspace/phase3_selfaware_calibrated_expression_plane.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/calibrated_expression_plane/phase3_selfaware_calibrated_expression_plane/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/calibrated_expression_plane/phase3_selfaware_calibrated_expression_plane/plane_summary.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/calibrated_expression_plane/phase3_selfaware_calibrated_expression_plane/plane_rows.csv
  commands:
  - python .\experiment\phase1\probe\phase3_calibrated_expression_plane.py --config
    .\archive\experiment\phase1\probe\config\selfaware-geometry-and-subspace\phase3_selfaware_calibrated_expression_plane.yaml
  decisions:
  - Treat the reusable plane output as the current provenance for KTO h_lora L24-L27
    calibrated-expression cell projections.
  - Use paired behavior-cell movement, not refusal movement alone, to evaluate future
    interventions from this layer window.
  signals:
    projection_row_count: 4932
    layers: 4
    rows_per_layer: 1233
    known_correct_answered_rows_across_layers: 1860
    known_refused_rows_across_layers: 132
    unknown_answered_wrong_rows_across_layers: 368
    unknown_refused_rows_across_layers: 2340
    other_rows_across_layers: 232
- id: 020-cross-regimen-calibrated-expression-geometry
  at: '2026-06-20T12:45:00Z'
  kind: result
  title: Cross-Regimen Geometry Shows Shared Over-Refusal, Not Shared Unknown-Wrong
    Axis
  summary: 'Mined the existing calibrated-expression h_lora window geometry rather
    than creating a new config. SFT and KTO known-overrefusal directions align strongly
    at matched layers, while DPO''s unknown-wrong-vs-refused delta direction is nearly
    orthogonal to the KTO h_lora unknown-wrong-vs-refused window. This supports a
    regimen-asymmetric read: SFT and KTO share a strong over-refusal geometry, DPO
    exposes an under-refusal/hallucination failure mode in a different direction,
    and KTO is the only current seed1 panel with enough rows for both damage axes
    in the same behavior plane.

    '
  evidence:
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_hlora_window_geometry/pairwise_cosine.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/direction_geometry/phase3_selfaware_calibrated_expression_hlora_window_geometry/nearest_neighbors.csv
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_calibrated_expression_axis_scan/sft_dpo_seed1_full/summary.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/behavior_axis_scan/phase3_selfaware_calibrated_expression_axis_scan/sft_merged_seed1_behavior_on_dpo_base_hidden/summary.json
  commands:
  - Import-Csv ...\pairwise_cosine.csv | filter SFT known-overrefusal vs KTO known-overrefusal
  - Import-Csv ...\pairwise_cosine.csv | filter DPO unknown-wrong/refused vs KTO unknown-wrong/refused
  decisions:
  - Do not assume a shared cross-regimen humility axis.
  - Treat available behavior-cell support as part of the evidence: SFT lacks unknown-wrong
      rows in this panel; DPO lacks known-refused rows; KTO has both.
  - Prefer future interventions that test paired cell movement inside KTO first, then
    replicate only behavior cells that are estimable in SFT/DPO.
  signals:
    sft_kto_known_overrefusal_same_layer_cosines:
    - 0.9125
    - 0.8975
    - 0.8902
    - 0.8801
    dpo_kto_unknown_wrong_abs_cosine_max: 0.0387
    kto_same_layer_damage_axis_cosines:
    - -0.5182
    - -0.4858
    - -0.5256
    - -0.5148
    dpo_known_refused_rows: 0
    sft_unknown_answered_wrong_rows: 0
- id: 021-kto-calibrated-expression-logit-sweep
  at: '2026-06-20T11:55:00Z'
  kind: result
  title: KTO Plane Axes Move Refusal Logits But Single-Axis Steering Is Too Blunt
  summary: 'Ran the KTO calibrated-expression logit diagnostic on 64 fixed SelfAware
    rows: 16 known-refused, 16 known-correct, 16 unknown-refused, and 16 unknown-answered-wrong.
    Tested KTO h_lora unknown-wrong-vs-refused L24 and known-refused-vs-correct L24/L27
    with source, wrong-layer, and random matched-norm controls. The axes are active
    and random controls are small, but source and wrong-layer effects are very close.
    Known-overrefusal subtraction reduces refusal-openers strongly on known-refused
    rows, but also reduces refusal-openers on unknown-refused rows. Unknown-wrong-axis
    subtraction has the opposite sign, increasing refusal-openers on unknown-answered-wrong
    rows. This supports a two-axis/composite-control next step rather than more single-axis
    scaling.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_logit_candidates.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_logit_sweep.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml
  - experiment/phase1/probe/phase3_logit_cell_analysis.py
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_calibrated_expression_kto_logit_sweep/cell_analysis/cell_logit_summary.csv
  commands:
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_logit_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_logit_cell_analysis.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_logit_cell_analysis.yaml
  decisions:
  - Treat single-axis KTO steering as active but unsafe for calibrated humility because
    it improves one cell while damaging another.
  - Prefer a composite plane direction next: subtract known-overrefusal damage and
      subtract unknown-wrong damage together, then check whether cell effects separate.
  - Keep this as logit evidence only until generated-answer replay verifies behavior.
  signals:
    known_axis_l24_subtraction_coef50_known_refused_refusal_delta: -0.4358
    known_axis_l24_subtraction_coef50_unknown_refused_refusal_delta: -0.2945
    known_axis_l27_subtraction_coef50_known_refused_refusal_delta: -0.3235
    known_axis_l27_subtraction_coef50_unknown_refused_refusal_delta: -0.1901
    unknown_axis_l24_subtraction_coef50_unknown_wrong_refusal_delta: 0.2501
    unknown_axis_l24_addition_coef50_unknown_wrong_refusal_delta: -0.2083
    random_matched_norm_refusal_delta_near_zero: true
    wrong_layer_controls_close_to_source: true
- id: 022-kto-composite-plane-grid
  at: '2026-06-20T12:22:00Z'
  kind: result
  title: Equal Composite Fails, Weighted KTO Composite Finds Weak Tradeoff
  summary: 'Added linear-combination direction transforms and tested KTO h_lora L24
    composites that combine known-overrefusal repair with unknown-wrong repair on
    the same 64 fixed SelfAware behavior-cell rows. The equal blend mostly cancelled
    the unknown-wrong repair. A 1:1.25 blend (known-overrefusal:unknown-wrong repair)
    produced the first right-signed cell pattern at coefficient 50: known-refused
    refusal-openers down, unknown-wrong refusal-openers up, known-correct roughly
    preserved, and unknown-refused slightly up. The effect is small and wrong-layer
    controls remain comparable, so this is not a clean source-layer mechanism.

    '
  evidence:
  - experiment/phase1/probe/phase3_direction_transforms.py
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite_grid_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_calibrated_expression_kto_composite_grid_logit_sweep/cell_analysis/cell_logit_summary.csv
  commands:
  - python .\experiment\phase1\probe\phase3_direction_transforms.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite_grid_directions.yaml
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite_grid_logit_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_logit_cell_analysis.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite_grid_logit_cell_analysis.yaml
  decisions:
  - Do not use the equal-weight composite as a candidate; it cancels too much of the
    unknown-wrong repair.
  - Treat 1:1.25 L24 as the best current composite logit tradeoff, but require generated
    replay before any behavioral claim.
  - Interpret wrong-layer parity as layer-window evidence, not localization.
  signals:
    equal_composite_l24_addition_coef50_known_refused_refusal_delta: -0.1216
    equal_composite_l24_addition_coef50_unknown_wrong_refusal_delta: -0.0263
    weighted_1p25_l24_addition_coef50_known_refused_refusal_delta: -0.025
    weighted_1p25_l24_addition_coef50_unknown_wrong_refusal_delta: 0.0599
    weighted_1p25_l24_addition_coef50_known_correct_refusal_delta: -0.0055
    weighted_1p25_l24_addition_coef50_unknown_refused_refusal_delta: 0.0254
    wrong_layer_comparable: true
- id: 023-kto-composite-layer-window
  at: '2026-06-20T12:32:00Z'
  kind: result
  title: KTO 1:1.25 Composite Is Best At L24 And Weakens Across L25-L27
  summary: 'Exported the 1:1.25 composite across KTO h_lora layers 24-27 and ran a
    focused source-vs-control logit diagnostic. L24 remains the cleanest layer: known-refused
    refusal-openers decrease while unknown-wrong refusal-openers increase. L25 and
    L26 keep weaker versions of the same pattern. L27 reduces refusal on both unknown-wrong
    and unknown-refused cells, which is the wrong direction for calibrated abstention.
    This supports a narrow L24-L26 window rather than a late-layer knob.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_directions.yaml
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_sweep.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_sweep/cell_analysis/cell_logit_summary.csv
  commands:
  - python .\experiment\phase1\probe\phase3_direction_transforms.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite125_layer_window_directions.yaml
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python .\experiment\phase1\probe\phase3_logit_cell_analysis.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite125_layer_window_logit_cell_analysis.yaml
  decisions:
  - Prioritize L24 for generated replay if testing this composite family.
  - Do not treat L27 as a candidate for calibrated abstention steering.
  signals:
    l24_known_refused_delta: -0.025
    l24_unknown_wrong_delta: 0.0599
    l25_known_refused_delta: -0.0221
    l25_unknown_wrong_delta: 0.0157
    l26_known_refused_delta: -0.0136
    l26_unknown_wrong_delta: 0.0277
    l27_known_refused_delta: -0.0281
    l27_unknown_wrong_delta: -0.015
- id: 024-kto-composite-generation-replay
  at: '2026-06-20T12:36:00Z'
  kind: result
  title: KTO Composite Does Not Pass Behavioral Replay
  summary: 'Ran bounded generated-answer replay for the best current L24 1:1.25 KTO
    composite on the same 64 fixed SelfAware rows. The logit pattern did not translate
    into a useful behavioral intervention. Known over-refusal did not improve. Unknown
    refusal rate dropped from 84.38% to 81.25%, and answer-on-unknown rose from 15.62%
    to 18.75%. Only three rows changed: one unknown answered-wrong row improved by
    switching to refusal, but two rows worsened by switching from refusal to non-refusal,
    including an unknown-refused row that became `Yes`.

    '
  evidence:
  - archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay.yaml
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay/kto_h_lora_l24_composite_known1_unknown125_window_normed/generation/run_20260620T123358Z/metrics.json
  - experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/causal_pilots/phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay/kto_h_lora_l24_composite_known1_unknown125_window_normed/generation/run_20260620T123358Z/scored_rows.jsonl
  commands:
  - python .\experiment\phase1\probe\phase3_causal_pilot_sweep.py --config .\archive\experiment\phase1\probe\config\selfaware-calibrated-expression-kto-panels\phase3_selfaware_calibrated_expression_kto_composite125_l24_generation_replay.yaml
    --mode-filter generation --write-plan --materialize-configs --execute --allow-generation
  decisions:
  - Do not promote the L24 1:1.25 composite as a steering intervention.
  - Keep it as evidence that linear blends can tune logit-cell tradeoffs but may still
    fail generated behavior.
  - Next direction should emphasize richer behavior-conditioned objectives or generation-time
    scoring, not larger coefficients on this vector.
  signals:
    baseline_unknown_refusal_rate: 84.38
    intervention_unknown_refusal_rate: 81.25
    baseline_answer_on_unknown_rate: 15.62
    intervention_answer_on_unknown_rate: 18.75
    baseline_over_refusal_on_known: 53.12
    intervention_over_refusal_on_known: 53.12
    refusal_changed_rows: 3
    helpful_unknown_wrong_to_refusal_flips: 1
    harmful_refusal_to_answer_flips: 2
next_steps:
- Explore constrained subspace controls or learned low-rank steering objectives; simple
  single-axis, same-layer composite, and two-hook KTO steering are active but behaviorally
  unsafe.
- Treat gold KTO L28/L36 behavior axes as useful diagnostic components, not as a calibrated
  steering recipe.
- Consider sequence-level answer probability or richer generated-answer diagnostics
  before further activation steering; first-token and refusal-opener movement were
  not enough.
- For DPO, run a nearby-layer/source-window diagnostic or deprioritize it as non-local
  because wrong-layer tracks source addition closely.
- Repeat the behavior-axis layer-window diagnostic on the true original base runtime
  once the adapterless original-base extraction path is available.
- Consider a compact cross-model replication on seed 2/3 SFT and SFT->KTO/DPO once
  the current seed-eval provenance is settled.
- Replay DPO f49 row-level top-k tokens to see whether addition suppresses refusal
  or shifts to answer-like tokens.
- Add sequence-probability or row-specific answer-token slices before scaling behavior-feature
  diagnostics.
- Test behavior features in same-runtime adapterless SFT mode to separate adapter-native
  effects from direction effects.
- Use `phase3_logit_cell_sign_score.py` to rank cell-level logit candidates against
  explicit four-cell goals before selecting any future replay candidate.
- Run the prepared orthogonalized KTO L24-L26 logit sweep only after explicit live
  Docker/GPU approval.
legacy_session:
  id: phase3-behavior-conditioned-sae-features
  path: docs/sessions/0011 - phase3-behavior-conditioned-sae-features.md
---
# 0011 - Phase 3 Behavior-Conditioned SAE Features

## Status

Active. This session adds a behavior-conditioned feature search, a bounded
causal smoke, a layerwise behavior-axis scan, a same-runtime behavior-axis
logit diagnostic, a nearby-layer known-panel follow-up, a layer-window
source-axis diagnostic, a known-panel answer-token follow-up, and a
gold-backed first-token answer slice with scaled follow-up. It does not
establish a clean feature mechanism.

## Plain-Language Finding

We found candidate axes, not a single tidy epistemic-humility feature.

The behavior screen can pick out features that correlate with refusal,
low-confidence answers, and over-refusal. But the geometry says those features
are mostly separate from each other and only weakly aligned with the broader
known/unknown subspace. The causal smoke reinforces that: DPO `f49` moves
refusal logits strongly, but in the opposite sign from the behavior label;
KTO `f12` and `f16` move refusal in the expected direction, but the effects are
small; DPO `f125` is not convincing because the wrong-layer control is stronger
than the source-layer intervention.

The layerwise scan strengthens the distributed-subspace reading. Broad
unknown-refusal vs known-correct directions are easy to separate almost
everywhere after the early layers, but the subtler "unknown refused vs unknown
answered" and confidence contrasts peak later and are not confined to one
single layer. The same-runtime logit diagnostic adds that KTO and SFT-derived
axes can move refusal probability, especially under subtraction, but wrong-layer
controls remain competitive. So the working hypothesis remains: epistemic
humility is probably represented as a distributed control/subspace with several
content- and behavior-conditioned axes, not one sparse local knob.

The nearby-layer known-panel follow-up sharpened this: SFT known-overrefusal
does move strongly on known rows, but the same vector applied at earlier layers
is stronger than source-layer application. KTO shows a similar source-minus-2
advantage. That makes the "localized L25/L27 feature" story weaker and the
"behavior direction threads through a layer window" story stronger. The
layer-window source-axis follow-up supports that reading: the strongest SFT
known-overrefusal addition appears at layer 24, not layer 27, and KTO
within-unknown subtraction is strongest around layers 24-25 rather than only at
the late scan peak.

The answer-token follow-up exposed an important limitation: the SelfAware
"known" rows we used for this panel do not include gold aliases, so we cannot
score movement toward correct answers from this run. The raw top-k behavior is
still suggestive: subtracting the SFT known-overrefusal axis often reduces the
`I` refusal opener and reveals plausible answer starts, but a gold-backed
TriviaQA/Cheng panel is needed before making a correctness claim.

On the older gold-backed changed-row slice, KTO `h_lora` subtraction gives the
cleanest tiny-slice signal so far: refusal-openers go down while answer-alias
first-token probability goes up. DPO `delta` is not clean: source addition can
lower refusal while also lowering answer probability, and wrong-layer controls
are competitive. This makes KTO the more promising target for the next scaled
answer-token diagnostic, while DPO still looks entangled or unstable. However,
the first scaled 16-row pass weakened the KTO story: refusal probability still
dropped under KTO subtraction, but answer-alias probability did not rise. So the
current evidence supports "refusal/style modulation" more than "correct-answer
recovery." The known/unknown split sharpens this: KTO subtraction lowered
refusal mostly on unknown rows, but answer-start probability also fell on those
same unknown rows. The only answer-start lift appeared on known rows, where
refusal was already less central. That is useful steering evidence, but not yet
the behavior we want. A larger 64-row panel gives a slightly more favorable but
still guarded KTO read: on unknown rows, KTO subtraction lowers refusal and
raises answer-start probability on average, but the effect is small and random
matched-norm control is close enough that source specificity is not established.
DPO addition moves unknown rows more strongly, but wrong-layer tracks it too
closely. The practical takeaway is that the next test should target control
separation and behavior-specific row selection, not just more aggregate rows.
The fixed unknown-row coefficient sweep gives KTO the better mechanistic shape:
source subtraction and wrong-layer move in opposite directions, while DPO source
and wrong-layer remain nearly parallel. KTO still has a random-control caveat,
because random matched-norm can also lower refusal, but source subtraction is
more favorable on answer-start probability. So KTO remains our best next lead,
with the claim limited to "candidate source direction" rather than mechanism.
The follow-up random-seed panel makes that lead stronger: KTO source subtraction
beats the five-seed random mean on both refusal reduction and answer-start lift,
and wrong-layer still moves the wrong way. The claim is still narrow: we are
seeing next-token answer-start steering on a fixed unknown-row panel, not
validated generated-answer correctness. The generated-answer replay is the
harder behavioral gate, and KTO does not pass it yet: it answers one extra
unknown row but that new answer is wrong, while exact correctness stays flat.
That is a useful negative result. It suggests this direction can loosen refusal
without supplying the missing knowledge, which is exactly the failure mode we
need to avoid.

## Checkpoint 025 - Gold-Backed KTO Behavior Panel

Question: can we move from broad refusal axes to gold-backed calibrated
expression cells where generated correctness is known?

Work completed:

- Added `phase3_gold_behavior_panel.py` to materialize behavior-cell rows from
  scored baseline generations.
- Added `rows_path` support to behavior-axis scan/export so generated behavior
  labels can be supplied without moving hidden-state shards.
- Ran full SFT->KTO baseline generation on the 256-row gold-backed extraction:
  `phase3_gold_kto_baseline_generation_replay`.
- Materialized `phase3_gold_kto_behavior_panel`.
- Ran `phase3_gold_kto_calibrated_expression_axis_scan`.
- Exported six gold KTO directions and ran a bounded two-axis logit diagnostic
  on the 28-row balanced four-cell panel.

Baseline generated-answer metrics:

- Known answer correctness: `81.25%`.
- Known answer retention: `94.53%`.
- Known over-refusal: `5.47%`.
- Unknown refusal: `84.38%`.
- Unknown answer rate: `15.62%`.
- Truthful rate: `82.81%`.

Behavior cells:

- `known_refused`: 7.
- `known_correct_answered`: 104.
- `known_answered_wrong`: 17.
- `unknown_refused`: 108.
- `unknown_answered_wrong`: 16.
- `unknown_answered_correct`: 4.

Axis scan read:

- Known over-refusal vs known-correct is very separable late, especially
  `h_lora` L36 (`d ~= 5.02`, AUC `~0.997`) and L32.
- Unknown-wrong vs unknown-refused is separable but weaker, with `h_lora`
  around L25-L28 and best listed L27 (`d ~= 2.57`, AUC `~0.947`).
- Known-wrong vs known-correct is strongest late, especially `h_lora` L34
  (`d ~= 4.54`, AUC `~1.0`).
- This looks like multiple behavior axes across a layer window, not one
  epistemic-humility knob.

Logit diagnostic read:

- Known-overrefusal L36 source addition reduces refusal probability on
  known-refused rows, but also reduces refusal on unknown-refused rows.
- Unknown-wrong L27 source subtraction raises refusal probability on
  unknown-wrong rows, but also raises refusal on known-correct rows.
- Wrong-layer controls are competitive or stronger, especially for the
  unknown-wrong axis.
- Answer-alias probability movement is tiny compared with refusal movement.

Decision:

- Do not promote either single gold-backed KTO axis to generated replay yet.
- Next highest-ROI direction is a richer subspace/composite search using the
  gold behavior cells, with explicit controls for paired desired behaviors.

Gotcha captured:

- A wrong-layer offset of `+1` on hidden-state L36 maps past the final decoder
  block in this 36-block model. Bound wrong-layer offsets near final layers.

## Checkpoint 026 - Gold Same-Layer Composite Grid

Question: can same-layer linear combinations of gold-backed KTO damage axes
repair both damaged cells at once?

Work completed:

- Exported same-layer `h_lora` axes at L27, L28, L30, and L36 for:
  `known_refused_vs_known_correct_answered` and
  `unknown_answered_wrong_vs_unknown_refused`.
- Built six same-layer composites:
  `known_refused_vs_correct - alpha * unknown_wrong_vs_refused`, with
  `alpha` in `{0.25, 0.5}` at layers 27, 28, and 36.
- Ran the composite logit sweep on the 28-row balanced gold four-cell panel.
- Ran a follow-up same-layer single-axis sign map for the missing L27/L28/L36
  axes to explain the composite behavior.

Composite result:

- No composite improved the target pattern.
- L27/L28 composites increased refusal on `unknown_answered_wrong`, which is
  desired, but also increased refusal on `known_refused` and
  `known_correct_answered`, which is not a repair.
- L36 composites reduced refusal on `known_refused`, but lowered desired
  `unknown_refused` refusal and did not repair `unknown_answered_wrong`.
- Answer-alias probability movement was tiny relative to refusal movement.

Sign-map result:

- L27/L28 known-overrefusal axes under subtraction reduce refusal on
  `known_refused`, but also reduce refusal on `unknown_refused` and
  `unknown_answered_wrong`.
- L27/L28 unknown-wrong axes under subtraction increase refusal on
  `unknown_answered_wrong`, but also increase refusal on `known_correct_answered`.
- L36 unknown-wrong is weaker; subtraction modestly increases refusal on
  `unknown_answered_wrong`, but still lowers `unknown_refused` refusal.

Interpretation:

- The problem is not just an unlucky weight ratio. The same-layer axes have
  incompatible causal signs for calibrated expression.
- Current evidence supports a distributed, multi-layer control hypothesis more
  than a same-layer linear combination hypothesis.

Decision:

- Do not run generated-answer replay for the same-layer composites.
- Next highest-ROI experimental path is a dedicated multi-layer intervention or
  constrained subspace method that can apply different repairs at different
  layers while gating against known-correct and unknown-refused damage.

## Checkpoint 027 - Gold Multi-Layer KTO Diagnostic

Question: can applying different repairs at different layers solve the
same-layer sign conflict?

Work completed:

- Added reusable multi-layer support to `phase3_causal_pilot_runner.py`.
  Candidates can now declare `multi_layer_components`; the runner loads each
  component vector, applies its signed weight, and installs one final-token hook
  per component.
- Added dry-run validation for component manifests, vector hashes, roles,
  layers, tensor keys, and direction files.
- Added a three-candidate gold KTO multi-layer sweep:
  L36 known-overrefusal repair plus L28 unknown-wrong repair at weights
  `-0.10`, `-0.25`, and `-0.50`.
- Ran the Docker logit diagnostic on the fixed 28-row gold four-cell panel and
  analyzed refusal-openers and answer-aliases by behavior cell.

Validation:

- Focused tests: `61 passed`.
- Causal runner/sweep/dry-run tests: `75 passed`.
- Live Docker jobs: `3/3` completed.
- Hook telemetry matched expectation: two hooks per row, `56` applications per
  28-row candidate.

Result:

- Weight `-0.10`: known-refused refusal down `-0.077`, but unknown-refused
  refusal also down `-0.097`; unknown-wrong refusal did not improve (`-0.007`).
- Weight `-0.25`: known-refused refusal down `-0.055`, unknown-wrong refusal
  slightly up `+0.011`, but unknown-refused refusal still down `-0.086` and
  known-correct refusal up `+0.019`.
- Weight `-0.50`: unknown-wrong refusal up `+0.062`, but known-correct refusal
  up `+0.041`, unknown-refused refusal down `-0.081`, and known-refused repair
  weakened to `-0.022`.
- Answer-alias probability movement was tiny across all cells.
- Wrong-layer controls remained competitive for some cells, especially
  unknown-wrong movement at the highest L28 weight.

Interpretation:

- Multi-layer intervention plumbing works, but this two-hook recipe is still
  behaviorally unsafe.
- The result supports the idea that calibrated expression is distributed across
  multiple axes/layers, but it also shows that simply adding separate repair
  axes is not enough.
- Next highest-ROI path is a constrained objective or learned low-rank
  direction that explicitly optimizes the four behavior-cell inequalities:
  lower known-refused refusal, raise unknown-wrong refusal, preserve
  known-correct answering, and preserve unknown-refused abstention.

## Checkpoint 028 - KTO Cell Sign Scoring

Question: among the existing SelfAware KTO logit-cell runs, which candidate
best satisfies the four calibrated-expression sign goals, and does that change
the replay interpretation?

Work completed:

- Added `phase3_logit_cell_sign_score.py` to rank
  `cell_logit_summary.csv` rows against declared behavior-cell sign goals.
- Added `phase3_selfaware_kto_cell_sign_score.yaml` covering the current KTO
  single-axis, equal-composite, composite-grid, and L24-L27 composite125 layer
  window summaries.
- Added `logit-cell-sign-score` to the mech-interp skill CLI.
- Ran the scorer over 100 candidate/control groups.
- Re-inspected the existing L24 1:1.25 generated replay rows.

Validation:

- `python -m pytest experiment/phase1/probe/tests/test_phase3_logit_cell_sign_score.py .skills/mech-interp-runner/tests/test_phase3_cli.py -q`
  -> `6 passed`.
- `python -m py_compile experiment/phase1/probe/phase3_logit_cell_sign_score.py .skills/mech-interp-runner/scripts/phase3_cli.py`
  -> passed.
- `python bin/sync_skills.py --check` -> in sync.

Scoring result:

- Top overall sign score is the L24 1:1.25 composite wrong-layer control:
  score `0.1034`, all four sign goals passed.
- Best source arm is the same L24 1:1.25 composite under source
  `activation_addition`: score `0.0849`, all four sign goals passed.
- The source arm decreased refusal on `known_refused` rows (`-0.0250`),
  increased refusal on `unknown_answered_wrong` rows (`+0.0599`), kept
  `known_correct_answered` roughly stable (`-0.0055`), and preserved
  `unknown_refused` in the sign-score sense (`+0.0254`).
- L26 source addition is the next clean source arm but weaker: score `0.0413`.
- The fact that the wrong-layer control beats the source arm remains a major
  caveat against source-layer localization.

Replay row check:

- The existing L24 1:1.25 source replay still fails the behavioral gate.
- Refusal state changed on only three rows: one unknown wrong answer (`God`) was
  repaired to refusal, but two unknown-refused rows became non-refusals (`Yes`
  and `I'd rather be captured by pirates`).
- Several other rows only changed refusal wording, not behavior.
- Exact correctness did not change.

Interpretation:

- The sign-score makes the best logit tradeoff reproducible, but it does not
  rescue the candidate as a user-facing steering intervention.
- The next research step should not be "scale this L24 vector." It should be a
  constrained objective or generation-time/sequence-level diagnostic that
  optimizes the four behavior cells directly and rejects candidates that
  increase harmful refusal-to-answer flips.

## Checkpoint 029 - Orthogonalized Window Candidates Prepared

Question: given the negative replay and wrong-layer caveat, is there evidence
that the KTO calibrated-expression axes overlap enough to justify a constrained
subspace test?

Research check:

- Local KG search surfaced the newer refusal-caveat literature: refusal-like
  behavior can involve multiple geometrically distinct directions that collapse
  into similar refusal/over-refusal tradeoffs under linear steering.
- SAE refusal steering notes reinforce that active refusal features can still
  trade off unrelated capability, so feature/axis steering needs output-effect
  and generated-behavior gates.
- The faithful-calibration note supports treating confidence expression,
  token probabilities, hidden states, and sample consistency as distinct
  readouts rather than assuming refusal equals epistemic humility.

Work completed:

- Added `orthogonalize_to` support to `phase3_direction_transforms.py`.
- Added unit tests for orthogonalization and cross-layer rejection.
- Added `phase3_selfaware_calibrated_expression_kto_orthogonalized_window_directions.yaml`.
- Materialized six L24-L26 SelfAware KTO h_lora constrained directions:
  known-repair orthogonalized to unknown-wrong, and unknown-repair
  orthogonalized to known-overrefusal.
- Added hash-pinned candidate and sweep configs for a future logit diagnostic.
- Materialized the sweep plan/configs without execution.

Validation:

- `python -m pytest experiment/phase1/probe/tests/test_phase3_direction_transforms.py -q`
  -> `5 passed`.
- `python -m py_compile experiment/phase1/probe/phase3_direction_transforms.py`
  -> passed.
- `python .skills/mech-interp-runner/scripts/phase3_cli.py causal-sweep --config archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs`
  -> six planned jobs, zero skipped, `executed=false`.

Geometry result:

- L24 removed component fraction: `0.518`.
- L25 removed component fraction: `0.486`.
- L26 removed component fraction: `0.526`.
- This is a meaningful same-layer overlap between known-overrefusal and
  unknown-wrong axes, not a tiny correction.

Interpretation:

- This supports the "coherent but entangled layer band" hypothesis: the axes
  are not identical, but roughly half of each unit-scaled vector lies along the
  paired behavior axis in this L24-L26 window.
- The next live diagnostic should ask whether orthogonalization improves the
  four-cell sign pattern and weakens wrong-layer parity. It should not jump
  directly to generated replay until the logit-cell sign score beats the
  current L24 composite source arm and its controls.

## Checkpoint 030 - Orthogonalized Window Sweep And KG-Ingest Delegation

KG capture status:

- Delegated the interpretability-paper KG ingest path to a subagent while the
  local GPU sweep ran.
- The subagent loaded the repo-local `kg-ingest` skill mirror and validated the
  existing graph, but the required `Workflow` tool is not callable in this
  environment. Therefore, full KG ingest did not complete.
- Prepared ingest payload:
  `C:\Users\Joseph\AppData\Local\Temp\kg_ingest_payload_interpretability_papers.json`.
- Ready local papers in the payload:
  `2602.02132` (`library/notes/2602.02132--more-to-refusal-than-single-direction.md`,
  `library/fulltext/2602.02132.html`) and `2411.11296`
  (`library/notes/2411.11296--steering-refusal-with-sparse-autoencoders.md`,
  `library/fulltext/2411.11296.html`).
- Partial local paper: `2606.03969` has a note but no local fulltext/PDF source.
- Missing local notes/sources for follow-up: `2411.02193` and `2505.20063`.
- Baseline graph validation remained clean:
  `validate_kg_relationships.py --root library` -> `OK 374 graph notes
  validated`; `analyze_kg.py --root library` -> `374` graph notes, `1373`
  typed edges, `0` unresolved targets, `0` legacy edges, `0` orphan graph nodes.

Live sweep:

- Ran the prepared SelfAware KTO h_lora L24-L26 orthogonalized logit diagnostic
  after explicit local GPU approval.
- First attempt failed fast because transformed manifests inherited the source
  contrast. Fixed by adding explicit `contrast:` fields for the conceptual
  transformed contrasts and regenerated directions.
- Retry completed all six live Docker jobs successfully. The append-only
  execution log retains the failed event plus six successful events.
- Added cell-analysis config:
  `phase3_selfaware_calibrated_expression_kto_orthogonalized_window_logit_cell_analysis.yaml`.
- Added sign-score config:
  `phase3_selfaware_kto_orthogonalized_cell_sign_score.yaml`.

Results:

- Cell analysis summarized six runs into 120 behavior-cell rows.
- Sign scoring produced 30 scored arms.
- Best arm: `kto_h_lora_l24_unknown_repair_orthogonal_to_known_overrefusal`
  under `activation_subtraction` at coefficient `50`.
- Best score: `0.0317`, only `2/4` goals passed.
- Desired unknown side moved correctly: unknown-wrong refusal-openers increased
  (`+0.1788`) and unknown-refused refusal-openers were preserved/increased
  (`+0.0797`).
- Known-question protections failed: known-refused refusal-openers increased
  (`+0.0765`) and known-correct refusal-openers increased (`+0.0706`).
- Random matched-norm controls were small but sometimes passed `3/4` goals,
  mostly failing only known-correct preservation.

Interpretation:

- Orthogonalization confirmed meaningful geometric overlap, but it did not
  isolate calibrated expression.
- The constrained unknown-repair direction still behaves like a broad
  refusal-pressure lever: it helps unknown-wrong abstention but worsens
  known-question answering/refusal tradeoffs.
- Do not run generated replay for this candidate unless a later constrained or
  multi-layer score improves the four-cell gate substantially.

## Checkpoint 031 - Gold Multi-Layer Local Artifact Recheck

Why this rerun happened:

- The session/finding notes already recorded the gold-backed KTO multi-layer
  result, but the expected local output root was absent after later cleanup or
  workspace drift.
- Re-ran the smaller three-candidate multi-layer diagnostic to restore local
  provenance and verify that the recorded interpretation still matches the
  actual artifacts.

Run:

- Config:
  `archive/experiment/phase1/probe/config/gold-kto-calibrated-expression-logit-panels/phase3_gold_kto_calibrated_expression_multilayer_logit_sweep.yaml`.
- Candidates: L36 known-overrefusal repair plus L28 unknown-wrong repair with
  L28 weights `-0.10`, `-0.25`, and `-0.50`.
- Live Docker execution completed all three jobs with return code `0`.
- Aggregated refusal-openers and answer-aliases by four gold behavior cells.

Confirmed result:

- The multi-layer path is active but still not a calibrated-expression steering
  win.
- Refusal-opener deltas under source addition:
  - weight `-0.10`: known-refused `-0.0774`, unknown-wrong `-0.0071`,
    known-correct `+0.0088`, unknown-refused `-0.0967`.
  - weight `-0.25`: known-refused `-0.0553`, unknown-wrong `+0.0111`,
    known-correct `+0.0188`, unknown-refused `-0.0857`.
  - weight `-0.50`: known-refused `-0.0218`, unknown-wrong `+0.0616`,
    known-correct `+0.0409`, unknown-refused `-0.0808`.
- Increasing the L28 repair weight improves the desired unknown-wrong refusal
  direction, but it also raises refusal on known-correct rows and still lowers
  desired refusal on unknown-refused rows.
- Answer-alias deltas are tiny (`~0.002` absolute at most), so this is still a
  refusal-start intervention rather than answer recovery.

Decision:

- Do not run generated replay for this two-hook recipe.
- Commit the four source configs for reproducibility; keep generated run
  outputs ignored.

## Checkpoint 032 - Gold KTO Multicell Readout

Question: is calibrated expression better represented as a low-dimensional
behavior-cell subspace than as one refusal/answer axis?

Work completed:

- Added `phase3_multicell_readout.py`, a CPU-only hidden-state readout over
  behavior cells.
- Added a reusable CLI route:
  `python .skills/mech-interp-runner/scripts/phase3_cli.py multicell-readout --config ...`.
- Added `phase3_gold_kto_multicell_readout.yaml` for the gold KTO behavior
  panel.
- Added tests proving the readout can distinguish a rank-2 behavior surface
  that rank-1 cannot.
- Initial unweighted readout mostly learned majority cells, so the readout now
  supports `class_weighting: balanced` with fold-local weighted
  standardization and inverse-frequency ridge training weights.

Run:

- Config: `archive/experiment/phase1/probe/config/gold-kto-calibrated-expression/phase3_gold_kto_multicell_readout.yaml`.
- Input: KTO seed1 gold behavior panel over 256 generated rows.
- Labeled rows used: 235.
- Cell counts: `known_refused=7`, `known_correct_answered=104`,
  `unknown_refused=108`, `unknown_answered_wrong=16`.
- 21 rows were unmatched by the four target cells, mostly non-target behavior
  cells such as known-wrong or unknown-correct.

Result:

- Rank-1 readouts remain weak: best macro recall is about `0.46`.
- Low-rank multicell readouts improve meaningfully:
  - `h_lora` L21 rank 4: macro recall `0.582`, accuracy `0.604`.
  - `delta` L27 rank 8: macro recall `0.575`, accuracy `0.736`.
  - `delta` L25 rank 4: macro recall `0.575`, accuracy `0.638`.
  - `h_base` L22 rank 4: macro recall `0.569`, accuracy `0.604`.
- Full-rank readouts are not best after balanced weighting; the useful signal is
  low-dimensional but not one-dimensional.
- Confusion remains substantial. Example `h_lora` L21 rank 4:
  - known-refused recall `5/7`.
  - known-correct recall `77/104`.
  - unknown-refused recall `54/108`.
  - unknown-wrong recall `6/16`.

Interpretation:

- This supports the multi-dimensional control-surface hypothesis more than a
  single humility knob.
- The readout is not strong enough to export steering directions directly. It
  is screening/localization evidence.
- The biggest practical bottleneck is row balance: the panel has too few
  known-refused and unknown-wrong examples to learn stable rare-cell boundaries.

Next step:

- Build a larger, targeted gold behavior panel that oversamples candidate rows
  likely to produce the rare cells (`known_refused` and
  `unknown_answered_wrong`) before exporting readout-derived directions.

## Checkpoint 033 - Targeted KTO Rare-Cell Gold Panel

Question: can a targeted probe-pool slice produce enough rare generated
behavior cells to make multicell readouts more stable?

Reusable plumbing added:

- `hidden_state_probe.py` now supports `selection.row_keys_file` for
  `source: probe_pool` extraction.
- The exact row-key path validates keys against frozen known/unknown pools,
  rejects duplicates and discard/out-of-frozen rows, and preserves file order.
- Added `phase3_targeted_row_keys.py`, a CPU-only selector that writes exact
  row-key files plus a provenance manifest from frozen split + probe results.
- Added tests for exact hidden-state row-key selection and targeted row-key
  selector behavior.

Targeted row-key panel:

- Config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_rare_cell_row_keys.yaml`.
- Output row keys:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_rare_cell_row_keys.txt`.
- The selector excluded the original 256-row KTO gold extraction.
- Selected `448` rows, balanced `224` known / `224` unknown.
- Heuristic buckets selected:
  - `known_low_confidence_or_refusal=160`.
  - `known_high_confidence_correct=64`.
  - `unknown_answered_wrong_like=160`.
  - `unknown_refusal_like=64`.

Extraction and baseline generation:

- Hidden-state extraction config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/hidden_state_gold_kto_targeted_rare_cells.yaml`.
- Extraction completed in Docker with manifest `status=ok`, `verified=true`.
- Extraction output:
  `experiment/phase1/probe/qwen3-4b-instruct/hidden_states_gold_kto_targeted/extraction__9220ebb266f4`.
- Candidate directions derived with `hidden_state_directions.py`.
- New candidate source:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_candidates.yaml`.
- No-vector baseline generation config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_baseline_generation_replay.yaml`.
- Initial generation launch correctly failed because the inherited template
  readiness check expected `row_count=256`; fixed by overriding
  `row_count=448` and label counts `known=224`, `unknown=224`.
- Generation completed successfully:
  `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_gold_kto_targeted_baseline_generation_replay/sft_kto_targeted_h_lora_l35/generation/run_20260620T194500Z`.

Actual generated behavior cells:

- Behavior panel config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_behavior_panel.yaml`.
- Behavior panel output:
  `experiment/phase1/probe/qwen3-4b-instruct/gold_behavior_panels/phase3_gold_kto_targeted_behavior_panel`.
- Counts:
  - `known_refused=37`.
  - `known_correct_answered=164`.
  - `known_answered_wrong=23`.
  - `unknown_refused=187`.
  - `unknown_answered_wrong=31`.
  - `unknown_answered_correct=6`.
- Compared with the earlier 256-row panel, the targeted slice increased
  `known_refused` from `7` to `37` and `unknown_answered_wrong` from `16` to
  `31`, while preserving large desired-cell pools.

Targeted multicell readout:

- Config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_multicell_readout.yaml`.
- Output:
  `experiment/phase1/probe/qwen3-4b-instruct/multicell_readout/phase3_gold_kto_targeted_multicell_readout`.
- Four-cell labeled rows: `419`; unmatched rows: `29`.
- Cell counts used by the readout:
  `known_refused=37`, `known_correct_answered=164`,
  `unknown_refused=187`, `unknown_answered_wrong=31`.
- Best current readouts:
  - `h_lora` L27 rank 16: macro recall `0.613`, accuracy `0.695`,
    rare-cell recall `known_refused=0.432`,
    `unknown_answered_wrong=0.548`.
  - `delta` L34 rank 16: macro recall `0.595`, accuracy `0.704`.
  - `h_base` L25 rank 16: macro recall `0.576`, accuracy `0.702`.

Interpretation:

- The targeted panel confirmed row balance was a real bottleneck.
- The best readout moved from about `0.58` macro recall on the imbalanced
  panel to about `0.61` on the enriched panel, with notably better
  `unknown_answered_wrong` recall.
- This strengthens the low-dimensional-but-not-rank-1 control-surface
  hypothesis.
- It is still localization/screening evidence, not a steering result.
- The next causal slice should use enriched behavior-cell row-key files and
  test candidate controls against paired desired cells before generated replay.

## Checkpoint 034 - Targeted KTO Simple-Axis Causal Follow-Up

Question: do simple behavior axes from the enriched panel around the best
multicell readout regions produce a calibrated-expression logit control?

Offline axis prep:

- Scan config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-calibrated-expression/phase3_gold_kto_targeted_calibrated_expression_axis_scan.yaml`.
- Direction export config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-calibrated-expression/phase3_gold_kto_targeted_calibrated_expression_axis_directions.yaml`.
- Candidate source:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_calibrated_expression_logit_candidates.yaml`.
- Tested simple axes:
  - `h_lora` L27 known-refused vs known-correct.
  - `h_lora` L27 unknown-wrong vs unknown-refused.
  - `delta` L34 known-refused vs known-correct.
  - `delta` L34 unknown-wrong vs unknown-refused.
- Offline separation stayed strong:
  - `h_lora` L27 known-refused vs known-correct:
    AUC `0.985`, Cohen d `3.223`.
  - `h_lora` L27 unknown-wrong vs unknown-refused:
    AUC `0.962`, Cohen d `2.618`.
  - `delta` L34 known-refused vs known-correct:
    AUC `0.920`, Cohen d `1.999`.
  - `delta` L34 unknown-wrong vs unknown-refused:
    AUC `0.911`, Cohen d `1.946`.

Live diagnostic:

- Sweep config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_calibrated_expression_logit_sweep.yaml`.
- Exact row-key panel:
  `experiment/phase1/probe/qwen3-4b-instruct/gold_behavior_panels/phase3_gold_kto_targeted_behavior_panel/row_keys/calibrated_expression_four_cell_available_row_keys.txt`.
- Rows: `124` total, `31` per target cell.
- Controls: no-vector baseline, source add/subtract, wrong-layer add/subtract,
  random matched norm.
- Coefficients: `25`, `50`.
- All four Docker jobs completed successfully.

Cell-level scoring:

- Refusal cell-analysis config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_calibrated_expression_refusal_logit_cell_analysis.yaml`.
- Answer-alias cell-analysis config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_calibrated_expression_answer_logit_cell_analysis.yaml`.
- Sign-score config:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/phase3_gold_kto_targeted_cell_sign_score.yaml`.
- Top source arm:
  `h_lora` L27 known-overrefusal axis, activation subtraction, coefficient
  `50`.
- Top source-arm score: `0.0908`, `2/4` goals passed.
- Refusal-opener deltas for that arm:
  - `known_refused=-0.4079` (desired).
  - `known_correct_answered=-0.0155` (acceptable preservation).
  - `unknown_answered_wrong=-0.1456` (wrong direction).
  - `unknown_refused=-0.1715` (wrong direction).
- Complementary `h_lora` L27 unknown-wrong axis, activation subtraction,
  coefficient `50`, also passed only `2/4`:
  - `unknown_answered_wrong=+0.3565` (desired).
  - `unknown_refused=+0.0442` (desired preservation).
  - `known_refused=+0.0863` (wrong direction).
  - `known_correct_answered=+0.1856` (wrong direction).
- Delta L34 axes were weaker and showed the same split pattern.
- Answer-alias probability movement stayed small relative to refusal-opener
  movement. The largest source-arm answer-alias lift was about `+0.0185` on
  known-refused rows under `h_lora` L27 known-axis subtraction, while many
  answer-alias effects were near zero or moved the wrong cell.

Interpretation:

- The enriched panel and offline axes are real separability evidence, but simple
  behavior-axis steering still does not satisfy calibrated-expression goals.
- The two main L27 axes behave like complementary levers: one repairs known
  over-refusal while damaging unknown abstention; the other repairs unknown
  under-refusal while increasing known-question refusal pressure.
- No generated replay is warranted for these simple axes.
- The next mech-interp step, if any, should be a true constrained subspace or
  readout-derived intervention rather than more single-axis replay. Otherwise,
  this is a good stopping point for pivoting back to training experiments.
