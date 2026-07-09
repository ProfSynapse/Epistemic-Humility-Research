# Phase 1 Probe Config Migration Log

This log records migration batches after the terrain baseline in
`docs/migration/phase1-probe-config-terrain.md`.

## C005 - Current-Clean GRPO v2 Known-Overrefusal

- Date: 2026-07-09
- Source component: `C005`
- File count: 31
- Source root: `experiment/phase1/probe/config/`
- Destination:
  `archive/experiment/phase1/probe/config/current-clean-grpo-v2-known-overrefusal/`
- Reason: historical exploratory Phase 3 config component with no live code,
  test, or skill references outside the component.
- Reference updates:
  - Rewrote component-internal config path references to the archive path.
  - Rewrote the historical session note
    `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`.
- Non-goals:
  - Did not promote these configs to `experiments/common/`; they are provenance,
    not reusable shared inputs.
  - Did not rewrite legacy analysis output roots in the configs. Those paths
    preserve the historical run provenance and will be handled with the broader
    `experiment/phase1/probe/analysis/` archive migration.
- Provenance gap noted:
  - `phase3_current_clean_grpo_v2_known_overrefusal_replay_192_panel_d_row_keys.manifest.json` was referenced by the historical session note and row-key config but was not tracked or present at migration time.
