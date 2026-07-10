# Current-Clean Behavior-Axis Direction Config Archive

This directory archives the legacy Phase 3 current-clean behavior-axis scan and direction-export config component formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C002` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the Phase 3 model-variation and GRPO v2 known-overrefusal work. No migrated `experiments/<slug>` owner was present, and this component was not a reusable shared input at migration time.

The component contains the current-clean behavior-axis scan plus direction-export configs for known-overrefusal and L26 repair/protection directions. It is upstream provenance for archived generated-replay/logit-diagnostic components, especially the GRPO v2 known-overrefusal archive. The outside-component references at migration time were historical notes only: `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md` and `archive/notes/experiments/mech-interp-model-variation-panel.md`.

Keep these files as provenance for historical Phase 3 analyses. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.