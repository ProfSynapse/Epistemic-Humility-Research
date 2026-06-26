---
title: 'Clean SFT -> DPO -> GRPO response-confidence stack'
kg:
  id: experiment:clean-sft-dpo-grpo
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: done
governance: amendment
phase: phase1
lane: local
est_compute: '~7-10 local RTX 3090 GPU-hours for seed-1 merge, GRPO train, and full SelfAware eval'
relationships:
  - type: tests
    target: '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
    target_id: mechanism:dpo-diversity-cost-depends-on-upstream-sft-state
    confidence: high
  - type: tests
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: high
related:
  - '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
---

## Question & Hypothesis

Can GRPO restore unknown-row abstention after `clean SFT -> DPO` lowers
known-row over-refusal, without simply reverting to GRPO-style over-refusal?

This is an Amendment F experiment under `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** DPO first moves the model toward answering known rows, then
  GRPO reintroduces a reward-shaped refusal boundary for unknown rows.
- **Falsifier.** GRPO erases DPO's known-answer recovery, or DPO's answer-prone
  policy causes GRPO to retain high unknown answering.

## Design

Arm: `clean_sft_dpo_grpo`, defined as clean Amendment E SFT, then corrected-base
DPO, then GRPO v2 unless Amendment F is updated with a newer reward variant.

Primary comparator set:

- clean SFT merged seed 1;
- clean SFT->DPO corrected-base seed 1;
- clean SFT->GRPO v2 seed 1;
- Amendment E grouped comparison table.

Metrics: full SelfAware truthful percentage, unknown refusal recall, unknown
answer rate, known over-refusal, correct-on-known among answered known rows,
response-confidence coverage, confidence distribution by behavioral cell, and
Brier/MAE versus response appropriateness.

## Prerequisites & Gating

- Source `clean_schema_sft_dpo_seed1_corrected_base` full eval exists and is not
  lineage-confounded.
- Merge the DPO adapter onto the clean SFT merged base before GRPO.
- Run a bounded merged-source SelfAware sanity eval before GRPO launch.
- Confirm GRPO config uses the merged SFT->DPO model as `model.model_name`, not
  the original Qwen3 base.
- Confirm Docker/GPU is idle enough for GRPO and record `nvidia-smi` before
  launch.

## Runbook

1. Read `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md` and
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`.
2. Compare source-arm metrics against
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Materialize a seed-1 GRPO config by copying the pattern in
   `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`
   and changing only the base model/output labels for `clean_sft_dpo_grpo`.
4. Launch the merged-source sanity eval using the existing eval-config pattern in
   `experiment/phase1/eval/config/`.
5. If sanity passes, launch GRPO locally with the v2 reward implementation in
   `experiment/phase1/grpo/humility_reward_v2.py`.
6. Run the full SelfAware eval, rebuild the comparison CSV with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`, and
   write a `docs/sessions/` checkpoint.

## Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, DPO adapter, merge path,
  and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** GRPO training has final artifacts, reward debug rows have
  nonzero reward variance, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->DPO, and SFT->GRPO v2.

## Outputs & provenance

- Run record: `experiment/phase1/run_records/`.
- Session checkpoint: `docs/sessions/`.
- Analysis: `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  and grouped companion.
- Hugging Face publication is allowed only after eval passes: publish public
  adapter/config/model-card artifacts and a repository pointer to the data
  recipe, not restricted raw data or large unreviewed run products.
- Results remain Amendment F exploratory evidence and do not enter PROTOCOL v0.3
  headline claims.

## Variations

- Seed 1 local only until the arm is interpretable.
- Seeds 2/3 are deferred until seed 1 beats or clearly diagnoses the immediate
  source arm.
- If GRPO v3 supersedes v2 before launch, update Amendment F and this note before
  training.

## Status log

- 2026-06-24: created (proposed) as one of four Amendment F GRPO-centered
  stacking experiment notes.
- 2026-06-24: activated for seed-1 local launch after Amendment F sign-off.
- 2026-06-24: merged the clean SFT->DPO seed-1 adapter, passed bounded
  merged-source sanity eval, and launched full GRPO in
  `eh-clean-sft-dpo-grpo-seed1-full-20260624a`.
- 2026-06-24: full SelfAware eval completed cleanly with `n=3369`, `100%`
  response-confidence coverage, `truthful_pct=41.20`,
  `refusal_recall_pct=93.31`, `answer_on_unknown_pct=6.69`,
  `over_refusal_pct=65.30`, `correct_on_known_pct=52.40`, mean response
  confidence `0.844615`, and Brier vs response appropriateness `0.428793`.
  Interpretation: GRPO after DPO strongly controls unknown answering but does
  so with high known-row over-refusal; it is useful evidence but did not beat
  the `clean_sft_grpo_dpo` direction on the overall tradeoff.
