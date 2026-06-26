---
title: 'Thinking-enabled training regimen replication'
kg:
  id: experiment:thinking-enabled-training-replication
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: amendment
phase: phase1
lane: local
est_compute: '~30+ local RTX 3090 GPU-hours for seed-1 replication of the approved regimen family; seeds 2/3 add proportionally'
relationships:
  - type: tests
    target: '[[generation-discrimination-gap]]'
    target_id: term:generation-discrimination-gap
    confidence: high
  - type: tests
    target: '[[grpo-composite-reward-installs-epistemic-output-schema]]'
    target_id: mechanism:grpo-composite-reward-installs-epistemic-output-schema
    confidence: medium
related:
  - '[[generation-discrimination-gap]]'
  - '[[grpo-composite-reward-installs-epistemic-output-schema]]'
---

## Question & Hypothesis

Do the current non-thinking fine-tuning results hold when the source labels,
training/eval prompts, and final measurements are built under a thinking-enabled
model posture?

This is an Amendment H experiment under
`experiment/protocol/AMENDMENT-H-thinking-enabled-parallel-arm.md`; it is
outside locked PROTOCOL v0.3 headline reporting.

The source-label concern is motivated by
`library/notes/2410.02707--llms-know-more-than-they-show.md` and by the local
bounded audit in `experiment/phase1/probe/analysis/thinking_audit_128_1024/`.

- **Hypothesis.** Thinking-derived labels and thinking-enabled evaluation will
  change the measured abstention boundary enough that at least one regimen's
  tradeoff differs from the non-thinking branch.
- **Falsifier.** The same relative ranking of SFT, DPO, KTO, GRPO, and stacks
  appears under thinking with no material behavior or confidence deltas beyond
  normal seed variance.

## Design

This note covers the downstream branch after
`experiment/notes/thinking-triviaqa-source-probe.md` accepts a thinking-derived
source-label set.

The branch mirrors the active non-thinking response-confidence family rather
than replacing it. Seed 1 is the first plumbing and behavior screen. Seeds 2/3
are reserved for best-arm replication once the seed-1 thinking branch is
interpretable.

Candidate regimen family:

| Arm | Dependency | Purpose |
|---|---|---|
| thinking SFT | thinking-derived source dataset | Teach final response/schema behavior from thinking labels. |
| thinking SFT -> DPO | merged thinking SFT | Test paired preference shaping after thinking-derived SFT. |
| thinking SFT -> KTO | merged thinking SFT | Test unpaired preference shaping after thinking-derived SFT. |
| thinking SFT -> GRPO | merged thinking SFT | Test reward shaping after thinking-derived SFT. |
| thinking SFT -> DPO -> GRPO | merged thinking SFT->DPO | Test whether GRPO recovers unknown abstention after DPO. |
| thinking SFT -> GRPO -> DPO | merged thinking SFT->GRPO | Test whether the current best non-thinking stack reproduces. |
| thinking SFT -> KTO -> GRPO | merged thinking SFT->KTO | Test KTO-first stacking. |
| thinking SFT -> GRPO -> KTO | merged thinking SFT->GRPO | Test KTO-after-GRPO stacking. |

Deferred reciprocal preference-family stacks:

| Arm | Status | Rationale |
|---|---|---|
| thinking SFT -> DPO -> KTO | deferred | DPO and KTO are both offline preference-family objectives; current literature check did not show a strong distinct ordering mechanism. |
| thinking SFT -> KTO -> DPO | deferred | Deprioritized for the same reason; revisit only if a concrete failure mode calls for reciprocal preference stacking. |

Training targets should remain final-answer / final-JSON targets unless a later
amendment explicitly adds synthetic reasoning traces. The thinking branch is
about the model operating with thinking enabled, not about inventing unverified
chain-of-thought supervision.

## Prerequisites & Gating

- `experiment/notes/thinking-triviaqa-source-probe.md` is complete or explicitly
  approved for the subset used.
- Thinking-derived datasets are rebuilt with leakage checks and provenance.
- Tuner/eval configs clearly label `thinking` in run IDs, output directories,
  and model tags.
- Eval configs use thinking-enabled generation and preserve final-answer
  extraction after `</think>`.
- Each sequential adapter is evaluated on the same base family it was trained
  from; lineage must be checked before launch.
- GPU/Docker is idle before each local launch.

## Runbook

1. Read `experiment/protocol/AMENDMENT-H-thinking-enabled-parallel-arm.md`.
2. Confirm the accepted source-label artifact from
   `experiment/notes/thinking-triviaqa-source-probe.md`.
3. Build thinking-derived SFT/DPO/KTO/GRPO datasets using checked-in data-build
   scripts under `experiment/phase1/data/`.
4. Launch the seed-1 thinking SFT through the existing local training recipe
   pattern under `experiment/phase1/recipes/` or a documented Amendment H
   materialized recipe.
5. Merge the thinking SFT model and run a full thinking-enabled SelfAware eval
   before launching downstream preference/reward arms.
6. Launch DPO/KTO/GRPO only from the accepted merged thinking SFT source.
7. For each stack, merge the intermediate model, run a bounded sanity eval, then
   train/eval the next stage.
8. Rebuild comparison tables with
   `experiment/phase1/eval/analysis/build_selfaware_full_run_comparison.py` and
   add a thinking-specific grouped comparison.
9. Record run records and session checkpoints under `experiment/phase1/run_records/`
   and `docs/sessions/`.

## Validation contract

- **Pre-run.** Dataset provenance points to the thinking source probe; configs
  include thinking labels in output paths; lineage points to the intended
  same-branch source checkpoint.
- **During run.** Early output QA checks final-answer extraction, schema
  coverage, confidence distribution, and reward/debug rows where applicable.
- **Post-run.** Each arm has final artifacts, full eval metrics, row samples,
  and comparison against matched non-thinking controls.
- **Definition of done.** A result checkpoint ranks the thinking branch against
  its matched non-thinking controls and states whether the same next-best arm is
  still favored.

## Outputs & provenance

- Run records: `experiment/phase1/run_records/`.
- Training/eval configs: `experiment/phase1/`.
- Eval analysis: `experiment/phase1/eval/analysis/`.
- Session notes: `docs/sessions/`.
- Public artifacts: deferred until a later publication decision; do not push
  thinking adapters or merged models before lineage, metrics, and model cards
  are ready.

Results remain Amendment H exploratory evidence. They should be reported beside
the non-thinking branch, not pooled with it.

## Variations

- Seed-1 full branch: proposed.
- Seed-2/3 best-arm replication: deferred until seed-1 thinking branch is
  interpretable.
- 8B thinking branch: deferred until local 4B thinking results justify scale.
- Thinking-at-eval-only control: optional diagnostic if training reruns are too
  costly or if source-label effects remain small.

## Status log

- 2026-06-25: created as the downstream Amendment H parallel-arm runbook. No
  training launch is authorized by this note.
- 2026-06-25: quick literature check found support for preference-derived
  reward feeding RL optimization via RTO, but no comparable reason to prioritize
  DPO/KTO reciprocal ordering. Default matrix narrowed to preference -> RL and
  RL -> preference three-step crossings.
