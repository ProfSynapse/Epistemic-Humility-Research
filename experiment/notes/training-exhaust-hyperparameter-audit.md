---
title: 'Training exhaust and hyperparameter audit'
kg:
  id: experiment:training-exhaust-hyperparameter-audit
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: exploratory
phase: phase1
lane: local
est_compute: 'No GPU required unless follow-up diagnostics are approved'
relationships:
  - type: tests
    target: '[[reverse-kl-narrows-policy-to-single-mode]]'
    target_id: mechanism:reverse-kl-narrows-policy-to-single-mode
    confidence: medium
  - type: tests
    target: '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
    target_id: mechanism:dpo-diversity-cost-depends-on-upstream-sft-state
    confidence: high
  - type: tests
    target: '[[lora-regularizes-calibration]]'
    target_id: mechanism:lora-regularizes-calibration
    confidence: medium
  - type: builds_on
    target: '[[lora-rank-changes-require-learning-rate-retuning]]'
    target_id: mechanism:lora-rank-changes-require-learning-rate-retuning
    confidence: high
  - type: builds_on
    target: '[[dpo-beta-should-follow-pair-quality]]'
    target_id: mechanism:dpo-beta-should-follow-pair-quality
    confidence: high
related:
  - '[[reverse-kl-narrows-policy-to-single-mode]]'
  - '[[dpo-diversity-cost-depends-on-upstream-sft-state]]'
  - '[[lora-regularizes-calibration]]'
  - '[[lora-rank-changes-require-learning-rate-retuning]]'
  - '[[dpo-beta-should-follow-pair-quality]]'
---

## Question & Hypothesis

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

## Design

This is an offline audit over:

- checked-in configs under `experiment/phase1/recipes/` and
  `experiment/phase1/grpo/configs/`;
- local scratch run exhaust under `scratch/schema_response_confidence/runs/`;
- durable eval metrics under `experiment/phase1/eval/analysis/`;
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

## Prerequisites & Gating

- Do not launch new sweeps while this audit is incomplete unless the user gives
  an exact override.
- Treat scratch artifacts as local evidence only; do not commit raw logs or
  model artifacts.
- Use KG search before external search for literature gaps.
- If external papers are newly relied on, ingest them with `kg-ingest` before
  using them as durable rationale.

## Runbook

1. Read current aggregate metrics from
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv`.
2. Inventory configs under `experiment/phase1/recipes/` and
   `experiment/phase1/grpo/configs/` for LR, beta, batch, accumulation, epochs,
   LoRA rank, alpha, dropout, and target modules.
3. Inventory local scratch logs under `scratch/schema_response_confidence/runs/`
   without committing raw run products.
4. Extract per-run summaries: final loss, reward means, reward component spread,
   schema validity, confidence distribution, completion length, batch size,
   throughput, and any checkpoint/sanity gates.
5. Join training summaries to full eval rows in
   `experiment/phase1/eval/analysis/selfaware_full_run_comparison.csv`.
6. Search the KG for hyperparameter mechanisms, then fill gaps with arXiv
   primary sources and ingest any paper used as rationale.
7. Write a recommendation checkpoint in
   `docs/sessions/0022 - 8b-scale-and-hyperparameter-planning.md` naming which
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

## Interim recommendation

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

## Validation contract

- **Pre-analysis.** Every included run has an identifiable config, output path,
  and eval metrics or is labeled as smoke/excluded.
- **Post-analysis.** The recommendation distinguishes optimization failure from
  data/reward/model-capacity failure and names concrete stop conditions for any
  proposed sweep.
- **Definition of done.** We can say whether LR/beta/KL/reward/LoRA changes are
  worth running before 8B, and why.

## Outputs & provenance

- Session checkpoint:
  `docs/sessions/0022 - 8b-scale-and-hyperparameter-planning.md`.
- Optional derived CSVs under `experiment/phase1/analysis/` if a parser is
  created.
- No raw logs, raw completions, model weights, or scratch artifacts committed.

## Variations

- Config-only audit: first pass, no scratch parsing.
- Scratch-log audit: parse local JSONL and trainer logs.
- Literature-backed sweep proposal: only after KG/arXiv review.
- Bounded smoke sweep: requires exact user approval for a named knob and arm.

## Status log

- 2026-06-25: created as a no-GPU audit plan before additional sensitivity runs.
- 2026-06-25: arXiv check identified four new candidate papers for LR/LoRA and
  DPO beta/KL sensitivity; all are currently NEW to the vault and require
  `kg-ingest` before they can support a launch recommendation.
- 2026-06-25: ingested `2602.06204` and `2407.08639`; added reusable mechanisms
  for LoRA rank/LR coupling and DPO beta/pair-quality coupling; generated
  `experiment/phase1/analysis/training_exhaust_summary.csv` and
  `experiment/phase1/analysis/training_exhaust_hyperparameter_report.md` from
  32 local scratch capacity/log artifacts.
