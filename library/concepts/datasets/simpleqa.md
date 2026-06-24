---
aliases:
- SimpleQA benchmark
- simple QA
- short-form factuality benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:simpleqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2502.11028--mind-the-confidence-gap]]'
- '[[truthfulqa]]'
- '[[triviaqa]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2502.11028--mind-the-confidence-gap]]'
  target_id: paper:2502.11028
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
---

A factual question-answering benchmark of 4,326 short, fact-seeking queries with clearly defined correct answers, verified by multiple independent AI trainers. Designed to measure short-form factual accuracy and calibration of LLMs, with high-quality annotations intended to minimize ambiguity.

**Why it matters here:** Provides a reproducible benchmark for measuring the gap between model confidence and factual accuracy across question types (Date, Number, Person, Place), enabling calibration comparisons across models and prompting regimes. Used in this paper to measure ECE and accuracy in both free-generation and distractor-augmented settings.

**Lineage:** Introduced by Wei et al. (2024), arXiv 2411.04368. Used by Chhikara (2025, arXiv 2502.11028) for calibration benchmarking across six LLMs.
