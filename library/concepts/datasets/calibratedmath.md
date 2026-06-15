---
aliases:
- CalibratedMath suite
- Calibrated Math
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:calibratedmath
  type: dataset
  status: canonical
area: datasets
related:
- '[[2205.14334--teaching-models-uncertainty-in-words]]'
- '[[sciq]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2205.14334--teaching-models-uncertainty-in-words]]'
  target_id: paper:2205.14334
  confidence: high
- type: related_to
  target: '[[sciq]]'
  target_id: dataset:sciq
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
---

CalibratedMath is a benchmark suite of 21 programmatically generated elementary
arithmetic tasks (addition, subtraction, multiplication, division, rounding, and
others) introduced to test calibration under distribution shift. Each task
requires the model to produce both a numerical answer and an explicit confidence
level, and tasks vary substantially in difficulty for [[gpt-3]], enabling
fine-grained analysis of whether verbalized probabilities track actual accuracy
across varying problem types.

**Why it matters here:** CalibratedMath demonstrates that calibration learned
via supervised finetuning can transfer across task difficulty levels within a
domain, providing evidence for the broader claim that verbal uncertainty
expression is a learnable, generalizable skill rather than task-specific
memorization.

**Lineage:** introduced by [[2205.14334--teaching-models-uncertainty-in-words]];
related to [[sciq]] as an in-distribution/out-of-distribution calibration
benchmark pair.
