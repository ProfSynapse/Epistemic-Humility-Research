---
aliases:
- BeHonest benchmark
- Be Honest dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:behonest
  type: dataset
  status: canonical
area: datasets
related:
- '[[2409.18786--survey-honesty-of-llms]]'
- '[[selfaware]]'
- '[[unknownbench]]'
- '[[self-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2409.18786--survey-honesty-of-llms]]'
  target_id: paper:2409.18786
  confidence: high
- type: related_to
  target: '[[selfaware]]'
  target_id: dataset:selfaware
  confidence: medium
- type: related_to
  target: '[[unknownbench]]'
  target_id: dataset:unknownbench
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
---

BeHonest is a 12,227-question benchmark for LLM honesty evaluation with 63% unknown questions, aggregating questions from SelfAware and UnknownBench. It combines existing resources into a single comprehensive evaluation suite for both self-knowledge and self-expression.

**Why it matters here:** BeHonest provides the largest combined known-unknown benchmark by question count among the model-agnostic benchmarks surveyed, and its hybrid sourcing allows direct comparison of a model's performance across the distinct unknown-question construction methods of its component datasets.

**Lineage:** Proposed by Chern et al. 2024; surveyed in Li et al. 2024 (2409.18786) Table 1.
