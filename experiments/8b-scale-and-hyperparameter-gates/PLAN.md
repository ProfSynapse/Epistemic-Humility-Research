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
track: training-regimen
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
- Run the hyperparameter/training-exhaust audit summarized in this plan before adding new
  LR, beta, KL, reward-weight, epoch, or LoRA-rank variants.

## Runbook

1. Read `experiments/8b-scale-and-hyperparameter-gates/AMENDMENT.md`.
2. Compare current 4B results in
   `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
3. Check existing 8B recipes under `archive/experiment/phase1/recipes/`.
4. For thinking variants, follow
   `experiments/thinking-enabled-parallel-arm/PLAN.md` and adapt the source
   probe to Qwen3-8B before building datasets.
5. For non-thinking Tier 1, prepare exact configs and run records only after
   source labels, lane, seed, and output paths are approved.
6. After each cell, run full SelfAware response-confidence eval and rebuild
   `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`.
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
- Run records: `archive/experiment/phase1/run_records/`.
- Eval analysis: `archive/experiment/phase1/eval/analysis/`.
- No model weights, raw generated rows, or large artifacts should be committed.

## Variations

- Tier 1 non-thinking seed 1: proposed.
- Tier 2 non-thinking seed 1: deferred until Tier 1.
- Tier 3 thinking 8B source probe: proposed before any thinking 8B training.
- HF Jobs lane: deferred until local process and artifact policy are settled.

## Status log

- 2026-06-25: created as the 8B variant map. No launch authorized.

## Training exhaust and hyperparameter audit

### Question & Hypothesis

Before spending compute on LR, beta, KL, reward-weight, epoch, batch, or LoRA
rank sweeps, what do the existing local training logs and relevant literature
say is most likely to move behavior?

- **Hypothesis.** Some knobs may be low-ROI because prior runs already show
  objective separation without SelfAware behavior movement, implying data or
  reward design is tighter than optimization. Other knobs may be justified if
  logs show undertraining, reward saturation, instability, or confidence-gradient
  collapse.
- **Falsifier.** The local exhaust is too incomplete to distinguish saturation
  from undertraining, or literature points to a different missing variable that
  we are not logging.

### Design

This is an offline audit over:

- checked-in configs under `archive/experiment/phase1/recipes/` and
  `archive/experiment/phase1/grpo/configs/`;
- local scratch run exhaust under `scratch/schema_response_confidence/runs/`;
- durable eval metrics under `archive/experiment/phase1/eval/analysis/`;
- relevant KG notes and papers on DPO beta/KL, GRPO KL/reward variance, LoRA
  capacity, data composition, and post-training diversity collapse.

Questions to answer by arm:

| Arm family | Audit focus |
|---|---|
| SFT | loss trend, schema learning, confidence target diversity, over-refusal onset, LoRA rank/alpha capacity. |
| DPO | chosen/rejected reward gap, beta/KL strength, whether objective separation maps to behavior. |
| KTO | desirable/undesirable reward separation, loss saturation, over-answering or over-refusal transitions. |
| GRPO | reward component variance, group reward spread, schema validity, behavior reward vs confidence reward, KL/beta effects. |
| Stacks | whether later stages overwrite, preserve, or merely re-confidence the source behavior. |

### Prerequisites & Gating

- Do not launch new sweeps while this audit is incomplete unless the user gives
  an exact override.
- Treat scratch artifacts as local evidence only; do not commit raw logs or
  model artifacts.
- Use KG search before external search for literature gaps.
- If external papers are newly relied on, ingest them with `kg-ingest` before
  using them as durable rationale.

### Runbook

1. Read current aggregate metrics from
   `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
2. Inventory configs under `archive/experiment/phase1/recipes/` and
   `archive/experiment/phase1/grpo/configs/` for LR, beta, batch, accumulation, epochs,
   LoRA rank, alpha, dropout, and target modules.
