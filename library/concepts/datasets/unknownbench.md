---
aliases:
- Unknown Bench
- UnknownBench dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:unknownbench
  type: dataset
  status: canonical
area: datasets
related:
- '[[2409.18786--survey-honesty-of-llms]]'
- '[[selfaware]]'
- '[[known-unknown-questions]]'
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
  target: '[[known-unknown-questions]]'
  target_id: dataset:known-unknown-questions
  confidence: medium
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
---

UnknownBench is a 13,319-question benchmark for evaluating known-unknown recognition in LLMs, with 50% unknown questions. Known questions are drawn from FalseQA (true-premise questions), NaturalQuestions, and template-generated data; unknown questions are constructed by inducing non-existent concepts into those same sources.

**Why it matters here:** UnknownBench is one of the largest model-agnostic known-unknown benchmarks and is used as a source for BeHonest. Its non-existent-concept construction method provides a systematic way to generate unknown questions without requiring expert annotation.

**Lineage:** Proposed by Liu et al. 2024a; surveyed in Li et al. 2024 (2409.18786) Table 1.
