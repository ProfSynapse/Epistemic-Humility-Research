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

This is an Amendment F experiment under `experiments/grpo-centered-stacking/AMENDMENT.md`;
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

1. Read `experiments/grpo-centered-stacking/AMENDMENT.md` and
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

## Clean SFT -> GRPO -> DPO

### Question & Hypothesis

Can DPO recover known answers after `clean SFT -> GRPO v2` shifts refusal upward,
without materially reopening unknown answering?

This is an Amendment F experiment under `experiments/grpo-centered-stacking/AMENDMENT.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** GRPO first installs a stronger unknown-refusal boundary; DPO
  can then reduce known-row over-refusal by preferring answerable completions.
- **Falsifier.** DPO after GRPO reintroduces the DPO-style unknown-answering
  failure mode, or merely amplifies stated confidence without improving behavior.

### Design

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

### Prerequisites & Gating

- Source `clean_schema_sft_grpo_v2_seed1_corrected_base` full eval exists.
- Merge the GRPO v2 adapter onto the clean SFT merged base before DPO.
- Run a bounded merged-source SelfAware sanity eval before DPO launch.
- Confirm DPO config uses the merged SFT->GRPO v2 model as base/reference state
  where the generic tuner supports that relationship.
- Confirm Docker/GPU capacity; DPO may start with the safer Amendment E batch 2 /
  accumulation 4 unless a fresh smoke supports a larger batch.

### Runbook

1. Read `experiments/grpo-centered-stacking/AMENDMENT.md` and
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

### Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, GRPO v2 adapter, merge
  path, and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** DPO training has final artifacts, training lineage points at the
  merged GRPO v2 source, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->GRPO v2, and SFT->DPO.

### Outputs & provenance

- Run record: `experiment/phase1/run_records/`.
- Session checkpoint: `docs/sessions/`.
- Analysis: `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  and grouped companion.
- Hugging Face publication is allowed only after eval passes: publish public
  adapter/config/model-card artifacts and a repository pointer to the data
  recipe, not restricted raw data or large unreviewed run products.
- Results remain Amendment F exploratory evidence and do not enter PROTOCOL v0.3
  headline claims.

### Variations

- Seed 1 local only until the arm is interpretable.
- Probe a larger DPO batch only after source sanity passes and the objective is
  worth spending the run.
- Seeds 2/3 are deferred until seed 1 improves the immediate source tradeoff.

### Status log

- 2026-06-24: created (proposed) as one of four Amendment F GRPO-centered
  stacking experiment notes.
- 2026-06-25: staged the shared GRPO-v2 merged-source sanity eval config at
  `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_local_4b.yaml`.
  Actual merge, sanity eval, and DPO launch remain gated on the active
  `clean_sft_kto_grpo` full eval completing and passing post-eval sanity.
- 2026-06-25: merged the clean SFT->GRPO v2 seed-1 adapter, passed the
  merged-source sanity/equivalence gate, and launched the full local
  `clean_sft_grpo_dpo` DPO run in
  `eh-clean-sft-grpo-dpo-seed1-full-20260625a` with conservative batch 2 /
  accumulation 4.
- 2026-06-25: full DPO training completed at step 1868 with low OOM risk and
  final adapter artifacts in
  `scratch/schema_response_confidence/runs/clean_sft_grpo_dpo_seed1_full/20260625_031724/final_model`.
  The full SelfAware eval config is
  `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_dpo_seed1_full_local_4b.yaml`.
- 2026-06-25: full SelfAware eval completed cleanly with `n=3369`, no thinking
  tags, `100%` response-confidence coverage, and zero retries. Metrics:
  `truthful_pct=41.64`, `refusal_recall_pct=93.31`,
  `answer_on_unknown_pct=6.69`, `over_refusal_pct=63.63`,
  `correct_on_known_pct=51.76`, mean response confidence `0.866301`, Brier vs
  response appropriateness `0.445413`. Interpretation: modestly lower
  over-refusal than direct GRPO v2 while preserving low unknown answering, but
  confidence remains high and behavior-insensitive.

## Clean SFT -> GRPO -> KTO

### Question & Hypothesis

Can KTO soften `clean SFT -> GRPO v2` over-refusal while preserving the improved
unknown-row abstention boundary?

