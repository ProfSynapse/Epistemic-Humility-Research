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

## C015-C018 - SelfAware Behavior-Axis Configs

- Date: 2026-07-09
- Source components: `C015`, `C016`, `C017`, `C018`
- File count: 10
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-behavior-axis/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  SelfAware behavior-axis work. No migrated `experiments/<slug>` owner was
  present, and these files are not reusable shared defaults.
- Reason: these configs form a historical scan -> direction-export -> exploratory
  local logit-diagnostic chain for SelfAware behavior axes, with session-note
  references and component-internal config links but no active experiment owner.
- Reference updates:
  - Rewrote component-internal `source_scan_config`, `runner_config`, and
    `candidate_source_config` references to the archive path.
  - Rewrote moved-config references and command paths in
    `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`.
  - Rewrote the moved scan-config reference in
    `archive/notes/experiments/mech-interp-model-variation-panel.md`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move scan, direction, or causal-pilot output roots under
    `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/`.
  - Did not move downstream calibrated-expression geometry configs that reference
    generated behavior-axis direction manifests; those belong to separate terrain
    components for later review.
## C019 - SelfAware Calibrated-Expression Axis Configs

- Date: 2026-07-09
- Source component: `C019`
- File count: 3
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-calibrated-expression-axis/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  SelfAware calibrated-expression axis work. No migrated `experiments/<slug>`
  owner was present, and these files are not reusable shared defaults.
- Reason: these configs form a historical calibrated-expression scan ->
  direction-export chain. Downstream files reference generated direction manifests,
  not these config files directly.
- Reference updates:
  - Rewrote component-internal `source_scan_config` references to the archive path.
  - Rewrote moved-config references and command paths in
    `docs/sessions/20260620T010500Z-phase3-behavior-conditioned-sae-features.md`.
  - Rewrote the moved scan-config reference in
    `archive/notes/experiments/mech-interp-model-variation-panel.md`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move scan or direction output roots under
    `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/`.
  - Did not move downstream calibrated-expression geometry, composite, candidate,
    or logit configs; those are separate terrain components for later review.
## C026 - Sycophancy Answer Behavior-Axis Configs

- Date: 2026-07-09
- Source component: `C026`
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/sycophancy-answer-behavior-axis/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  answer-sycophancy behavior-axis work. No migrated `experiments/<slug>` owner
  was present, and these files are not reusable shared defaults.
- Reason: these configs form a historical answer-sycophancy scan ->
  direction-export pair. Downstream files reference generated direction manifests,
  not these config files directly.
- Reference updates:
  - Rewrote the direction config's `source_scan_config` reference to the archive path.
  - Rewrote moved-config references and command paths in
    `docs/sessions/20260620T145500Z-sycophancy-helpfulness-probe.md`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move scan or direction output roots under
    `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer/`.
  - Did not move downstream answer-sycophancy candidate, logit, or replay configs;
    those are separate terrain components for later review.
## C001a - Causal-Pilot Core Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 3
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/causal-pilot-core/`
- Owner decision: archive-only historical provenance for the legacy Phase 3
  causal-pilot runner template, full candidate inventory, and local sweep plan.
  These remain referenced by historical sweep configs and procedural runbook text,
  but are not the home for new experiment instruments.
- Reason: these files are the dependency root for the remaining mixed C001 sweep
  configs. Moving them first lets downstream historical configs point at the
  archived runner/candidate templates before those downstream panels are split
  into their own archive folders.
- Reference updates:
  - Rewrote `runner_config` and `candidate_source_config` references across
    historical configs, docs, and skill references to the archive path.
  - Updated the canonical `.skills/experiment-runner/reference/phase3-causal-pilot-sweeps.md`
    runbook path references; mirrors are regenerated by the skill sync workflow.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move downstream gold, SelfAware, or sycophancy panel configs in this
    batch; those remain separate C001 sub-batches.
  - Did not move generated causal-pilot outputs under `experiment/phase1/probe/`.
## C001b - Sycophancy Answer Logit/Replay Panel Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/sycophancy-answer-logit-panels/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  answer-sycophancy same-condition logit diagnostic and KTO wrong-hint replay
  work. No migrated `experiments/<slug>` owner was present, and these files are
  not reusable shared defaults.
- Reason: these files form a bounded downstream panel: fixed row keys,
  intervention candidates, one logit sweep, and one targeted generation replay.
- Reference updates:
  - Rewrote `candidate_source_config` and `row_keys_file` references to the
    archive path.
  - Rewrote moved-config references and command paths in
    `docs/sessions/20260620T145500Z-sycophancy-helpfulness-probe.md`.
  - Retained references to generated output roots under `experiment/phase1/probe/`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated causal-pilot outputs under
    `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer/`.
## C001c - SelfAware Calibrated-Expression KTO Panel Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 12
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-calibrated-expression-kto-panels/`
- Owner decision: archive-only historical provenance for the June 20 Phase 3
  SelfAware KTO calibrated-expression logit/replay panel work. No migrated
  `experiments/<slug>` owner was present, and these files are not reusable shared
  defaults.
