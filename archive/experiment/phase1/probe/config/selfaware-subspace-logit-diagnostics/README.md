# SelfAware Subspace Logit Diagnostics Config Archive

This directory archives the legacy Phase 3 SelfAware subspace logit-diagnostic config component formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C025` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 19 Phase 3 SAE smoke/plumbing session. No migrated `experiments/<slug>` owner was present, and this component was not a reusable shared input at migration time.

The component contains same-norm subspace logit-diagnostic runner configs and sweep wrappers for SAE-derived and broad known/unknown directions, including known-retention screens and SFT-runtime variants. The only outside-component operational reference at migration time was `docs/sessions/20260619T195217Z-phase3-sae-smoke-plumbing.md`, which now points here.

Keep these files as provenance for historical Phase 3 SAE/subspace diagnostics. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.