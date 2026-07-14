# SelfAware Full-Delta Logit Diagnostics Config Archive

This directory archives the legacy Phase 3 full SelfAware delta logit-diagnostic config component formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C020` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 19 Phase 3 SelfAware stratified-row session. No migrated `experiments/<slug>` owner was present, and this component was not a reusable shared input.

The component contains exploratory local logit-diagnostic runner configs and sweep wrappers for the full SelfAware top delta candidates and nearby-layer offset checks. It is archived as a connected config component because the sweep wrappers reference the runner configs. The only outside-component operational reference was the historical session note `docs/sessions/20260619T101926Z-phase-3-selfaware-stratified-row-manifest.md`, which now points here.

Keep these files as provenance for the historical Phase 3 SelfAware logit-diagnostic work. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.