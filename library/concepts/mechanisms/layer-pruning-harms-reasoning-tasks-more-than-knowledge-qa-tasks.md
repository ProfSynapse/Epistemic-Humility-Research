---
aliases:
- Pruning Harms Reasoning More Than Knowledge QA
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:layer-pruning-harms-reasoning-tasks-more-than-knowledge-qa-tasks
  type: mechanism
  status: canonical
cause: Fraction of layers removed by similarity-informed layer pruning, after QLoRA healing, compared across task type
effect: Multi-step reasoning benchmarks such as GSM8K degrade earlier and more severely than knowledge-recall QA benchmarks such as MMLU and BoolQ, and than commonsense-completion benchmarks such as HellaSwag, at matched pruning fractions
polarity: enables
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[layer-pruning]]'
- '[[gsm8k]]'
- '[[mmlu]]'
- '[[hellaswag]]'
relationships:
- type: supported_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: related_to
  target: '[[layer-pruning]]'
  target_id: method:layer-pruning
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[hellaswag]]'
  target_id: dataset:hellaswag
  confidence: medium
---

At matched pruning fractions, benchmarks requiring multi-step reasoning
(GSM8K) lose accuracy earlier and more sharply than benchmarks that mostly
probe stored factual/commonsense knowledge (MMLU, BoolQ, HellaSwag). This
asymmetry indicates that whatever computation the pruned deep layers were
performing is disproportionately load-bearing for chained reasoning steps
relative to single-step knowledge retrieval, even though both task types
sit on the same smoothly-degrading loss curve.

**Why it matters here:** Complements the loss/accuracy decoupling finding by
showing the decoupling is not uniform across task types: it sharpens the
paper's interpretation that shallow layers (or the union of layers that
survive pruning) preferentially retain simple knowledge-recall computation
while reasoning is the first capability lost.

**Lineage:** established in arXiv:2403.17887 (Section 4, robustness checks
following Figures 2-3) across the same seven-model sweep.
