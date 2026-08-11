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
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[mmlu]]'
- '[[perplexity]]'
relationships:
- type: evaluation_set_for
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: used_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: low
- type: related_to
  target: '[[perplexity]]'
  target_id: metric:perplexity
  confidence: medium
---

BoolQ is a reading-comprehension benchmark of naturally occurring yes-or-no questions paired with short supporting passages. Models must resolve the answer from the supplied context rather than answer from a fixed multiple-choice inventory.

**Why it matters here:** BoolQ is used to track capability under layer pruning and as a downstream check for circuit-guided pruning, quantization, and selective fine-tuning. It helps distinguish interventions that preserve useful reasoning from those that merely perform well on an intrinsic circuit metric.

**Lineage:** Clark et al. 2019; used in arXiv:2403.17887 and [[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]].
