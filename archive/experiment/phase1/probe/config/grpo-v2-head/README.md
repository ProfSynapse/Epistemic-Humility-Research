# GRPO v2 Attention-Head Config Archive

This directory archives legacy Phase 3 current-clean GRPO v2 unknown-failure
attention-head localization, steering-direction, read-trajectory, and
intervention-sweep configs formerly stored under
`experiment/phase1/probe/config/`.

Migration subset: the prompt-matched attention-head slice of `C009` from
`docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the GRPO v2
unknown-failure attention-head follow-up. No migrated `experiments/<slug>`
owner was present, and these configs are not reusable shared defaults.

The component group belongs conceptually with
`archive/experiment/phase1/probe/config/current-clean-grpo-v2-unknown-failure/`,
but is kept in this shorter sibling path to avoid Windows Git path-length
failures on the longest intervention-sweep filenames.

Non-goal: generated head-localization, steering-direction, read-trajectory, and
intervention outputs under `experiment/phase1/probe/` are preserved as
historical run provenance.
