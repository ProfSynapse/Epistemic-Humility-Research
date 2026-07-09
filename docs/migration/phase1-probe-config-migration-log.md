# Phase 1 Probe Config Migration Log

This log records migration batches after the terrain baseline in
`docs/migration/phase1-probe-config-terrain.md`.

## C005 - Current-Clean GRPO v2 Known-Overrefusal

- Date: 2026-07-09
- Source component: `C005`
- File count: 31
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`
- Owner decision: archive-only historical provenance for the Phase 3 model-variation session; no migrated experiments/<slug> owner was present, and the component was not a reusable shared input.
- Reason: historical exploratory Phase 3 config component with no live code,
  test, or skill references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote the historical session note
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy analysis output roots in the configs. Those paths
    preserve the historical run provenance and will be handled with the broader
    `experiment/phase1/probe/analysis/` archive migration.
- Provenance gap noted:
  - `phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.manifest.json` was referenced by the historical session note and row-key config but was not tracked or present at migration time.
## C008 - Current-Clean GRPO v2 Unknown-Failure

- Date: 2026-07-09
- Source component: `C008`
- File count: 10
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-unknown-failure/`
- Owner decision: archive-only historical provenance for the Phase 3 model-variation session; no migrated `experiments/<slug>` owner was present, and the component was not a reusable shared input.
- Reason: historical exploratory Phase 3 config component with no live code,
  test, or skill references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote the historical session note
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy analysis output roots, extraction dirs, or the
    generated manifest under `experiment/phase1/probe/manifests/`. Those paths
    preserve historical run provenance and will be handled with broader legacy
    artifact archive passes.
- Provenance gaps noted:
  - `phase3_current_clean_grpo_v2_unknown_failure_selfaware_scored_rows.jsonl` was referenced by the historical session note and manifest config but was not tracked or present at migration time.
  - `phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.summary.json` was referenced by the manifest config but was not tracked or present at migration time.
## C020 - SelfAware Full-Delta Logit Diagnostics

- Date: 2026-07-09
- Source component: `C020`
- File count: 10
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-full-delta-logit-diagnostics/`
- Owner decision: archive-only historical provenance for the June 19 Phase 3
  SelfAware stratified-row session; no migrated `experiments/<slug>` owner was
  present, and the component was not a reusable shared input.
- Reason: historical exploratory Phase 3 local logit-diagnostic config component
  with no live code, test, or skill references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote the historical session note
    `docs/sessions/20260619T101926Z-phase-3-selfaware-stratified-row-manifest.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy causal-pilot output roots or extraction artifact
    paths. Those paths preserve historical run provenance and will be handled
    with broader legacy artifact archive passes.
## C002 - Current-Clean Behavior-Axis Directions

- Date: 2026-07-09
- Source component: `C002`
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-behavior-axis-directions/`
- Owner decision: archive-only historical provenance for the Phase 3
  model-variation and GRPO v2 known-overrefusal work; no migrated
  `experiments/<slug>` owner was present, and the component was not a reusable
  shared input at migration time.
- Reason: historical exploratory Phase 3 behavior-axis scan/direction-export
  component with only historical note references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote historical references in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md` and
    `archive/notes/experiments/mech-interp-model-variation-panel.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy extraction dirs, row overlays, or analysis output
    roots. Those paths preserve historical run provenance and will be handled
    with broader legacy artifact archive passes.
## C025 - SelfAware Subspace Logit Diagnostics

- Date: 2026-07-09
- Source component: `C025`
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-subspace-logit-diagnostics/`
- Owner decision: archive-only historical provenance for the June 19 Phase 3 SAE
  smoke/plumbing session; no migrated `experiments/<slug>` owner was present,
  and the component was not a reusable shared input at migration time.
- Reason: historical exploratory Phase 3 SAE/subspace local logit-diagnostic
  component with only historical session-note references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote the historical session note
    `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy causal-pilot output roots, extraction dirs, SAE output
    paths, or live runner-template references. Those paths preserve historical
    run provenance or belong to later live-default migration passes.

## C012 - Current-Clean KTO Unknown-Failure

- Date: 2026-07-09
- Source component: `C012`
- File count: 4
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-kto-unknown-failure/`
- Owner decision: archive-only historical provenance for the Phase 3
  model-variation KTO prompt-matched arm; no migrated `experiments/<slug>`
  owner was present, and the component was not a reusable shared input at
  migration time.
- Reason: historical exploratory Phase 3 KTO generated-replay component with
  only historical session-note references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote moved-file references and generated-output references in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy extraction dirs, analysis output roots, generated
    manifest paths under `experiment/phase1/probe/manifests/`, or sibling KTO
    direction/readout configs that belong to later component batches. Those
    paths preserve historical run provenance or remain live until their own
    migration pass.
- Provenance gaps noted:
  - `phase3_current_clean_kto_unknown_failure_selfaware_scored_rows.jsonl` was
    referenced by the manifest config but was not tracked or present at
    migration time.
  - `phase3_current_clean_kto_unknown_failure_selfaware_manifest.summary.json`
    was referenced by the manifest config and historical session note but was
    not tracked or present at migration time.

