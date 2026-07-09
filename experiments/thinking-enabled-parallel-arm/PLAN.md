---
title: 'Thinking-enabled TriviaQA source probe'
kg:
  id: experiment:thinking-triviaqa-source-probe
  type: experiment
  status: canonical
tags:
  - kg/experiment
status: proposed
governance: amendment
phase: phase1
lane: local
est_compute: '~10-20 local RTX 3090 GPU-hours for a full 20k-row thinking probe, depending on token budget'
relationships:
  - type: tests
    target: '[[generation-discrimination-gap]]'
    target_id: term:generation-discrimination-gap
    confidence: high
related:
  - '[[generation-discrimination-gap]]'
---

## Question & Hypothesis

Does enabling Qwen3 thinking materially change the TriviaQA known/unknown source
labels that feed the Phase 1 epistemic-humility datasets?

This is an Amendment H experiment under
`experiments/thinking-enabled-parallel-arm/AMENDMENT.md`; it is
outside locked PROTOCOL v0.3 headline reporting.

The motivating literature includes
`library/notes/2410.02707--llms-know-more-than-they-show.md`, which supports
the concern that generation can understate latent knowledge.

- **Hypothesis.** Thinking mode will move some non-thinking unknown rows into
  discard or known because the model can recover final answers after an
  explicit reasoning trace.
- **Falsifier.** The thinking-aware label-transition table is mostly identity,
  or movement is dominated by trace truncation and exact-alias scorer artifacts.

## Design

Rerun the TriviaQA source probe on the same Qwen3 base family with
`enable_thinking: true`, preserving raw generations and scoring only final
answer text after the last `</think>`.

The bounded 2026-06-25 pilot already established the required implementation
posture:

- `max_new_tokens: 384` was invalid for interpretation because traces often did
  not close.
- `max_new_tokens: 1024` was usable but imperfect on 128 rows:
  3,303/4,096 sampled generations reached `post_think`.
- Exact TriviaQA alias scoring is conservative and should be interpreted with
  row-level examples when labels change.

Full-run acceptance should be based on extraction quality, label-transition
rates, and row review, not only aggregate counts.

## Prerequisites & Gating

- Non-thinking source probe exists at
  `experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`.
- Thinking extraction support exists in `experiment/phase1/probe/probe.py` and
  `experiment/phase1/probe/backends.py`.
- Probe tests pass:
  `python -m pytest experiment/phase1/probe/tests/test_probe_smoke.py -q`.
- The bounded audit artifacts exist under
  `experiments/thinking-enabled-parallel-arm/artifacts/thinking_audit_128_1024/`.
- GPU is idle and Docker is available before launch.

## Runbook

1. Read `experiments/thinking-enabled-parallel-arm/AMENDMENT.md`.
2. Inspect bounded audit results in
   `experiments/thinking-enabled-parallel-arm/artifacts/thinking_audit_128_1024/README.md`.
3. Create a full thinking-probe config by following the pattern in
   `experiments/thinking-enabled-parallel-arm/artifacts/configs/probe_thinking_audit_128_1024.yaml` and
   changing only `model.model_tag`, `probe_pool.max_questions`, and any
   explicitly approved token-budget values.
4. Run the probe with `experiment/phase1/probe/probe.py` inside the local Docker
   vLLM image, using a fresh output directory.
5. Compare thinking rows against the locked non-thinking rows with
   `experiment/phase1/probe/compare_thinking_probe_results.py`.
6. Review extraction-status counts and label-transition examples before
   deciding whether to rebuild datasets.
7. Record launch, heartbeat, result, and interpretation checkpoints in
   `docs/sessions/`.

## Validation contract

- **Pre-run.** Config has `model.enable_thinking: true`, unique `model_tag`,
  same `probe_pool.subset_seed` as the locked probe, and no existing output rows
  outside the configured subset.
- **During run.** Early rows show mostly `post_think` extraction; if
  `unterminated_thinking` dominates, stop and revise token budget or design.
- **Post-run.** Manifest exists, `n_questions` matches the configured cap,
  comparison `summary.json` exists, and row-level CSV joins by
  `probe_pool_row_key`.
