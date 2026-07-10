---
title: 'Clean SFT -> GRPO -> DPO seed replication'
kg:
  id: experiment:clean-sft-grpo-dpo-seed-replication
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: amendment
track: training-regimen
lane: local
est_compute: '~2-3 full local seed rebuilds; exact GPU-hours depend on whether clean SFT/GRPO seed artifacts already exist'
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

Does the best Amendment F seed-1 stack, `clean SFT -> GRPO v2 -> DPO`,
replicate across clean response-confidence seeds before publication or scale-up?

This is an Amendment G experiment under
`experiments/best-stack-replication-scale-gate/AMENDMENT.md`; it is
outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** GRPO installs a stronger unknown-refusal boundary, then DPO
  modestly recovers known answers without reopening unknown answering.
- **Falsifier.** The seed-1 improvement disappears across seeds, or the final
  DPO stage mainly amplifies stated confidence while leaving the behavior
  tradeoff unchanged.

## Design

Replicate the same stack for clean response-confidence seeds 2 and 3:

- `clean_sft_grpo_dpo_seed2`
- `clean_sft_grpo_dpo_seed3`

Each seed must rebuild or verify the same-seed clean SFT source, GRPO v2 source,
merged GRPO v2 checkpoint, final DPO adapter, and full SelfAware eval. The
seed-1 artifacts are comparators only.

Primary comparators:

- same-seed clean SFT merged model;
- same-seed clean SFT->GRPO v2 model;
- Amendment F seed-1 `clean_sft_grpo_dpo`;
- grouped comparison table in
  `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.

## Prerequisites & Gating

- Amendment G must be signed or explicitly approved for the exact seed/cell
  before launch.
- For each seed, source lineage must identify clean SFT base, GRPO v2 adapter,
  merge path, DPO final-stage config, and eval config.
- The merged GRPO v2 source must pass a bounded SelfAware sanity eval before
  the final DPO launch.
- Docker and GPU capacity must be checked before each launch.
- If behavior is obviously out of family at a sanity gate, stop and audit
  lineage before continuing.

## Runbook

1. Read `experiments/best-stack-replication-scale-gate/AMENDMENT.md`
   and `experiments/grpo-centered-stacking/AMENDMENT.md`.
2. Compare current evidence in
   `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. For the chosen seed, follow the clean response-confidence setup patterns in
   `archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`.
4. Train or verify same-seed clean SFT, then run full SelfAware eval.
5. Train same-seed GRPO v2 from the clean SFT source, then run full SelfAware
   eval.
6. Merge same-seed GRPO v2, run a bounded merged-source SelfAware sanity eval,
   then launch final-stage DPO.
7. Run the full SelfAware eval, rebuild comparison CSVs with
   `archive/experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`,
   and checkpoint the result in `docs/sessions/`.

## Validation contract

- **Pre-run.** Same-seed source lineage is complete and sanity evals are
  behaviorally in family.
- **Post-run.** Training writes final adapter artifacts, lineage points at the
  intended same-seed merged GRPO source, and eval has `n=3369`, no thinking
  contamination, zero or explainable schema retries, and complete response
  confidence coverage.
- **Definition of done.** Seeds 2/3 have full SelfAware metrics and a
  comparison against same-seed GRPO v2 and seed-1 Amendment F.

## Outputs & provenance

- Run records: `archive/experiment/phase1/run_records/`.
- Session checkpoints: `docs/sessions/20260625T115330Z-best-stack-replication-and-scale-gate.md`.
- Analysis: `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  and grouped companion.
- Publication: no Hugging Face upload until seed replication, artifact policy,
  and model-card gates are explicitly approved.

## Variations

- Seed 2 local.
- Seed 3 local.
- Optional 8B seed-1 confirm only after the local seed gate is interpretable.

## Status log

- 2026-06-25: created as a proposed Amendment G experiment note after all four
  Amendment F seed-1 stacks completed.