- Reason: these files form a bounded downstream panel around the fixed 64-row
  SelfAware behavior-cell set: candidate files, logit sweeps, composite/grid and
  orthogonalized variants, and one bounded generation replay.
- Reference updates:
  - Rewrote `candidate_source_config` and `row_keys_file` references to the
    archive path.
  - Rewrote moved-config references and command paths in historical docs/session
    notes found by exact path search.
  - Retained generated direction/output roots under `experiment/phase1/probe/`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated behavior-axis, direction-transform, causal-pilot, or
    generation outputs under `experiment/phase1/probe/`.
## C001d - Gold-Answer KTO Panel Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 6
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/gold-answer-kto-panels/`
- Owner decision: archive-only historical provenance for gold-backed KTO
  answer-start and generated-answer diagnostic work. No migrated
  `experiments/<slug>` owner was present, and these files are not reusable shared
  defaults.
- Reason: these files form a bounded downstream panel around gold-backed first
  token, fixed unknown-row, random-seed, baseline generation, and KTO unknown
  generation replay diagnostics.
- Reference updates:
  - Rewrote moved-config references and command paths in historical docs/session
    notes found by exact path search.
  - Retained generated output roots under `experiment/phase1/probe/`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated behavior panels or causal-pilot outputs under
    `experiment/phase1/probe/qwen3-4b-instruct/`.
## C001e - Gold-KTO Calibrated-Expression Logit Panel Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 8
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/gold-kto-calibrated-expression-logit-panels/`
- Owner decision: archive-only historical provenance for gold-backed KTO
  calibrated-expression simple, composite, same-layer, and multilayer logit
  diagnostic work. No migrated `experiments/<slug>` owner was present, and these
  files are not reusable shared defaults.
- Reason: these files form bounded candidate/sweep pairs around generated
  gold-KTO direction artifacts and the archived causal-pilot core runner.
- Reference updates:
  - Rewrote `candidate_source_config` references to the archive path.
  - Rewrote moved-config references and command paths in historical docs/session
    notes found by exact path search.
  - Retained generated direction/output roots under `experiment/phase1/probe/`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated direction transforms, causal-pilot outputs, or
    cell-analysis configs under `experiment/phase1/probe/qwen3-4b-instruct/`.
## C001f - Gold-KTO Targeted Rare-Cell Panel Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 9
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/`
- Owner decision: archive-only historical provenance for the targeted 448-row
  SFT->KTO gold behavior panel and follow-on targeted calibrated-expression
  logit triage. No migrated `experiments/<slug>` owner was present, and these
  files/artifacts are not reusable shared defaults.
- Reason: these files form a bounded targeted rare-cell pipeline: row-key
  generator artifacts, targeted extraction config, targeted candidates, baseline
  generation replay, and targeted calibrated-expression logit candidate/sweep
  pair.
- Reference updates:
  - Rewrote `candidate_source_config`, `row_keys_file`, and moved-artifact
    references to the archive path.
  - Rewrote moved-config references and command paths in historical docs/session
    notes found by exact path search.
  - Retained generated extraction, behavior-panel, and causal-pilot output roots
    under `experiment/phase1/probe/`.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated hidden-state extractions, behavior panels,
    causal-pilot outputs, or downstream cell-analysis configs under
    `experiment/phase1/probe/qwen3-4b-instruct/`.

## C003a - SelfAware Hidden-State Extraction Manifests

- Date: 2026-07-09
- Source component: `C003` subset
- File count: 13
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-hs/`
- Owner decision: archive-only historical provenance for Phase 3 SelfAware
  frozen-manifest hidden-state extraction prep and launch configs. These are not
  reusable shared defaults; new evidence-producing extraction cells should pin
  experiment-local configs under `experiments/<slug>/`.
- Reason: these files form a bounded SelfAware extraction family spanning SFT,
  SFT->DPO, SFT->KTO, clean-SFT, GRPO v2, GRPO-DPO, DPO-GRPO, KTO, and KTO-GRPO
  surfaces, including prompt-matched rare-cell and attention-head variants.
