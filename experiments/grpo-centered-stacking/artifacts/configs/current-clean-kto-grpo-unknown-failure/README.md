# Current-Clean KTO-GRPO Unknown-Failure Configs

Configuration artifacts for the Amendment F `clean_sft_kto_grpo` Phase 3 prompt-matched SelfAware rare-cell panel.

Migration batch: `C010` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: this component belongs to `experiments/grpo-centered-stacking` because the governed Amendment F design defines the `clean_sft_kto_grpo` arm and its seed-1 local evidence. These files are not reusable shared defaults.

Files:

- `phase3_current_clean_kto_grpo_unknown_failure_selfaware_manifest.yaml`: panel-builder config for the 64-per-cell unknown-failure SelfAware behavior panel.
- `phase3_current_clean_kto_grpo_unknown_failure_selfaware_row_keys.txt`: selected row-key artifact generated for that panel.

Known provenance gaps:

- `phase3_current_clean_kto_grpo_unknown_failure_selfaware_scored_rows.jsonl` was referenced by the manifest config but was not tracked or present at migration time.
- `phase3_current_clean_kto_grpo_unknown_failure_selfaware_manifest.summary.json` was referenced by the manifest config but was not tracked or present at migration time.
