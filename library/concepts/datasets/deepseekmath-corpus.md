---
aliases:
- DeepSeekMath pre-training data
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:deepseekmath-corpus
  type: dataset
  status: canonical
area: datasets
related:
- '[[2402.03300--deepseekmath-grpo]]'
- '[[math-benchmark]]'
- '[[gsm8k]]'
relationships:
- type: proposed_by
  target: '[[2402.03300--deepseekmath-grpo]]'
  target_id: paper:2402.03300
  confidence: high
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
---

The DeepSeekMath pre-training corpus is a 120-billion-token math-focused dataset
extracted from Common Crawl using an iterative fastText-based classifier
pipeline. It is roughly 7x larger than Minerva's math web data and 9x larger
than OpenWebMath, covering a wide range of mathematical content in multiple
languages alongside curated sources such as arXiv and textbooks.

**Why it matters here:** The corpus contextualizes why domain-specialized
pre-training can shift a model's knowledge boundary, a phenomenon directly
relevant to the epistemic-humility study's interest in what LLMs know versus
what they abstain from.

**Lineage:** introduced alongside [[group-relative-policy-optimization]] in the
DeepSeekMath paper; used to evaluate on [[math-benchmark]] and [[gsm8k]].