- Reference updates:
  - Rewrote moved-config references and command paths in historical docs/session
    notes found by exact path search.
  - Updated the GPU-free hidden-state probe unit test fixture path for the
    archived checked-in config.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move the live/default `hidden_state_probe.yaml` runner config.
  - Did not move KUQ or sycophancy hidden-state configs; those require separate
    owner decisions because KUQ belongs with the migrated xdataset transfer
    amendment and sycophancy configs are covered by a dedicated checked-in test.

## C003b - KUQ Cross-Dataset Hidden-State Extraction Config

- Date: 2026-07-09
- Source component: `C003` subset
- File count: 1
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `experiments/xdataset-probe-transfer/`
- Owner decision: experiment-associated instrument config for migrated Amendment
  P (`xdataset-probe-transfer`), not archive-only. The config consumes the
  experiment-local KUQ panel manifest and is the FIT-side hidden-state extraction
  instrument described by the amendment.
- Reason: this file belongs with the evidence-producing experiment that owns the
  KUQ panel artifacts and cross-dataset transfer record.
- Reference updates:
  - Added the config to `experiments/xdataset-probe-transfer/experiment.yaml`
    under `instrument.configs` and recorded its SHA-256 pin.
  - Rewrote the GPU-free hidden-state probe unit test fixture path.
  - Updated the canonical mech-interp-runner cross-dataset reference and synced
    generated skill mirrors.
- Non-goals:
  - Did not move the live/default `hidden_state_probe.yaml` runner config.
  - Did not move sycophancy hidden-state configs; they remain a separate slice
    because a dedicated sycophancy row-manifest test covers them.

## C003c - Sycophancy Answer Hidden-State Extraction Configs

- Date: 2026-07-09
- Source component: `C003` subset
- File count: 2
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/sycophancy-hs/`
- Owner decision: archive-only historical provenance for Phase 3
  answer-sycophancy hidden-state extraction prep configs. These are not reusable
  shared defaults; they remain checked-in parser/selection fixtures via the
  dedicated sycophancy row-manifest test.
- Reason: the pair forms the bounded base-vs-SFT and base-vs-KTO seed-1
  extraction prep surface over the shared answer-sycophancy row manifest.
- Reference updates:
  - Rewrote moved-config references in the sycophancy session note.
  - Updated the dedicated sycophancy row-manifest unit test fixture paths.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move the live/default `hidden_state_probe.yaml` runner config.

## C010a - Current-Clean Prompt-Matched Readout Configs

- Date: 2026-07-09
- Source component: `C010` subset
- File count: 8
- Source root: `experiment/phase1/probe/config/`
- Destinations:
  - Amendment F stacking arms:
    `experiments/grpo-centered-stacking/artifacts/configs/mi-readouts/`
  - GRPO v2 single-arm archive:
    `archive/experiment/phase1/probe/config/current-clean-grpo-v2-unknown-failure/`
  - KTO single-arm archive:
    `archive/experiment/phase1/probe/config/current-clean-kto-unknown-failure/`
- Owner decision: associate the DPO->GRPO, GRPO->DPO, and KTO->GRPO
  prompt-matched behavior-axis/readout configs with migrated Amendment F
  (`grpo-centered-stacking`). Keep the GRPO v2 and KTO single-arm readouts as
  archive-only historical provenance beside their already-archived scan and
  direction configs.
- Reason: these files complete the prompt-matched model-variation comparison
  readout surface: behavior-axis scan plus multicell readout for the three
  Amendment F stacking arms, and matching multicell readouts for the GRPO v2 and
  KTO single-arm baselines.
- Reference updates:
  - Rewrote moved-config references and command paths in the historical
    model-variation session note.
  - Added the Amendment F files to `experiments/grpo-centered-stacking` inputs
    and regenerated the experiment registry.
  - Updated destination README files.
- Non-goals:
  - Did not move generated extraction, analysis, or replay outputs under
    `experiment/phase1/probe/`.
  - Did not move AC coupled-intervention, head-intervention, logit-cell, SAE, or
    direction-transform config families.

## C025a - SelfAware SAE Screen Configs

- Date: 2026-07-09
- Source component: `C025` subset
- File count: 7
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/selfaware-sae-screens/`
- Owner decision: archive-only historical provenance for the June 19/20 Phase 3
  SelfAware SAE smoke, pilot-training, feature-analysis, feature-direction, and
  feature-composite screen sequence. No migrated `experiments/<slug>` owner was
  present, and these are not reusable shared defaults.
