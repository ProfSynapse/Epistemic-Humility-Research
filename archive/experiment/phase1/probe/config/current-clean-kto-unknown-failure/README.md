# Current-Clean KTO Unknown-Failure Config Archive

This directory archives the legacy Phase 3 current-clean KTO unknown-failure config component formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C012` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the Phase 3 model-variation KTO prompt-matched arm. No migrated `experiments/<slug>` owner was present, and this component was not a reusable shared input at migration time.

The component contains the KTO rare-cell behavior-panel manifest, generated replay candidate inventory, generated replay sweep, and row-key file. The only outside-component operational reference at migration time was `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, which now points here for the moved files and generated outputs owned by this component.

Keep these files as provenance for historical Phase 3 model-variation/KTO generated replay work. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.

Known provenance gaps:

- `phase3_current_clean_kto_unknown_failure_selfaware_scored_rows.jsonl` was referenced by the manifest config but was not tracked or present at migration time.
- `phase3_current_clean_kto_unknown_failure_selfaware_manifest.summary.json` was referenced by the manifest config and historical session note but was not tracked or present at migration time.
Additional migration batch:

- `C011`: prompt-matched KTO unknown-failure behavior-axis scan and direction export.

This batch remains archive-only historical provenance for the Phase 3 KTO unknown-failure generated replay slice. It is kept here with the replay candidate and generation configs that consume its direction outputs.