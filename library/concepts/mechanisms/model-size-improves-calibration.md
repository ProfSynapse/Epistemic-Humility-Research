---
aliases:
- Model Size Improves Calibration
- Model Scale Improves Calibration
- model-scale-improves-calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-size-improves-calibration
  type: mechanism
  status: canonical
cause: Increasing language model parameter count (800M to 52B) on diverse multiple-choice and True/False tasks with appropriate formatting
effect: Lower [[expected-calibration-error]] and better-calibrated probability predictions across BIG Bench, [[mmlu]], [[truthfulqa]], and other evaluations
polarity: decreases
related:
- '[[2207.05221--lms-mostly-know-what-they-know]]'
- '[[2306.13063--can-llms-express-uncertainty]]'
- '[[expected-calibration-error]]'
- '[[mmlu]]'
- '[[truthfulqa]]'
relationships:
- type: supported_by
  target: '[[2207.05221--lms-mostly-know-what-they-know]]'
  target_id: paper:2207.05221
  confidence: high
- type: supported_by
  target: '[[2306.13063--can-llms-express-uncertainty]]'
  target_id: paper:2306.13063
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
---

Larger models encode richer factual knowledge and develop more reliable internal representations of answer confidence, which translates to better-calibrated output probabilities. The "LMs Mostly Know What They Know" paper (arXiv:2207.05221) documents this trend systematically across 800M to 52B parameter models, finding that scale is one of the most reliable predictors of calibration quality. The effect holds across multiple benchmark formats and task types, consistent with neural scaling law predictions.
