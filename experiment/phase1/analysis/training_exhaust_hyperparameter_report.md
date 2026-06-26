# Training Exhaust Hyperparameter Audit

Generated from local scratch capacity profiles, timestamped trainer JSONL logs, and the checked-in self-aware eval rollup. Raw scratch artifacts remain uncommitted.

## Scope

- Parsed capacity/log artifacts: 32 runs.
- Full-run rows: 14.
- Clean response-confidence rows with eval joins: 9.

## Main Read

- LoRA shape was constant across the clean runs inspected here: rank 32, alpha 64, dropout 0.05. Current results therefore do not identify a LoRA-rank effect.
- Effective batch and VRAM limits are arm-specific. GRPO v2 full used batch 32 with low OOM risk; clean KTO used batch 12 and reached the high-VRAM/moderate-risk zone.
- Clean DPO/KTO rows generally optimized their trainer objective, but downstream behavior moved only modestly. That points first to preference/reward target design and beta/LR fit, not simply to needing more epochs.
- GRPO produces the strongest behavioral pushes in this matrix, but it also tends to push refusal recall and over-refusal together; the best seed-1 stack so far is still a compromise, not an aligned confidence solution.

## Best Clean Rows By Balanced Behavior

| arm | method | batch | lr | beta | peak VRAM % | log peak % | balanced | refusal recall | answer unknown | over-refusal | confidence | flags |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| clean_sft_grpo_dpo | DPO | 8 | 5e-06 | 0.1 | 46.68 | 46.68 | 55.77 | 93.31 | 6.69 | 63.63 | 0.866301 |  |
| clean_sft_grpo_v2 | GRPO | 32 | 5e-06 | 0.1 | 73.41 | 73.41 | 55.43 | 93.41 | 6.59 | 66.62 | 0.813382 | grpo_kl_high_mean |
| clean_sft_dpo_grpo | GRPO | 32 | 5e-06 | 0.1 | 57.99 | 57.99 | 55.4025 | 93.31 | 6.69 | 65.3 | 0.844615 | grpo_kl_high_mean |
| clean_sft_grpo_v1 | GRPO | 32 | 5e-06 | 0.1 | 72.49 | 72.49 | 55.3325 | 95.54 | 4.46 | 75.7 | 0.746546 | grpo_kl_high_mean |
| clean_sft_kto_grpo | GRPO | 32 | 5e-06 | 0.1 | 72.62 | 72.62 | 55.1425 | 92.54 | 7.46 | 66.37 | 0.862188 | grpo_kl_high_mean |
| clean_sft_grpo_kto | KTO | 12 | 1e-06 | 0.1 | 89.22 | 89.22 | 54.7825 | 89.63 | 10.37 | 60.59 | 0.864039 | vram_high;low_vram_headroom;oom_risk_moderate |
| clean_sft_dpo | DPO | 8 | 5e-06 | 0.1 | 46.68 | 46.68 | 54.4275 | 87.11 | 12.89 | 56.18 | 0.812083 |  |
| clean_sft_merged | SFT | 10 | 0.0002 |  | 135.99 | 135.99 | 54.33 | 87.02 | 12.98 | 57.51 | 0.748489 | capacity_pct_over_100;vram_high;low_vram_headroom;oom_risk_critical |

## Preference-Signal Flags

- No preference-margin flags in the clean rows.

## Capacity Flags

| arm | method | batch | peak VRAM % | log peak % | min headroom GB | samples/sec | flags |
|---|---:|---:|---:|---:|---:|---:|---|
| clean_sft_grpo_kto | KTO | 12 | 89.22 | 89.22 | 2.59 | 5.071 | vram_high;low_vram_headroom;oom_risk_moderate |
| clean_sft_kto | KTO | 12 | 89.37 | 89.37 | 2.55 | 4.564 | vram_high;low_vram_headroom;oom_risk_moderate |
| clean_sft_merged | SFT | 10 | 135.99 | 135.99 | 0 | 8.514 | capacity_pct_over_100;vram_high;low_vram_headroom;oom_risk_critical |

Note: `capacity_pct_over_100` marks a capacity signal that exceeded the card's nominal VRAM. On this Windows/Docker/Unsloth stack that may reflect offload/shared-memory behavior, allocator-history accounting, or a telemetry/unit anomaly. Treat that row as unsafe for batch-size increases, but do not treat the exact percentage as physically meaningful without an independent live rerun.

## Literature-Backed Hyperparameter Guidance

- LoRA rank: `2602.06204` supports a coupled rank/LR view. If we test ranks beyond r32, do not change rank alone; pair each rank with either a justified LR scaling rule or a small LR panel.
- DPO beta: `2407.08639` supports beta sensitivity as a function of preference-pair quality. Before a beta panel, audit chosen/rejected pair gaps or stratify known/unknown/ambiguous pair types.
- GRPO beta/KL: current GRPO rows are behaviorally strongest but flagged with high mean KL. A GRPO beta/KL panel is plausible only if it tests the over-refusal tradeoff, not just final reward.
- Batch size: use capacity evidence only after objective choice. DPO has room to probe higher effective batch; KTO is near the local ceiling; GRPO batch 32 is already the practical starting point.

## Decision Implications

- Do not blanket-increase batch size. SFT/DPO may have room; KTO is already near the ceiling; GRPO batch 32 is plausible but should keep a 6 GB minimum-headroom guard.
- Before LR/beta sensitivity runs, decide whether the underlying objective is worth rerunning; if yes, use the ingested LoRA-LR and DPO-beta papers to choose a small theory-backed panel.
- For 8B, start with the Tier 1 seed-1 response-confidence screen after the source-label/thinking gates, not the full matrix.
- For small-model tuning, prioritize reward/data design and confidence calibration over simply adding DPO/KTO epochs.
