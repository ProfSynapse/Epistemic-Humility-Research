# Latent Knowledge Controls Artifacts

This directory preserves the original JSON outputs and logs from the Phase 3
SelfAware latent-knowledge control package.

- `a1a2_h_lora.json`: lexical baseline and within-known over-refusal controls.
- `a3_h_base_probe.json`: base-hidden-state latent knowledge probe rerun.
- `c2_gap_sft.json`, `c2_gap_grpo_dpo.json`: over-refusal-gap readout panels.
- `c2_sft.json`, `c2_grpo_dpo.json`, `c2_grpo_v2.json`: cross-regimen control
  panels.
- `caution_axis_transfer.json`: cross-regimen caution-axis transfer geometry.
- `*.log`: original command output logs for the adjacent JSON result.

Producer scripts remain under `experiment/phase1/probe/` while the Phase 1 probe
code tree is migrated.