- **Definition of done.** A session checkpoint states whether thinking-derived
  labels are accepted for downstream dataset rebuild, rejected, or require a
  larger token-budget/scorer-sensitivity study.

## Outputs & provenance

- Probe output: `experiment/phase1/probe/<thinking-model-tag>/`.
- Comparison output: `experiment/phase1/probe/analysis/<thinking-analysis-tag>/`.
- Session notes: `docs/sessions/`.
- Amendment: `experiments/thinking-enabled-parallel-arm/AMENDMENT.md`.

Results remain Amendment H exploratory evidence and do not replace locked
non-thinking source labels unless a later signed amendment explicitly says so.

## Variations

- Bounded 128-row / 1024-token audit: completed 2026-06-25.
- Full 20k-row / approved-token-budget probe: proposed.
- Optional scorer-sensitivity pass: proposed, only after the locked-scorer
  comparison is complete.

## Status log

- 2026-06-25: created after bounded audit showed moderate label movement but no
  basis for replacing the non-thinking source labels.

## Thinking-enabled training replication

### Question & Hypothesis

Do the current non-thinking fine-tuning results hold when the source labels,
training/eval prompts, and final measurements are built under a thinking-enabled
model posture?

This is an Amendment H experiment under
`experiments/thinking-enabled-parallel-arm/AMENDMENT.md`; it is
outside locked PROTOCOL v0.3 headline reporting.

The source-label concern is motivated by
`library/notes/2410.02707--llms-know-more-than-they-show.md` and by the local
bounded audit in `experiments/thinking-enabled-parallel-arm/artifacts/thinking_audit_128_1024/`.

- **Hypothesis.** Thinking-derived labels and thinking-enabled evaluation will
  change the measured abstention boundary enough that at least one regimen's
  tradeoff differs from the non-thinking branch.
- **Falsifier.** The same relative ranking of SFT, DPO, KTO, GRPO, and stacks
  appears under thinking with no material behavior or confidence deltas beyond
  normal seed variance.

### Design

This plan covers the downstream branch after the source-probe section above
accepts a thinking-derived source-label set.

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

### Prerequisites & Gating

- The source-probe section in this plan is complete or explicitly
  approved for the subset used.
- Thinking-derived datasets are rebuilt with leakage checks and provenance.
- Tuner/eval configs clearly label `thinking` in run IDs, output directories,
  and model tags.
- Eval configs use thinking-enabled generation and preserve final-answer
  extraction after `</think>`.
- Each sequential adapter is evaluated on the same base family it was trained
  from; lineage must be checked before launch.
- GPU/Docker is idle before each local launch.

### Runbook

1. Read `experiments/thinking-enabled-parallel-arm/AMENDMENT.md`.
2. Confirm the accepted source-label artifact from the source-probe section of
   this plan.
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

### Validation contract

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

### Outputs & provenance

- Run records: `experiment/phase1/run_records/`.
- Training/eval configs: `experiment/phase1/`.
- Eval analysis: `experiment/phase1/eval/analysis/`.
- Session notes: `docs/sessions/`.
- Public artifacts: deferred until a later publication decision; do not push
  thinking adapters or merged models before lineage, metrics, and model cards
  are ready.

Results remain Amendment H exploratory evidence. They should be reported beside
the non-thinking branch, not pooled with it.

### Variations

- Seed-1 full branch: proposed.
- Seed-2/3 best-arm replication: deferred until seed-1 thinking branch is
  interpretable.
- 8B thinking branch: deferred until local 4B thinking results justify scale.
- Thinking-at-eval-only control: optional diagnostic if training reruns are too
  costly or if source-label effects remain small.

### Status log

- 2026-06-25: created as the downstream Amendment H parallel-arm runbook. No
  training launch is authorized by this note.
- 2026-06-25: quick literature check found support for preference-derived
  reward feeding RL optimization via RTO, but no comparable reason to prioritize
  DPO/KTO reciprocal ordering. Default matrix narrowed to preference -> RL and
  RL -> preference three-step crossings.
