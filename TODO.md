# TODO

## Current Evidence State

Durable aggregate table:

- `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
- `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`

Captured full SelfAware eval coverage:

| Family | Coverage |
|---|---|
| Original cold-start SFT/DPO/KTO | 3 seeds each |
| Amendment B answer-confidence cold-start base/SFT/DPO/KTO | 3 seeds each |
| Amendment B answer-confidence SFT-warmed SFT/DPO/KTO | 3 seeds each |
| Amendment E clean response-confidence two-stage screen | seed 1 |
| Amendment F GRPO-centered three-stage screen | seed 1 for all four active stacks |

Current best seed-1 stack:

- `clean_sft_grpo_dpo` = clean SFT -> GRPO v2 -> DPO

Deferred / deprioritized:

- `SFT -> DPO -> KTO`
- `SFT -> KTO -> DPO`

Rationale: reciprocal DPO/KTO stacking is lower priority than preference -> RL
versus RL -> preference crossings. See
`experiment/protocol/AMENDMENT-C-crossover-preference-stacking.md` and
`library/notes/2404.18922--dpo-meets-ppo-reinforced-token-optimization-rlhf.md`.

## Next Decision Points

| Track | Status | Next action |
|---|---|---|
| Amendment G best-stack replication | proposed | Sign off or revise, then run `clean_sft_grpo_dpo` for seeds 2 and 3. |
| 8B response-confidence variants | proposed | Use Amendment I tiers: prepare Tier 1 (`8b_clean_sft`, `8b_clean_sft_grpo_v2`, `8b_clean_sft_grpo_dpo`) before any full 8B matrix. |
| Thinking-enabled branch | proposed | Expand the source probe beyond the 128-row audit before launching training; for 8B, build a separate 8B thinking source probe. |
| Hyperparameter/training-exhaust audit | completed first pass | Use `experiment/phase1/analysis/training_exhaust_hyperparameter_report.md` and `training_exhaust_summary.csv`; do not run a blind LR/beta/rank grid. |
| Mechanistic interpretability | proposed | Use the existing evaluated models to test whether behavior differences map to coherent activation/feature directions. |
| Original PROTOCOL v0.3 robustness matrix | incomplete | LR/beta panel, 8B confirm, and bridge cells remain unrun/deferred. |
| Hugging Face publication | deferred | Wait until a pristine replicated artifact set exists, then publish adapters/model cards/pointers. |

## Recommended Order

1. Use the training-exhaust audit to choose between the next two high-ROI
   branches: no-training mech interp on existing models, or 8B Tier 1 setup.
2. Set up Amendment I Tier 1 8B configs only after the source-label/thinking
   gates are clear.
3. If doing any 4B diagnostic sweep first, keep it bounded and theory-backed:
   LoRA rank must be coupled to LR/effective multiplier, and DPO beta should be
   chosen after auditing preference-pair gap/quality.
4. Run a no-training mechanistic-interpretability pass across the already
   evaluated models, prioritizing clean SFT, clean SFT->GRPO v2,
   clean SFT->GRPO->DPO, and base.
5. Decide whether to run 8B Tier 1 locally or parallelize on HF Jobs.
6. Defer seed replication until we believe the seed-1 stack is final enough to
   replicate.
