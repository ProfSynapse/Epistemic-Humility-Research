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
  `experiment/phase1/probe/analysis/thinking_audit_128_1024/`.
- GPU is idle and Docker is available before launch.

## Runbook

1. Read `experiments/thinking-enabled-parallel-arm/AMENDMENT.md`.
2. Inspect bounded audit results in
   `experiment/phase1/probe/analysis/thinking_audit_128_1024/README.md`.
3. Create a full thinking-probe config by following the pattern in
   `experiment/phase1/probe/config/probe_thinking_audit_128_1024.yaml` and
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
