---
title: 'Clean SFT -> KTO -> GRPO response-confidence stack'
kg:
  id: experiment:clean-sft-kto-grpo
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: running
governance: amendment
phase: phase1
lane: local
est_compute: '~7-10 local RTX 3090 GPU-hours for seed-1 merge, GRPO train, and full SelfAware eval'
relationships:
  - type: tests
    target: '[[unpaired-binary-signal-matches-paired-preference]]'
    target_id: mechanism:unpaired-binary-signal-matches-paired-preference
    confidence: medium
  - type: tests
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: high
related:
  - '[[unpaired-binary-signal-matches-paired-preference]]'
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
---

## Question & Hypothesis

Can GRPO improve a less destructive `clean SFT -> KTO` policy by increasing
unknown-row abstention while preserving KTO's lower known-row over-refusal?

This is an Amendment F experiment under `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** KTO is a gentler first preference pass than DPO; GRPO can then
  tighten the refusal boundary without starting from a severely answer-prone
  policy.
- **Falsifier.** GRPO pushes the KTO-warmed model into the same over-refusal
  profile as direct SFT->GRPO, or KTO's higher unknown-answer rate persists.

## Design

Arm: `clean_sft_kto_grpo`, defined as clean Amendment E SFT, then corrected-base
KTO, then GRPO v2 unless Amendment F is updated with a newer reward variant.

Primary comparator set:

- clean SFT merged seed 1;
- clean SFT->KTO corrected-base seed 1;
- clean SFT->GRPO v2 seed 1;
- Amendment E grouped comparison table.

Metrics: full SelfAware truthful percentage, unknown refusal recall, unknown
answer rate, known over-refusal, correct-on-known among answered known rows,
response-confidence coverage, confidence distribution by behavioral cell, and
Brier/MAE versus response appropriateness.

## Prerequisites & Gating

- Source `clean_schema_sft_kto_seed1_corrected_base` full eval exists and is not
  lineage-confounded.
- Merge the KTO adapter onto the clean SFT merged base before GRPO.
- Run a bounded merged-source SelfAware sanity eval before GRPO launch.
- Confirm GRPO config uses the merged SFT->KTO model as `model.model_name`.
- Confirm Docker/GPU is idle enough for GRPO and record `nvidia-smi` before
  launch.

## Runbook

1. Read `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md` and
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`.
2. Compare source-arm metrics against
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Materialize a seed-1 GRPO config by copying the pattern in
   `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v2_full.yaml`
   and changing only the base model/output labels for `clean_sft_kto_grpo`.
4. Launch the merged-source sanity eval using the existing eval-config pattern in
   `experiment/phase1/eval/config/`.
5. If sanity passes, launch GRPO locally with the v2 reward implementation in
   `experiment/phase1/grpo/humility_reward_v2.py`.
6. Run the full SelfAware eval, rebuild the comparison CSV with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`, and
   write a `docs/sessions/` checkpoint.

## Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, KTO adapter, merge path,
  and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** GRPO training has final artifacts, reward debug rows have
  nonzero reward variance, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->KTO, and SFT->GRPO v2.

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
- 2026-06-25: staged the seed-1 GRPO config and bounded merged-source sanity
  eval config. Merge and sanity launch remain gated on the active
  `clean_sft_dpo_grpo` full eval freeing the local GPU.
- 2026-06-25: merged the clean SFT->KTO seed-1 adapter, passed the bounded
  merged-source sanity eval, and launched the full local `clean_sft_kto_grpo`
  GRPO run in container `eh-clean-sft-kto-grpo-seed1-full-20260625a`.
