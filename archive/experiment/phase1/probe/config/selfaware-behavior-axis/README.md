# SelfAware Behavior-Axis Config Archive

This directory archives legacy Phase 3 SelfAware behavior-axis scan, direction-export, and logit-diagnostic configs formerly stored under `experiment/phase1/probe/config/`.

Migration batches: `C015`, `C016`, `C017`, and `C018` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 20 Phase 3 SelfAware behavior-axis work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains:

- the SelfAware behavior-axis scan config;
- behavior-axis and layer-window direction-export configs;
- source-layer, nearby/known-panel, layer-window, and known-answer logit-diagnostic configs and sweeps.

Keep these files as provenance for historical behavior-axis scans and exploratory local logit diagnostics. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.

Non-goal: legacy scan, direction, and causal-pilot output roots under `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/` are preserved as historical run provenance and will be handled in broader artifact archive passes.