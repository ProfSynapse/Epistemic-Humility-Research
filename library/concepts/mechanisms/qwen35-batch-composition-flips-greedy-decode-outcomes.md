---
aliases:
- bf16 batch-composition non-determinism flips greedy-decode outcomes (Qwen3.5)
- batch size changes categorical steering outcomes on Qwen3.5
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  type: mechanism
  status: canonical
cause: "On Qwen3.5 (bf16), running greedy-decoding generation with per-row activation-intervention arms in a larger batch (16 or 32 rows) instead of a validated smaller reference batch (8 rows, or 1 row on the Modal cross-family cells), where bf16 batched matrix-multiply reduction order depends on which other rows are co-batched."
effect: "Most divergence from the smaller reference batch is superficial wording drift from shifted greedy tie-breaks (61 of 240 row-by-field comparisons diverged across batch 16/32 versus batch 8 on a 30-row local probe), but individual rows can flip categorically on the primary gate metrics: one row (kuq_unknowns_all:1041) refused at batch 8 (refused=True, clean_tighten=True) and was answered substantively at both batch 16 and batch 32 (refused=False, clean_tighten=False), reproduced identically at both larger sizes. The same hazard was independently observed on Modal A100 cross-family cells (Qwen3.5-9B passed a semantic-parity smoke at batch 1 and failed at batch 2; Qwen3.5-4B failed semantic parity at batch 8) before being reproduced on a local RTX 3090 mid-band probe, so evaluation cells on this model family must fix and validate one production batch size rather than assume batching is metric-neutral."
polarity: mediates
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
relationships:
- type: supported_by
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-08 12:20 and 08:55 entries)
- type: supported_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: high
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/NOTEBOOK.md (2026-07-10 batch-size probe entry)
---

Qwen3.5's batch-composition sensitivity surfaced twice, independently, before
being treated as a general hazard rather than a one-off smoke failure: first
on the Modal A100 cross-family cells, where the semantic-parity guard caught
a 4B/9B batch-size-dependent divergence that the original exact-token-match
guard had missed, and again on a local RTX 3090 probe for the mid-band
experiment, where a row-level trace isolated the effect to a single
categorical gate-metric flip reproduced identically at two different larger
batch sizes.

The practical consequence is procedural rather than substantive: this is not
evidence against the doubt-gated caution snap's selectivity, but it is
evidence that any Qwen3.5 evaluation cell must pin and validate its
production batch size (here, batch_size=8) against a smaller reference before
trusting per-row categorical outcomes such as refused or clean_tighten.
