# Current-Clean GRPO-DPO Unknown-Failure Configs

Configuration artifacts for the Amendment F `clean_sft_grpo_dpo` mechinterp prompt-matched SelfAware rare-cell panel.

Migration batch: `C004` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: this component belongs to `experiments/grpo-centered-stacking` because the governed Amendment F design defines the `clean_sft_grpo_dpo` arm and its seed-1 local evidence. These files are not reusable shared defaults.

Files:

- `current_clean_grpo_dpo_unknown_failure_selfaware_manifest.yaml`: panel-builder config for the 64-per-cell unknown-failure SelfAware behavior panel.
- `current_clean_grpo_dpo_unknown_failure_selfaware_row_keys.txt`: selected row-key artifact generated for that panel.

Known provenance gaps:

- `current_clean_grpo_dpo_unknown_failure_selfaware_scored_rows.jsonl` was referenced by the manifest config but was not tracked or present at migration time.
- `current_clean_grpo_dpo_unknown_failure_selfaware_manifest.summary.json` was referenced by the manifest config and historical session note but was not tracked or present at migration time.
