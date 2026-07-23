# SelfAware SAE Feature Logit-Diagnostic Config Archive

This directory archives legacy Phase 3 SelfAware SAE-feature logit-diagnostic configs formerly stored under `experiment/phase1/probe/config/`.

Migration batches: `C021`, `C022`, `C023`, and `C024` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 19/20 Phase 3 SAE feature diagnostic work. No migrated `experiments/<slug>` owner was present, and these configs were not reusable shared defaults at migration time.

The component group contains diagnostic and sweep pairs for:

- behavior-conditioned SAE features;
- SAE feature composites;
- the f047 nearby-layer follow-up;
- the original top-k SAE feature diagnostic.

Keep these files as provenance for historical SAE feature causal-smoke/logit-diagnostic work. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.

Non-goal: legacy extraction, SAE direction, and causal-pilot output roots under `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/` are preserved as historical run provenance and will be handled in broader artifact archive passes.