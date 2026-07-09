# Current-Clean GRPO v2 Known-Overrefusal Config Archive

This directory archives the legacy Phase 3 current-clean GRPO v2
known-overrefusal config component formerly stored under
`experiment/phase1/probe/config/`.

Migration batch: `C005` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the Phase 3 model-variation session. No migrated experiments/<slug> owner was present, and this component was not a reusable shared input.

The component contains exploratory logit diagnostics, generation replay sweeps,
candidate configs, and row-key panels. It is archived as a connected config
component because the files reference each other, but no live code, tests, or
skills referenced the component directly at migration time. The only
outside-component operational reference was the historical session note
`docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, which now
points here.

Keep these files as provenance for the historical Phase 3 model-variation work.
Do not use this directory as the home for new experiment instruments; new
evidence-producing cells belong under `experiments/<slug>/` or
`experiments/common/` when promoted for shared reuse.

Known provenance gap: `phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.manifest.json` was referenced by historical notes/config but was not tracked or present when this archive batch was created.
Additional migration batch:

- `C006`: same-layer GRPO v2 L26 known-overrefusal repair multi-protection behavior-axis scan and direction export.

This batch remains archive-only historical provenance for the Phase 3 GRPO v2 known-overrefusal repair/protection slice. It is kept here with the native, orthogonalized, double-orthogonalized, and replay configs that consume its direction outputs.