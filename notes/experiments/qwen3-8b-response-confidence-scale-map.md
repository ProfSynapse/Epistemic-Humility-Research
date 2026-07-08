---
title: 'Qwen3-8B response-confidence scale map'
kg:
  id: experiment:qwen3-8b-response-confidence-scale-map
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: amendment
phase: phase1
lane: either
est_compute: 'Tiered: Tier 1 is at least three 8B train/eval cells; Tier 2 and thinking variants add substantial local or HF Jobs compute'
relationships:
  - type: tests
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: high
  - type: tests
    target: '[[generation-discrimination-gap]]'
    target_id: term:generation-discrimination-gap
    confidence: medium
related:
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
  - '[[generation-discrimination-gap]]'
---

## Question & Hypothesis

Do the clean response-confidence and GRPO-centered findings from Qwen3-4B become
larger, cleaner, or more calibratable at Qwen3-8B?

This is an Amendment I planning note under
`experiments/8b-scale-and-hyperparameter-gates/AMENDMENT.md`; it does
not authorize local or cloud launches.

- **Hypothesis.** 8B has enough capacity that clean SFT and GRPO-centered stacks
  will move the refusal/known-answer tradeoff more cleanly than 4B, and may show
  less confidence collapse.
- **Falsifier.** The 8B Tier 1 screen reproduces the same small behavioral gains
  and high-confidence collapse as 4B, or source-label differences make the
  comparison uninterpretable.

The scale question is also informed by
`library/notes/2604.16027--posttraining-diversity-collapse.md`, which cautions
that post-training effects can be dominated by data composition and upstream
state rather than the nominal training method alone.

## Design

Use tiers rather than a flat matrix.

Tier 0 is the locked PROTOCOL v0.3 plain-answer 8B confirm: SFT, DPO, and KTO
across seeds 1-3. It remains separate from this response-confidence scale map.

Tier 1 is the minimal clean response-confidence 8B screen:

| Arm | Role |
|---|---|
| `8b_clean_sft` | Establish 8B schema, abstention, and confidence behavior. |
| `8b_clean_sft_grpo_v2` | Test whether GRPO v2 reward shaping has more leverage at 8B. |
| `8b_clean_sft_grpo_dpo` | Test whether the best 4B seed-1 stack scales. |

Tier 2 is the full seed-1 8B mirror of the 4B clean matrix:

| Arm | Role |
|---|---|
| `8b_clean_sft_dpo` | Two-stage DPO comparator. |
| `8b_clean_sft_kto` | Two-stage KTO comparator. |
| `8b_clean_sft_dpo_grpo` | Preference -> RL crossing. |
| `8b_clean_sft_kto_grpo` | Preference -> RL crossing. |
| `8b_clean_sft_grpo_kto` | RL -> preference crossing. |

Tier 3 is the 8B thinking-enabled branch. It starts with 8B source probes, not
training: Qwen3-8B non-thinking TriviaQA, Qwen3-8B thinking TriviaQA, row-level
label-transition review, then thinking-derived dataset builds. Training mirrors
Tier 1 first.

## Prerequisites & Gating

- Amendment I must be signed or exact cells must be approved before launch.
- Confirm Docker/GPU or HF Jobs lane separately for each 8B cell.
- Build or verify Qwen3-8B source labels before response-confidence training.
- Thinking 8B must have its own accepted source probe; 4B thinking labels are
  comparators only.
- Run the hyperparameter/training-exhaust audit in
  `notes/experiments/training-exhaust-hyperparameter-audit.md` before adding new
  LR, beta, KL, reward-weight, epoch, or LoRA-rank variants.

## Runbook

1. Read `experiments/8b-scale-and-hyperparameter-gates/AMENDMENT.md`.
2. Compare current 4B results in
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Check existing 8B recipes under `experiment/phase1/recipes/`.
4. For thinking variants, follow
   `notes/experiments/thinking-triviaqa-source-probe.md` and adapt the source
   probe to Qwen3-8B before building datasets.
5. For non-thinking Tier 1, prepare exact configs and run records only after
   source labels, lane, seed, and output paths are approved.
6. After each cell, run full SelfAware response-confidence eval and rebuild
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`.
7. Checkpoint results in
   `docs/sessions/20260625T141548Z-8b-scale-and-hyperparameter-planning.md` or a later
   launch-specific session note.

## Validation contract

- **Pre-run.** Source labels and dataset cards are model-size-specific; configs
  name Qwen3-8B; output paths encode 8B, thinking mode, seed, and tier.
- **Post-run.** Eval has `n=3369` where SelfAware full eval is used, response
  confidence coverage is reported, and row-level transitions compare against
  matched 4B and same-size source arms.
- **Definition of done.** Tier 1 has enough evidence to decide whether 8B scale
  justifies Tier 2, thinking 8B, or HF Jobs parallelization.

## Outputs & provenance

- Protocol: `experiments/8b-scale-and-hyperparameter-gates/AMENDMENT.md`.
- Session: `docs/sessions/20260625T141548Z-8b-scale-and-hyperparameter-planning.md`.
- Run records: `experiment/phase1/run_records/`.
- Eval analysis: `experiment/phase1/eval/analysis/`.
- No model weights, raw generated rows, or large artifacts should be committed.

## Variations

- Tier 1 non-thinking seed 1: proposed.
- Tier 2 non-thinking seed 1: deferred until Tier 1.
- Tier 3 thinking 8B source probe: proposed before any thinking 8B training.
- HF Jobs lane: deferred until local process and artifact policy are settled.

## Status log

- 2026-06-25: created as the 8B variant map. No launch authorized.
