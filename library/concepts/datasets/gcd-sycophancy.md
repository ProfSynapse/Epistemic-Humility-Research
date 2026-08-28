---
aliases:
- GCD-sycophancy
- GCD sycophancy dataset
- Great Common Divisor sycophancy dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:gcd-sycophancy
  type: dataset
  status: canonical
area: datasets
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
---

GCD-sycophancy is a synthetic arithmetic dataset with query-only, correct-solution, and incorrect-solution formats. Its training mixture creates a spurious association between user-provided solutions and agreement, which lets the paper test whether steering can reduce sycophancy while retaining learned GCD competence.

**Why it matters here:** The dataset separates behavioral correction from task retention after task-specific fine-tuning.

**Lineage:** Fierro and Roger construct it for the fine-tuning-induced sycophancy experiment in arXiv:2511.05408.
