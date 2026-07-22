---
title: family-atlas-surface-diversity-control
aliases:
- Family Atlas Surface-Diversity Control
- Shape A surface-diversity reanalysis
tags:
- kg/experiment
- experiment
- mechanistic-interpretability
- cross-family
kg:
  id: experiment:family-atlas-surface-diversity-control
  type: experiment
  status: canonical
related:
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
relationships:
- type: builds_on
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-diversity-control/AMENDMENT.md#substrates-and-existing-inputs
- type: builds_on
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-diversity-control/AMENDMENT.md#substrates-and-existing-inputs
---

CPU-only reanalysis designed to test whether the Gemma-4-E4B-it and Qwen3-4B
early-exterior `eff_dim_frac` peaks survive cross-fitted removal of activation
variance predictable from registered prompt-surface covariates. The signed
instrument reproduced both baseline profiles, but its prerequisite KUQ matching
support gate failed for both substrates. Gemma retained 293 pairs with
surface-role AUROC 0.643 and maximum scalar SMD 0.154; Qwen retained 108 pairs
with AUROC 0.610 and SMD 0.174, against registered ceilings of 0.60 and 0.10.

The hard stop prevented residualization, planted-signal, permutation, and peak-
location endpoints from running. The PI adjudicated this as a null result caused
by prerequisite support failure. It is indeterminate with respect to the
early-exterior prediction and supplies no evidence that the peak moved. Source
of truth: `experiments/family-atlas-surface-diversity-control/AMENDMENT.md` and
`analysis-committed/aggregate_results.json`.