- Reason: these files form the upstream SAE screen family for the already
  archived SAE feature logit-diagnostic configs.
- Reference updates:
  - Rewrote moved-config references and command paths in historical SAE session
    notes and the model-variation note.
  - Updated the canonical mech-interp-runner SAE reference and synced generated
    skill mirrors.
  - Added a README to the destination archive folder.
- Non-goals:
  - Did not move generated SAE outputs or analysis directories.
  - Did not move the downstream SAE feature logit-diagnostic configs; those were
    already archived in `selfaware-sae-feature-logit-diagnostics/`.

## C003d - KUQ Cross-Dataset Baseline Generation Config

- Date: 2026-07-09
- Source component: `C003` subset
- File count: 1
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `experiments/xdataset-probe-transfer/`
- Owner decision: experiment-associated instrument config for migrated Amendment
  P (`xdataset-probe-transfer`), not archive-only. The config generates the
  no-hook KUQ baseline answers consumed by the cross-dataset behavior assembly.
- Reason: this file is Step 2 of the Amendment P cross-dataset protocol and
  belongs with the KUQ panel artifacts and hidden-state extraction config.
- Reference updates:
  - Added the config to `experiments/xdataset-probe-transfer/experiment.yaml`
    under `instrument.configs` and recorded its SHA-256 pin.
  - Updated the canonical mech-interp-runner cross-dataset reference and synced
    generated skill mirrors.
- Non-goals:
  - Did not move generated KUQ baseline outputs under
    `experiments/xdataset-probe-transfer/analysis/`.

## C009c - Current-Clean GRPO v2 Unknown-Failure Logit-Cell Analyses

- Date: 2026-07-09
- Source component: `C009` subset
- File count: 4
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-unknown-failure/`
- Owner decision: archive-only historical provenance for generic and
  prompt-matched GRPO v2 unknown-failure logit-cell aggregation configs. These
  are downstream analyses over already archived candidate/sweep configs and are
  not reusable shared defaults.
- Reason: these files complete the logit-diagnostic aggregation surface for the
  archived GRPO v2 unknown-failure slice.
- Reference updates:
  - Rewrote the historical model-variation session command path for the
    prompt-matched refusal logit-cell analysis.
  - Updated the destination archive README.
- Non-goals:
  - Did not move generated logit diagnostic outputs or cell-analysis outputs.

## C001e2 - Gold-KTO Calibrated-Expression Logit-Cell Analyses

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 8
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/gold-kto-calibrated-expression-logit-panels/`
- Owner decision: archive-only historical provenance for gold-backed KTO
  calibrated-expression answer/refusal logit-cell aggregation configs. These
  are downstream analyses over already archived simple, composite, same-layer,
  and multilayer candidate/sweep configs, with no migrated `experiments/<slug>`
  owner and no reusable shared-default role.
- Reason: these files complete the archived Gold-KTO calibrated-expression
  logit-panel family by co-locating the aggregation configs with the candidate
  and sweep configs whose diagnostic outputs they summarize.
- Reference updates:
  - Updated the destination archive README.
  - No live docs, skills, tests, or experiment manifests referenced these moved
    config paths outside the generated terrain inventory.
- Non-goals:
  - Did not move generated behavior panels, causal-pilot outputs,
    logit-diagnostic outputs, or cell-analysis outputs under
    `experiment/phase1/probe/qwen3-4b-instruct/`.

## C001f2 - Gold-KTO Targeted Rare-Cell Scoring Configs

- Date: 2026-07-09
- Source component: `C001` subset
- File count: 5
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/gold-kto-targeted-rare-cell-panels/`
- Owner decision: archive-only historical provenance for the targeted 448-row
  SFT->KTO gold behavior-panel, multicell-readout, logit-cell aggregation, and
  sign-score configs. These complete the already archived targeted rare-cell
  panel family and are not reusable shared defaults.
- Reason: these files form the downstream scoring surface for the targeted
  rare-cell pipeline already archived in `C001f`: materialize behavior labels,
  fit the multicell readout, aggregate targeted logit diagnostics by behavior
  cell, and rank candidate arms by sign goals.
- Reference updates:
  - Rewrote moved-config references in the June 20 behavior-conditioned session
    note.
  - Rewrote the archived model-variation note reference to the targeted
    multicell readout.
  - Updated the destination archive README.
- Non-goals:
  - Did not move generated hidden-state extractions, behavior panels,
    causal-pilot outputs, logit-cell outputs, multicell-readout outputs, or
    cell-sign-score outputs under `experiment/phase1/probe/qwen3-4b-instruct/`.