3. Inventory local scratch logs under `scratch/schema_response_confidence/runs/`
   without committing raw run products.
4. Extract per-run summaries: final loss, reward means, reward component spread,
   schema validity, confidence distribution, completion length, batch size,
   throughput, and any checkpoint/sanity gates.
5. Join training summaries to full eval rows in
   `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`.
6. Search the KG for hyperparameter mechanisms, then fill gaps with arXiv
   primary sources and ingest any paper used as rationale.
7. Write a recommendation checkpoint in
   `docs/sessions/20260625T141548Z-8b-scale-and-hyperparameter-planning.md` naming which
   knob, if any, deserves a bounded sweep.

Initial external ingestion candidates from the 2026-06-25 arXiv check:

| Paper | Why inspect before sweeps |
|---|---|
| `2602.04998` / Learning Rate Matters | Tests whether apparent LoRA-method gains disappear once LR is tuned. |
| `2602.06204` / Learning Rate Scaling across LoRA Ranks | Directly addresses LR scaling when changing LoRA rank. |
| `2407.08639` / beta-DPO | Directly argues DPO beta should vary with preference-data informativeness. |
| `2502.13177` / epsilon-DPO | Directly targets adaptive per-pair KL/beta control in DPO. |

`2602.06204` and `2407.08639` were ingested on 2026-06-25 and can now be used
as durable rationale. `2602.04998` and `2502.13177` remain candidates, not
launch rationale.

### Interim recommendation

- Do not blanket-increase batch size. DPO has local headroom and can be probed
  upward only after the objective/reward target is worth rerunning; KTO is near
  the local RTX 3090 ceiling at batch 12; GRPO batch 32 is already the practical
  starting point.
- Do not run a LoRA-rank sweep by changing rank alone. The ingested LoRA scaling
  paper supports coupling rank with learning-rate/effective-multiplier logic.
- Do not treat beta as an arbitrary scalar sweep. The ingested beta-DPO paper
  supports auditing preference-pair gap/quality before choosing beta values.
- The highest-ROI next experimental branch is still either 8B Tier 1 or mech
  interp, not a blind 4B LR/beta/rank grid. A bounded 4B diagnostic is justified
  only if it answers a specific design question for 8B.

### Validation contract

- **Pre-analysis.** Every included run has an identifiable config, output path,
  and eval metrics or is labeled as smoke/excluded.
- **Post-analysis.** The recommendation distinguishes optimization failure from
  data/reward/model-capacity failure and names concrete stop conditions for any
  proposed sweep.
- **Definition of done.** We can say whether LR/beta/KL/reward/LoRA changes are
  worth running before 8B, and why.

### Outputs & provenance

- Session checkpoint:
  `docs/sessions/20260625T141548Z-8b-scale-and-hyperparameter-planning.md`.
- Optional derived CSVs under `archive/experiment/phase1/analysis/` if a parser is
  created.
- No raw logs, raw completions, model weights, or scratch artifacts committed.

### Variations

- Config-only audit: first pass, no scratch parsing.
- Scratch-log audit: parse local JSONL and trainer logs.
- Literature-backed sweep proposal: only after KG/arXiv review.
- Bounded smoke sweep: requires exact user approval for a named knob and arm.

### Status log

- 2026-06-25: created as a no-GPU audit plan before additional sensitivity runs.
- 2026-06-25: arXiv check identified four new candidate papers for LR/LoRA and
  DPO beta/KL sensitivity; all are currently NEW to the vault and require
  `kg-ingest` before they can support a launch recommendation.
- 2026-06-25: ingested `2602.06204` and `2407.08639`; added reusable mechanisms
  for LoRA rank/LR coupling and DPO beta/pair-quality coupling; generated
  `archive/experiment/phase1/analysis/training_exhaust_summary.csv` and
  `archive/experiment/phase1/analysis/training_exhaust_hyperparameter_report.md` from
  32 local scratch capacity/log artifacts.