This is an Amendment F experiment under `experiments/grpo-centered-stacking/AMENDMENT.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** GRPO installs the refusal boundary, then KTO's unpaired signal
  reduces excessive known-row refusals without the stronger DPO tendency to
  answer unknowns.
- **Falsifier.** KTO after GRPO raises unknown answering or mostly increases
  stated confidence while leaving the behavior tradeoff unchanged.

### Design

Arm: `clean_sft_grpo_kto`, defined as clean Amendment E SFT, then GRPO v2, then
KTO over the same response-confidence desirable/undesirable dataset.

Primary comparator set:

- clean SFT merged seed 1;
- clean SFT->GRPO v2 seed 1;
- clean SFT->KTO corrected-base seed 1;
- Amendment E grouped comparison table.

Metrics: full SelfAware truthful percentage, unknown refusal recall, unknown
answer rate, known over-refusal, correct-on-known among answered known rows,
response-confidence coverage, confidence distribution by behavioral cell, and
Brier/MAE versus response appropriateness.

### Prerequisites & Gating

- Source `clean_schema_sft_grpo_v2_seed1_corrected_base` full eval exists.
- Merge the GRPO v2 adapter onto the clean SFT merged base before KTO.
- Run a bounded merged-source SelfAware sanity eval before KTO launch.
- Confirm KTO config uses the merged SFT->GRPO v2 model as base.
- Confirm Docker/GPU capacity; KTO may use the Amendment E batch 12 /
  accumulation 1 plan only with live monitoring and fallback to batch 8 if VRAM
  risk rises.

### Runbook

1. Read `experiments/grpo-centered-stacking/AMENDMENT.md` and
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`.
2. Compare source-arm metrics against
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Materialize a KTO launch config/command using the KTO section in
   `experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md`, changing only
   the base model/output labels for `clean_sft_grpo_kto`.
4. Launch the merged-source sanity eval using the existing eval-config pattern in
   `experiment/phase1/eval/config/`.
5. If sanity passes, launch KTO locally from the merged GRPO v2 source model.
6. Run the full SelfAware eval, rebuild the comparison CSV with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py`, and
   write a `docs/sessions/` checkpoint.

### Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, GRPO v2 adapter, merge
  path, and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** KTO training has final artifacts, training lineage points at the
  merged GRPO v2 source, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->GRPO v2, and SFT->KTO.

### Outputs & provenance

- Run record: `experiment/phase1/run_records/`.
- Session checkpoint: `docs/sessions/`.
- Analysis: `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  and grouped companion.
- Hugging Face publication is allowed only after eval passes: publish public
  adapter/config/model-card artifacts and a repository pointer to the data
  recipe, not restricted raw data or large unreviewed run products.
- Results remain Amendment F exploratory evidence and do not enter PROTOCOL v0.3
  headline claims.

### Variations

- Seed 1 local only until the arm is interpretable.
- Batch 12 / accumulation 1 is provisional and must be monitored; fallback batch
  8 / accumulation 1 remains acceptable.
- Seeds 2/3 are deferred until seed 1 improves the immediate source tradeoff.

### Status log

- 2026-06-24: created (proposed) as one of four Amendment F GRPO-centered
  stacking experiment notes.
- 2026-06-25: staged the shared GRPO-v2 merged-source sanity eval config at
  `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_v2_merged_seed1_sanity_local_4b.yaml`.
  Actual merge, sanity eval, and KTO launch remain gated on the active
  `clean_sft_kto_grpo` full eval completing and the preceding
  `clean_sft_grpo_dpo` decision point.
- 2026-06-25: preceding `clean_sft_grpo_dpo` arm completed and passed structural
  eval sanity; `clean_sft_grpo_kto` is the next Amendment F arm to launch from
  the already sanity-gated merged clean SFT->GRPO v2 source model.
- 2026-06-25: launched local KTO run in
  `eh-clean-sft-grpo-kto-seed1-full-20260625a` using run dir
  `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610`.
  Step-250 monitoring passed at batch 12 / accumulation 1 with max reserved
  VRAM `16.639 GB` and OOM risk `low`; mid-run objective separation is strong,
  so the full SelfAware eval will decide whether this is useful behavior or only
  another KTO separation artifact. Full eval config:
  `experiment/phase1/eval/config/eval_amendment_f_response_confidence_selfaware_clean_sft_grpo_kto_seed1_full_local_4b.yaml`.
- 2026-06-25: KTO training completed successfully at step 2491 with final
  adapter artifacts in
  `scratch/schema_response_confidence/runs/clean_sft_grpo_kto_seed1_full/20260625_052610/final_model`.
  Peak reserved VRAM reached `21.412 GB` (`89.22%`) with final risk `moderate`,
  so batch 12 is usable but should not be treated as having large headroom. The
  full SelfAware eval is running in
  `eh-clean-sft-grpo-kto-full-eval-20260625a`.