## C003 - Current-Clean DPO-GRPO Unknown-Failure

- Date: 2026-07-09
- Source component: `C003`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `experiments/grpo-centered-stacking/artifacts/configs/current-clean-dpo-grpo-unknown-failure/`
- Owner decision: moved into `experiments/grpo-centered-stacking` because
  `AMENDMENT.md` governs the Amendment F `clean_sft_dpo_grpo` arm and this
  component is a downstream Phase 3 panel artifact for that arm.
- Reason: owner experiment exists; the files are not reusable shared defaults
  and should travel with the Amendment F provenance rather than the generic
  archive.
- Reference updates:
  - Rewrote component-internal config path references to the experiment artifact
    path.
  - Rewrote moved-file references and generated-output references in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Added the moved config files to `experiments/grpo-centered-stacking/experiment.yaml`
    `inputs`.
- Non-goals:
  - Did not move sibling hidden-state extraction, behavior-axis, or multicell
    configs; they are separate terrain components and will be reviewed in their
    own batches.
  - Did not rewrite generated manifest paths under `experiment/phase1/probe/manifests/`
    or legacy extraction/analysis artifact paths.
- Provenance gaps noted:
  - `phase3_current_clean_dpo_grpo_unknown_failure_selfaware_scored_rows.jsonl`
    was referenced by the manifest config but was not tracked or present at
    migration time.
  - `phase3_current_clean_dpo_grpo_unknown_failure_selfaware_manifest.summary.json`
    was referenced by the manifest config and historical session note but was
    not tracked or present at migration time.

## C004 - Current-Clean GRPO-DPO Unknown-Failure

- Date: 2026-07-09
- Source component: `C004`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `experiments/grpo-centered-stacking/artifacts/configs/current-clean-grpo-dpo-unknown-failure/`
- Owner decision: moved into `experiments/grpo-centered-stacking` because
  `AMENDMENT.md` governs the Amendment F `clean_sft_grpo_dpo` arm and this
  component is a downstream Phase 3 panel artifact for that arm.
- Reason: owner experiment exists; the files are not reusable shared defaults
  and should travel with the Amendment F provenance rather than the generic
  archive.
- Reference updates:
  - Rewrote component-internal config path references to the experiment artifact
    path.
  - Rewrote moved-file references and generated-output references in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Added the moved config files to `experiments/grpo-centered-stacking/experiment.yaml`
    `inputs`.
- Non-goals:
  - Did not move sibling hidden-state extraction, behavior-axis, or multicell
    configs; they are separate terrain components and will be reviewed in their
    own batches.
  - Did not rewrite generated manifest paths under `experiment/phase1/probe/manifests/`
    or legacy extraction/analysis artifact paths.
- Provenance gaps noted:
  - `phase3_current_clean_grpo_dpo_unknown_failure_selfaware_scored_rows.jsonl`
    was referenced by the manifest config but was not tracked or present at
    migration time.
  - `phase3_current_clean_grpo_dpo_unknown_failure_selfaware_manifest.summary.json`
    was referenced by the manifest config and historical session note but was
    not tracked or present at migration time.

## C010 - Current-Clean KTO-GRPO Unknown-Failure

- Date: 2026-07-09
- Source component: `C010`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `experiments/grpo-centered-stacking/artifacts/configs/current-clean-kto-grpo-unknown-failure/`
- Owner decision: moved into `experiments/grpo-centered-stacking` because
  `AMENDMENT.md` governs the Amendment F `clean_sft_kto_grpo` arm and this
  component is a downstream Phase 3 panel artifact for that arm.
- Reason: owner experiment exists; the files are not reusable shared defaults
  and should travel with the Amendment F provenance rather than the generic
  archive.
- Reference updates:
  - Rewrote component-internal config path references to the experiment artifact
    path.
  - Rewrote moved-file command/reference paths in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Added the moved config files to `experiments/grpo-centered-stacking/experiment.yaml`
    `inputs`.
- Non-goals:
  - Did not move sibling hidden-state extraction, behavior-axis, or multicell
    configs; they are separate terrain components and will be reviewed in their
    own batches.
  - Did not rewrite generated manifest paths under `experiment/phase1/probe/manifests/`
    or legacy extraction/analysis artifact paths.
- Provenance gaps noted:
  - `phase3_current_clean_kto_grpo_unknown_failure_selfaware_scored_rows.jsonl`
    was referenced by the manifest config but was not tracked or present at
    migration time.
  - `phase3_current_clean_kto_grpo_unknown_failure_selfaware_manifest.summary.json`
    was referenced by the manifest config but was not tracked or present at
    migration time.
## C007/C009 - Current-Clean GRPO v2 Unknown-Failure Axis And Direction Configs

