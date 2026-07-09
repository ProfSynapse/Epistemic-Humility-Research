# Nearby-Layer Offset Panel Config Archive

This directory archives legacy Phase 3 Qwen3-4B instruct nearby-layer
logit-diagnostic runner configs formerly stored under
`experiment/phase1/probe/config/`.

Migration subset: the DPO-delta and KTO h_lora L35 nearby-layer offset panels
from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the June 18 Phase 3
causal-pilot nearby-layer controls. No migrated `experiments/<slug>` owner was
present, and these configs are not reusable shared defaults.

The component group contains DPO delta L35 offset `-2`, `-1`, `+1`, `+2`
runner configs and KTO h_lora L35 offset `-2`, `-1`, `+1` runner configs.

Non-goal: generated causal-pilot outputs under
`experiment/phase1/probe/qwen3-4b-instruct/` are preserved as historical run
provenance.
