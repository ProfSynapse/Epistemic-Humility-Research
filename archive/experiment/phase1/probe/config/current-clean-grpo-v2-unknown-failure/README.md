# Current-Clean GRPO v2 Unknown-Failure Config Archive

This directory archives the legacy Phase 3 current-clean GRPO v2 unknown-failure config component formerly stored under `experiment/phase1/probe/config/`.

Migration batch: `C008` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the Phase 3 model-variation session. No migrated `experiments/<slug>` owner was present, and this component was not a reusable shared input.

The component contains the GRPO v2 unknown-answering failure candidate inventory, logit diagnostic sweeps, generated replay configs, the L26 constrained replay follow-up, and the row-key panel used by those configs. It is archived as a connected config component because the files reference each other, but no live code, tests, or skills referenced the component directly at migration time. The only outside-component operational reference was the historical session note `docs/sessions/20260625T145842Z-phase-3-model-variation-panel.md`, which now points here.

Keep these files as provenance for the historical Phase 3 model-variation work. Do not use this directory as the home for new experiment instruments; new evidence-producing cells belong under `experiments/<slug>/` or `experiments/common/` when promoted for shared reuse.
Known provenance gaps: `phase3_current_clean_grpo_v2_unknown_failure_selfaware_scored_rows.jsonl` and `phase3_current_clean_grpo_v2_unknown_failure_selfaware_manifest.summary.json` were referenced by historical notes/config but were not tracked or present when this archive batch was created.
Additional migration batches:

- `C007`: generic-prompt GRPO v2 unknown-failure behavior-axis scan and direction export.
- `C009`: prompt-matched GRPO v2 unknown-failure behavior-axis scan plus simple and L26 multicell direction exports.
- `C009b`: prompt-matched GRPO v2 unknown-failure multicell readout config.
- `C009c`: generic and prompt-matched GRPO v2 unknown-failure logit-cell analysis configs.
- `C009d`: prompt-matched attention-head localization, head steering-direction,
  read-trajectory, and intervention sweep configs, including random-head
  controls. These live in sibling archive folder `../grpo-v2-head/` to keep
  Windows paths short enough for Git.

These batches remain archive-only historical provenance for the Phase 3 GRPO v2 unknown-failure slice. They are kept here with the generated replay, logit diagnostic, and candidate configs that consume their analysis outputs.
