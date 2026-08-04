---
aliases:
- BoolQ
- Boolean Questions
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:boolq
  type: dataset
  status: canonical
area: datasets
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[mmlu]]'
relationships:
- type: evaluation_set_for
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: low
---

BoolQ (Clark et al. 2019) is a reading-comprehension benchmark of naturally
occurring yes/no questions paired with a short supporting passage; the model
must answer True or False given the passage as context.

**Why it matters here:** One of the two primary QA benchmarks (alongside
[[mmlu]]) used to track accuracy as a function of pruning fraction; the
sharp accuracy collapse to random (50%) guessing on BoolQ, occurring at
roughly the same pruning fraction as the MMLU collapse, is central evidence
for the loss/accuracy phase-transition finding.

**Lineage:** Clark et al. 2019; used as an evaluation benchmark in
arXiv:2403.17887.
