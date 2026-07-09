# Gold-KTO Targeted Rare-Cell Panel Config Archive

This directory archives legacy Phase 3 targeted gold-backed KTO rare-cell row-key, extraction, candidate, baseline replay, and targeted calibrated-expression logit configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the targeted rare-cell slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the targeted 448-row SFT->KTO gold behavior panel and follow-on targeted calibrated-expression logit triage. No migrated `experiments/<slug>` owner was present, and these configs/artifacts are not reusable shared defaults.

The component group contains the row-key generator config, row-key manifest/text output, selected rare-cell rows, targeted hidden-state extraction config, targeted candidate source, baseline generation replay, and targeted calibrated-expression logit candidate/sweep pair. Sweep configs point to the archived causal-pilot core runner template.

Non-goal: generated hidden-state extractions, behavior panels, causal-pilot outputs, and downstream cell-analysis configs under `experiment/phase1/probe/qwen3-4b-instruct/` are preserved as historical run provenance or separate terrain components.