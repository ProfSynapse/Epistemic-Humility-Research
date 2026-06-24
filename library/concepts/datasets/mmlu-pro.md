---
aliases:
- Massive Multitask Language Understanding Pro
- MMLU-Professional
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mmlu-pro
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.05126--metacognition-uncertainty-communication]]'
- '[[mmlu]]'
- '[[gsm8k]]'
- '[[triviaqa]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2510.05126--metacognition-uncertainty-communication]]'
  target_id: paper:2510.05126
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A harder variant of MMLU containing 12,032 college-level multiple-choice questions across 14 academic domains, with 83% of questions offering ten answer choices rather than four, making guessing substantially less effective than in the original MMLU benchmark.

**Why it matters here:** Serves as a standard expert-knowledge evaluation that is significantly harder than MMLU due to the expanded choice set; used as a training domain for metacognitive fine-tuning research and as a benchmark for calibration and discrimination under expert-level difficulty.

**Lineage:** Introduced by Wang et al. (2024) as a more challenging extension of the original MMLU benchmark.
