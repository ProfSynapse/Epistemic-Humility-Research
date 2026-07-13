# Gold-Answer KTO Panel Config Archive

This directory archives legacy Phase 3 gold-answer KTO baseline, first-token, unknown-row coefficient/random-seed, and bounded generation replay configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the gold-answer KTO panel slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the gold-backed KTO answer-start and generated-answer diagnostic work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains baseline generation replay plus gold-backed first-token, fixed unknown-row coefficient/random-seed, and KTO unknown generation replay sweeps. Sweep configs point to the archived causal-pilot core runner/candidate templates.

Non-goal: generated behavior panels and causal-pilot outputs under `experiment/phase1/probe/qwen3-4b-instruct/` are preserved as historical run provenance.