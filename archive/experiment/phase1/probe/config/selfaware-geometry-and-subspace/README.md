# SelfAware Geometry And Subspace Config Archive

This directory archives legacy Phase 3 SelfAware direction-geometry,
calibrated-expression plane, and DPO/KTO subspace direction-transform configs
formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the SelfAware geometry and subspace diagnostic slices of
`C001` and SelfAware-related components from
`docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for read-only geometry,
plane, and subspace normalization diagnostics. No migrated `experiments/<slug>`
owner was present, and these configs are not reusable shared defaults.

The component group contains direction-geometry comparisons across broad
SelfAware DPO/KTO candidate directions, SAE feature directions,
calibrated-expression behavior axes, the calibrated-expression plane analysis,
and DPO/KTO subspace transforms normalized to the SAE contrast norm.

Non-goal: generated direction-geometry outputs, calibrated-expression plane
outputs, and direction-transform outputs under
`experiment/phase1/probe/qwen3-4b-sft-merged-seed1-selfaware/` are preserved as
historical run provenance.
