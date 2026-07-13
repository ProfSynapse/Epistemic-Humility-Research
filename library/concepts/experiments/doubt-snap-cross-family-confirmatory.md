---
title: doubt-snap-cross-family-confirmatory
aliases:
- doubt-gated caution snap cross-family confirmatory replication
tags:
- kg/experiment
- experiment
- cross-family
- doubt-snap
kg:
  id: experiment:doubt-snap-cross-family-confirmatory
  type: experiment
  status: draft
related:
- '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
- '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
relationships:
- type: supports
  target: '[[qwen35-late-site-entangles-refusal-and-format-collapse]]'
  target_id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 and 2026-07-10 entries)
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md (dose-recalibration note)
- type: supports
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 entry)
- type: supports
  target: '[[qwen35-batch-composition-flips-greedy-decode-outcomes]]'
  target_id: mechanism:qwen35-batch-composition-flips-greedy-decode-outcomes
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-08 12:20 and 08:55 entries)
---

Registered cross-family confirmatory replication of the resolved Qwen3-4B
doubt-gated-caution-tighten mechanism (a doubt-threshold gate plus a
caution-direction snap) across a Llama / Mistral-Ministral / Qwen3.5 / Gemma
small-and-mid-tier family panel, with FIT-only direction/tau/dose selection
per model and held-out G1/G2/G3 scoring. As of this writing the matrix is
still running (`experiment.yaml` status: running, verdict unfilled); this
note records only the two Qwen3.5 cells that have resolved, and does not
assert an overall cross-family verdict.

Both Qwen3.5 cells (qwen35_4b, qwen35_9b) failed the registered FIT
dose-viability gate (G0) before any held-out scoring. The audit of committed
FIT artifacts established this as overdose collapse specific to each
substrate's fitted write-direction scale, not a family null on the
mechanism itself: Qwen3.5-4B's fitted sigma_c (2.80) is about 4.7x smaller
than the Qwen3-4B exploratory reference, so the registered dose grid was
already tens of sigma too strong at its lowest rung. A pre-outcome per-cell
grid recalibration found a narrow coherent window peaking at only ~33%
clean_tighten (4B) and ~6% (9B), both well below the registered 60% bar, with
refusal induction and JSON well-formedness collapsing together at every
coherent dose. Both cells are recorded as G0 dose-viability fails, not held
out G1/G2/G3 fails, and are ineligible for the panel denominator. A separate
batch-composition non-determinism hazard, caught by the semantic-parity
smoke guard on these same two cells, is recorded as a procedural finding
rather than a substantive result.

Other family cells in the matrix are still in progress or unresolved as of
this writing. Source of truth: `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`
and `NOTEBOOK.md`.