- 2026-06-25: full SelfAware eval completed cleanly with `n=3369`, no thinking
  tags, `100%` response-confidence coverage, and zero retries. Metrics:
  `truthful_pct=40.90`, `refusal_recall_pct=89.63`,
  `answer_on_unknown_pct=10.37`, `over_refusal_pct=60.59`,
  `correct_on_known_pct=49.19`, mean response confidence `0.864039`, Brier vs
  response appropriateness `0.448626`. Interpretation: KTO after GRPO softened
  GRPO's known over-refusal but reopened unknown answering and left confidence
  collapsed high; `clean_sft_grpo_dpo` is the stronger Amendment F seed-1 stack
  on truthful rate and unknown-answer control.

## Clean SFT -> KTO -> GRPO

### Question & Hypothesis

Can GRPO improve a less destructive `clean SFT -> KTO` policy by increasing
unknown-row abstention while preserving KTO's lower known-row over-refusal?

This is an Amendment F experiment under `experiments/grpo-centered-stacking/AMENDMENT.md`;
it is outside locked PROTOCOL v0.3 headline reporting.

- **Hypothesis.** KTO is a gentler first preference pass than DPO; GRPO can then
  tighten the refusal boundary without starting from a severely answer-prone
  policy.
- **Falsifier.** GRPO pushes the KTO-warmed model into the same over-refusal
  profile as direct SFT->GRPO, or KTO's higher unknown-answer rate persists.

### Design

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

### Prerequisites & Gating

- Source `clean_schema_sft_kto_seed1_corrected_base` full eval exists and is not
  lineage-confounded.
- Merge the KTO adapter onto the clean SFT merged base before GRPO.
- Run a bounded merged-source SelfAware sanity eval before GRPO launch.
- Confirm GRPO config uses the merged SFT->KTO model as `model.model_name`.
- Confirm Docker/GPU is idle enough for GRPO and record `nvidia-smi` before
  launch.

### Runbook

1. Read `experiments/grpo-centered-stacking/AMENDMENT.md` and
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

### Validation contract

- **Pre-run.** Source lineage identifies clean SFT base, KTO adapter, merge path,
  and eval result. The sanity eval is not base-like or schema-broken.
- **Post-run.** GRPO training has final artifacts, reward debug rows have
  nonzero reward variance, and eval has 100% `answer` + `response_confidence`
  coverage.
- **Definition of done.** Full SelfAware metrics and row-level transition notes
  compare against clean SFT, SFT->KTO, and SFT->GRPO v2.

### Outputs & provenance

- Run record: `experiment/phase1/run_records/`.
- Session checkpoint: `docs/sessions/`.
- Analysis: `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`
  and grouped companion.
- Hugging Face publication is allowed only after eval passes: publish public
  adapter/config/model-card artifacts and a repository pointer to the data
  recipe, not restricted raw data or large unreviewed run products.
- Results remain Amendment F exploratory evidence and do not enter PROTOCOL v0.3
  headline claims.

### Variations

- Seed 1 local only until the arm is interpretable.
- Seeds 2/3 are deferred until seed 1 beats or clearly diagnoses the immediate
  source arm.
- If GRPO v3 supersedes v2 before launch, update Amendment F and this note before
  training.

### Status log

- 2026-06-24: created (proposed) as one of four Amendment F GRPO-centered
  stacking experiment notes.
- 2026-06-25: staged the seed-1 GRPO config and bounded merged-source sanity
  eval config. Merge and sanity launch remain gated on the active
  `clean_sft_dpo_grpo` full eval freeing the local GPU.
- 2026-06-25: merged the clean SFT->KTO seed-1 adapter, passed the bounded
  merged-source sanity eval, and launched the full local `clean_sft_kto_grpo`
  GRPO run in container `eh-clean-sft-kto-grpo-seed1-full-20260625a`.
- 2026-06-25: full GRPO training completed at step 1861 with final loss 0.1162,
  low OOM risk, and final adapter artifacts in
  `scratch/schema_response_confidence/runs/clean_sft_kto_grpo_seed1_full/20260625_012319/final_model`.
  The full SelfAware eval is running in
  `eh-clean-sft-kto-grpo-full-eval-20260625a`.
- 2026-06-25: full SelfAware eval completed with `truthful_pct=40.84`,
  `answer_on_unknown_pct=7.46`, `over_refusal_pct=66.37`,
  `correct_on_known_pct=53.56`, and mean response confidence `0.862188`. The
  arm is structurally valid but converges to the same GRPO-final tradeoff and a
  five-value confidence collapse.
