---
title: 'Clean SFT -> GRPO -> DPO response-confidence stack'
kg:
  id: experiment:clean-sft-grpo-dpo
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: amendment
phase: phase1
lane: local
est_compute: '~3-5 local RTX 3090 GPU-hours for seed-1 merge, DPO train, and full SelfAware eval'
relationships:
  - type: tests
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: high
  - type: tests
    target: '[[dpo-choice-induces-severe-answer-uncertainty-shift]]'
    target_id: mechanism:dpo-choice-induces-severe-answer-uncertainty-shift
    confidence: high
related:
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
  - '[[dpo-choice-induces-severe-answer-uncertainty-shift]]'
---

## Question & Hypothesis

Can DPO recover known answers after `clean SFT -> GRPO v2` shifts refusal upward,
without materially reopening unknown answering?

This is an Amendment F experiment under `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** GRPO first installs a stronger unknown-refusal boundary; DPO
  can then reduce known-row over-refusal by preferring answerable completions.
- **Falsifier.** DPO after GRPO reintroduces the DPO-style unknown-answering
  failure mode, or merely amplifies stated confidence without improving behavior.

## Design

Arm: `clean_sft_grpo_dpo`, defined as clean Amendment E SFT, then GRPO v2, then
DPO over the same response-confidence preference dataset.

Primary comparator set:

- clean SFT merged seed 1;
- clean SFT->GRPO v2 seed 1;
- clean SFT->DPO corrected-base seed 1;
- Amendment E grouped comparison table.

Metrics: full SelfAware truthful percentage, unknown refusal recall, unknown
answer rate, known over-refusal, correct-on-known among answered known rows,
response-confidence coverage, confidence distribution by behavioral cell, and
Brier/MAE versus response appropriateness.

## Prerequisites & Gating

- Source `clean_schema_sft_grpo_v2_seed1_corrected_base` full eval exists.
- Merge the GRPO v2 adapter onto the clean SFT merged base before DPO.
- Run a bounded merged-source SelfAware sanity eval before DPO launch.
- Confirm DPO config uses the merged SFT->GRPO v2 model as base/reference state
  where the generic tuner supports that relationship.
- Confirm Docker/GPU capacity; DPO may start with the safer Amendment E batch 2 /
  accumulation 4 unless a fresh smoke supports a larger batch.

## Runbook

1. Read `experiment/protocol/AMENDMENT-F-grpo-centered-stacking.md` and
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`.
2. Compare source-arm metrics against
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Materialize a DPO launch config/command using the DPO section in
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`, changing only
   the base model/output labels for `clean_sft_grpo_dpo`.
4. Launch the merged-source sanity eval using the existing eval-config pattern in
   `experiment/phase1/eval/config/`.
5. If sanity passes, launch DPO locally from the merged GRPO v2 source model.
6. Run the full SelfAware eval, rebuild the comparison CSV with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`, and
   write a `docs/sessions/` checkpoint.

## Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, GRPO v2 adapter, merge
  path, and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** DPO training has final artifacts, training lineage points at the
  merged GRPO v2 source, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->GRPO v2, and SFT->DPO.

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
- Probe a larger DPO batch only after source sanity passes and the objective is
  worth spending the run.
- Seeds 2/3 are deferred until seed 1 improves the immediate source tradeoff.

## Status log

- 2026-06-24: created (proposed) as one of four Amendment F GRPO-centered
  stacking experiment notes.
