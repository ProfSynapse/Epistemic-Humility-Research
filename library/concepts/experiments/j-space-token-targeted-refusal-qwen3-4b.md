---
title: j-space-token-targeted-refusal-qwen3-4b
aliases:
- J-space token-targeted refusal write
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:j-space-token-targeted-refusal-qwen3-4b
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[j-space-localization-qwen3-4b]]'
- '[[j-space-midband-dose-calibration-qwen3-4b]]'
relationships:
- type: supports
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: low
  evidence:
  - experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-token-targeted-refusal-qwen3-4b/analysis-committed/full_summary.json
- type: builds_on
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md#outcome
- type: builds_on
  target: '[[j-space-midband-dose-calibration-qwen3-4b]]'
  target_id: experiment:j-space-midband-dose-calibration-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md#outcome
---

Token-targeted J-space refusal write experiment on raw-base Qwen3-4B. The
natural token-target direction wrote accurately and was non-inert, but it did
not materially improve over the calibrated mid-band caution write.

This is exploratory successor evidence constraining, rather than confirming, the
J-space actuation mechanism. Source of truth:
`experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md`.
