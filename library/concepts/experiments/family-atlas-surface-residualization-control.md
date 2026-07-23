---
title: family-atlas-surface-residualization-control
aliases:
- Family Atlas Surface Residualization Control
- Full-population Shape A residualization control
tags:
- kg/experiment
- experiment
- mechanistic-interpretability
- cross-family
kg:
  id: experiment:family-atlas-surface-residualization-control
  type: experiment
  status: canonical
related:
- '[[family-atlas-surface-diversity-control]]'
- '[[family-atlas-surface-matched-json-completion-control]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
relationships:
- type: builds_on
  target: '[[family-atlas-surface-diversity-control]]'
  target_id: experiment:family-atlas-surface-diversity-control
  confidence: high
  evidence:
  - experiments/family-atlas-surface-residualization-control/AMENDMENT.md#motivation
- type: builds_on
  target: '[[family-atlas-surface-matched-json-completion-control]]'
  target_id: experiment:family-atlas-surface-matched-json-completion-control
  confidence: high
  evidence:
  - experiments/family-atlas-surface-residualization-control/AMENDMENT.md#motivation
- type: builds_on
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-residualization-control/AMENDMENT.md#existing-substrates-and-population
- type: builds_on
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: high
  evidence:
  - experiments/family-atlas-surface-residualization-control/AMENDMENT.md#existing-substrates-and-population
---

CPU-only full-population reanalysis testing whether the early-exterior
`eff_dim_frac` peak survives cross-fitted removal of activation variance
predicted by a registered linear prompt-surface representation. The instrument
used all eligible fit rows from the existing Gemma-4-E4B-it and Qwen3-4B atlas
captures and retained reusable private matrices and out-of-fold predictions
without committing row-level content.

All registered gates passed. Gemma remained at hs4 (depth 0.095) and Qwen at
hs5 (0.139) in both the full-fit combined residual and fixed 50% stability
profiles. The surface models explained measurable early activation variance,
the planted hs2 surface peaks were removed, and all 20 permutation profiles per
substrate remained early-exterior. The pre-stated peak-location falsifier did
not fire.

The result rejects the registered linear prompt-surface account as an
explanation for the peak location on these two populations. It does not exclude
every nonlinear encoding of raw token sequences. Source of truth:
`experiments/family-atlas-surface-residualization-control/AMENDMENT.md` and
`analysis-committed/aggregate_results.json`.
