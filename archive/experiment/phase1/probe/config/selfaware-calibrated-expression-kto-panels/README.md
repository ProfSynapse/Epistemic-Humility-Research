# SelfAware Calibrated-Expression KTO Panel Config Archive

This directory archives legacy Phase 3 SelfAware calibrated-expression KTO logit, composite, orthogonalized-window, and replay configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the SelfAware calibrated-expression KTO panel slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 20 Phase 3 SelfAware KTO calibrated-expression logit/replay panel work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains the fixed 64-row key panel, KTO intervention candidate files, logit sweeps for simple/composite/grid/orthogonalized variants, and the bounded composite generation replay. Sweep configs point to the archived causal-pilot core runner template.

Non-goal: generated behavior-axis direction manifests, direction-transform outputs, causal-pilot outputs, and generation outputs under `experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/` are preserved as historical run provenance.