---
title: j-space-midband-dose-calibration-qwen3-4b
aliases:
- J-space midband dose calibration
tags:
- kg/experiment
- experiment
- j-space
kg:
  id: experiment:j-space-midband-dose-calibration-qwen3-4b
  type: experiment
  status: canonical
related:
- '[[j-space-mediated-actuation-fragility]]'
- '[[j-space-localization-qwen3-4b]]'
relationships:
- type: supports
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json
- type: builds_on
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: high
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md#outcome
---

Layer-specific dose calibration for J-space mid-band write sites on raw-base
Qwen3-4B. The calibration showed that earlier hs23/hs26 writes that collapsed at
coarse dose could be recovered with lower setpoints.

This is exploratory calibration evidence, not a standalone confirmatory claim.
Source of truth:
`experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`.
