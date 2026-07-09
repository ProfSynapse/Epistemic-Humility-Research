# Gold-KTO Calibrated-Expression Logit Panel Config Archive

This directory archives legacy Phase 3 gold-backed KTO calibrated-expression candidate and logit-sweep configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the non-targeted gold-KTO calibrated-expression logit-panel slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the gold-backed KTO calibrated-expression simple, composite, same-layer, and multilayer logit diagnostic work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains candidate and sweep pairs for simple axes, composite directions, same-layer single controls, and multilayer controls. Sweep configs point to the archived causal-pilot core runner template.

Non-goal: generated behavior-axis directions, direction transforms, causal-pilot outputs, and cell-analysis configs under `experiment/phase1/probe/qwen3-4b-instruct/` are preserved as historical run provenance or separate terrain components.