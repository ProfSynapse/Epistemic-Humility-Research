---
title: family-atlas-surface-matched-json-completion-control
aliases:
- Family Atlas Surface-Matched JSON-Completion Control
- JSON-completion Shape B control
tags:
- kg/experiment
- experiment
- mechanistic-interpretability
- cross-family
kg:
  id: experiment:family-atlas-surface-matched-json-completion-control
  type: experiment
  status: canonical
related:
- '[[family-atlas-surface-diversity-control]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
relationships:
- type: builds_on
  target: '[[family-atlas-surface-diversity-control]]'
  target_id: experiment:family-atlas-surface-diversity-control
  confidence: high
  evidence:
  - experiments/family-atlas-surface-matched-json-completion-control/AMENDMENT.md#instrument-tier
- type: builds_on
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-matched-json-completion-control/AMENDMENT.md#motivation
- type: builds_on
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-matched-json-completion-control/AMENDMENT.md#motivation
---

Tier 2 surface-matched-pool experiment designed to test whether the
early-exterior `eff_dim_frac` location survives on newly constructed
three-role pools for Gemma-4-E4B-it and Qwen3-4B. Its pinned vLLM generation
instrument completed all 5,200 registered rows per model and repaired all 11
known Gemma JSON-interface failures without changing the 5,189 previously valid
outputs.

The prerequisite surface-balance gate failed before full-depth capture. Gemma
FIT had maximum pairwise surface-only AUROC 0.7223 and maximum scalar absolute
SMD 0.5722; Qwen FIT had AUROC 0.6127 and SMD 0.2730, against registered
ceilings of 0.60 and 0.10. The planted surface-role-tag control reached AUROC
1.0 for both models, demonstrating that the sensor could detect a present
signal. The PI adjudicated the run as a null result caused by prerequisite
support failure. No controlled peak-location result was produced, so it does
not falsify the early-exterior prediction.

The complete retained generation exhaust was later used in a CPU-only
successor-design diagnostic. Full-size optimized matches were objective- and
seed-sensitive, and robust 50% support was not available across both models.
This motivates a separately registered full-population residualization
successor rather than further matched-subset search. Source of truth:
`experiments/family-atlas-surface-matched-json-completion-control/AMENDMENT.md`,
its committed G0-G2 summaries, and `NOTEBOOK.md`.
