---
title: j-space-calibrated-layer-contrast-qwen3-4b
aliases:
- calibrated J-space layer contrast
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
relationships:
- type: supports
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/analysis-committed/full_summary.json
---

Held-out raw-base Qwen3-4B bf16 causal contrast comparing calibrated mid-band
J-space write sites hs23, hs26, and hs29 against the late hs34 predecessor
reference. The experiment resolved as an exploratory pass on 2026-07-08:
hs23 beat hs34 clean_tighten by 22.7 percentage points with only +0.78
percentage points known-correct cost, while hs34 remained viable.

This is surface-local causal support for the J-space layer-site account, not a
cross-family or headline confirmatory result. Source of truth:
`experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md`.