- Date: 2026-07-09
- Source components: `C007`, `C009`
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-unknown-failure/`
- Owner decision: archive-only historical provenance for the Phase 3 GRPO v2
  unknown-failure slice. No migrated `experiments/<slug>` owner was present, and
  these files are not reusable shared defaults.
- Reason: these configs are the generic-prompt and prompt-matched behavior-axis
  scan/direction-export producers for the already archived GRPO v2
  unknown-failure replay/logit candidate configs.
- Reference updates:
  - Rewrote component-internal `source_scan_config` references to the archive
    path.
  - Rewrote moved-file references and command paths in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Updated the destination archive README to list the added batches.
- Non-goals:
  - Did not move sibling hidden-state extraction, multicell readout,
    constrained-repair transform, or head-localization configs; those remain
    separate terrain components for later review.
  - Did not rewrite extraction dirs or analysis output roots. Those paths
    preserve historical run provenance and will be handled in broader artifact
    archive passes.
## C006 - Current-Clean GRPO v2 L26 Repair Multi-Protect Axis Configs

- Date: 2026-07-09
- Source component: `C006`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`
- Owner decision: archive-only historical provenance for the Phase 3 GRPO v2
  known-overrefusal repair/protection slice. No migrated `experiments/<slug>`
  owner was present, and these files are not reusable shared defaults.
- Reason: these configs produce the same-layer L26 known-repair, broad
  unknown-refusal protection, and known-wrong protection axes for the already
  archived GRPO v2 double-orthogonalized known-overrefusal replay configs.
- Reference updates:
  - Rewrote component-internal `source_scan_config` references to the archive
    path.
  - Rewrote moved-file references and command paths in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Updated the destination archive README to list the added batch.
- Non-goals:
  - Did not move sibling transform configs or replay artifacts that remain in
    separate terrain components; those will be reviewed in their own batches.
  - Did not rewrite extraction dirs or analysis output roots. Those paths
    preserve historical run provenance and will be handled in broader artifact
    archive passes.
## C011 - Current-Clean KTO Unknown-Failure Axis Configs

- Date: 2026-07-09
- Source component: `C011`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-kto-unknown-failure/`
- Owner decision: archive-only historical provenance for the Phase 3 KTO
  unknown-failure generated replay slice. No migrated `experiments/<slug>` owner
  was present, and these files are not reusable shared defaults.
- Reason: these configs produce the prompt-matched KTO unknown-failure
  behavior-axis scan and direction export for the already archived replay
  candidate/generation configs.
- Reference updates:
  - Rewrote component-internal `source_scan_config` references to the archive
    path.
  - Rewrote moved-file references and command paths in
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
  - Updated the destination archive README to list the added batch.
- Non-goals:
  - Did not move the sibling multicell readout config; it is a separate terrain
    component for later review.
  - Did not rewrite extraction dirs or analysis output roots. Those paths
    preserve historical run provenance and will be handled in broader artifact
    archive passes.
## C013/C014 - Gold KTO Calibrated-Expression Axis Configs

- Date: 2026-07-09
- Source components: `C013`, `C014`
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destinations:
  - `archive/experiment/phase1/probe/config/gold-kto-calibrated-expression/`
  - `archive/experiment/phase1/probe/config/gold-kto-targeted-calibrated-expression/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  gold-backed KTO calibrated-expression screening work. No migrated
  `experiments/<slug>` owner was present, and these files are not reusable shared
  defaults.
- Reason: these configs are axis-scan and direction-export producers for the
  gold-backed and targeted gold-backed KTO calibrated-expression slices; their
  downstream configs consume generated direction artifacts, not the config files
  directly.
- Reference updates:
  - Rewrote component-internal `source_scan_config` references to the archive
    paths.
  - Rewrote moved-file references in
    `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`.
  - Added README files to both destination archive folders.
- Non-goals:
  - Did not move downstream logit-candidate, logit-sweep, composite, multilayer,
    or cell-analysis configs; those are separate terrain components for later
    review.
  - Did not rewrite legacy output roots under `experiment/phase1/probe/qwen3-4b-instruct/`.
    Those paths preserve historical run provenance and will be handled in broader
    artifact archive passes.
## C021-C024 - SelfAware SAE Feature Logit-Diagnostic Configs

- Date: 2026-07-09
- Source components: `C021`, `C022`, `C023`, `C024`
- File count: 8
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-sae-feature-logit-diagnostics/`
- Owner decision: archive-only historical provenance for the June 19/20 Phase 3
  SAE feature diagnostic work. No migrated `experiments/<slug>` owner was
  present, and these files are not reusable shared defaults.
- Reason: these are diagnostic+sweep pairs for SelfAware SAE-feature causal-smoke
  / logit-diagnostic work, with only historical session-note references and
  component-internal sweep-to-candidate links.
- Reference updates:
  - Rewrote component-internal `runner_config` and `candidate_source_config`
    references to the archive path.
  - Rewrote moved-file references and command paths in
    `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md` and
    `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move SAE feature extraction/direction output roots or causal-pilot
    outputs under `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/`.
  - Did not move upstream SAE analysis/direction configs that are separate
    terrain components for later review.
