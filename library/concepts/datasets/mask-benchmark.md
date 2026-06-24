---
aliases:
- MASK
- Model Alignment between Statements and Knowledge
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mask-benchmark
  type: dataset
  status: canonical
area: datasets
related:
- '[[2503.03750--mask-benchmark-honesty]]'
- '[[honesty-bench]]'
- '[[truthfulqa]]'
- '[[representation-engineering]]'
- '[[p-lie]]'
- '[[sycophancy]]'
- '[[spurious-dishonesty]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2503.03750--mask-benchmark-honesty]]'
  target_id: paper:2503.03750
  confidence: high
- type: related_to
  target: '[[honesty-bench]]'
  target_id: dataset:honesty-bench
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[representation-engineering]]'
  target_id: method:representation-engineering
  confidence: medium
- type: related_to
  target: '[[p-lie]]'
  target_id: metric:p-lie
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[spurious-dishonesty]]'
  target_id: term:spurious-dishonesty
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
---

A large-scale human-curated benchmark of 1,500 adversarially-selected examples designed to directly measure lies of commission in LLMs by independently eliciting model beliefs via neutral prompts and model statements via pressure prompts, then comparing them programmatically via an LLM judge. Covers six pressure archetypes representing realistic scenarios where honesty may conflict with other objectives.

**Why it matters here:** Provides the first standardized, large-scale operationalization of lying (statement contradicts belief) that is orthogonal to factual accuracy, allowing researchers to detect models that know the truth but state a falsehood under pressure. Establishes P(Lie) as a concrete evaluation target separable from calibration or abstention.

**Lineage:** Proposed by Ren, Agarwal, Mazeika et al. (Center for AI Safety / Scale AI), 2025. Builds on definitions of lying in Mahon (2008) and on representation-engineering literature in Zou et al. (2023).
