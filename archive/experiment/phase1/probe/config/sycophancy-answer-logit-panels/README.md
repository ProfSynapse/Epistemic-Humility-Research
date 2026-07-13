# Sycophancy Answer Logit Panel Config Archive

This directory archives legacy Phase 3 answer-sycophancy logit diagnostic, row-key, candidate, and targeted replay configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the answer-sycophancy logit/replay slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 20 Phase 3 answer-sycophancy same-condition logit diagnostic and KTO wrong-hint replay work. No migrated `experiments/<slug>` owner was present, and these configs are not reusable shared defaults.

The component group contains fixed row-key panels, intervention candidates, the logit sweep, and the targeted KTO wrong-hint generation replay. The sweep configs now point to the archived causal-pilot core runner template.

Non-goal: generated causal-pilot outputs under `experiment/phase1/probe/qwen3-4b-instruct-sycophancy-answer/` are preserved as historical run provenance and will be handled in broader artifact archive passes.