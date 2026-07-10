# Amendment F Prompt-Matched Readout Configs

Configuration artifacts for Amendment F mechinterp prompt-matched behavior-axis
and multicell-readout analyses.

Owner decision: this folder belongs to `experiments/grpo-centered-stacking`
because the governed Amendment F design defines the `clean_sft_dpo_grpo`,
`clean_sft_grpo_dpo`, and `clean_sft_kto_grpo` arms and their seed-1 local
evidence. These files are not reusable shared defaults.

Files:

- `current_clean_dpo_grpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml`
- `current_clean_dpo_grpo_unknown_failure_prompt_matched_multicell_readout.yaml`
- `current_clean_grpo_dpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml`
- `current_clean_grpo_dpo_unknown_failure_prompt_matched_multicell_readout.yaml`
- `current_clean_kto_grpo_unknown_failure_prompt_matched_behavior_axis_scan.yaml`
- `current_clean_kto_grpo_unknown_failure_prompt_matched_multicell_readout.yaml`

The paired panel-builder configs and selected row-key files remain in the
per-arm sibling folders under `artifacts/configs/current-clean-*-unknown-failure/`.
