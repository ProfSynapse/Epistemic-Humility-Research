---
aliases:
- ETHICS commonsense morality
- ETHICS morality subset
- ETHICS
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:ethics-commonsense-morality
  type: dataset
  status: canonical
area: datasets
related:
- '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
- '[[sycophancy-eval]]'
- '[[true-false-dataset]]'
relationships:
- type: used_by
  target: '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
  target_id: paper:2505.13763
  confidence: high
- type: related_to
  target: '[[sycophancy-eval]]'
  target_id: dataset:sycophancy-eval
  confidence: medium
- type: related_to
  target: '[[true-false-dataset]]'
  target_id: dataset:true-false-dataset
  confidence: medium
---

The ETHICS commonsense morality subset contains first-person scenarios labeled
as morally acceptable or unacceptable. Ji-An et al. use 1,200 balanced
sentences, split equally between direction fitting and neurofeedback tests.

**Why it matters here:** It supplies the main semantic contrast used to fit a
linear activation direction and test whether models can report or control that
direction.
