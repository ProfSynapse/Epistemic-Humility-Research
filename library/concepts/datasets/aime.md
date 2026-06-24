---
aliases:
- AIME24
- AIME25
- AIME26
- American Invitational Mathematics Examination benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:aime
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[math-benchmark]]'
- '[[group-relative-policy-optimization]]'
- '[[rredcot]]'
relationships:
- type: proposed_by
  target: '[[2606.06475--stepwise-trace-scoring]]'
  target_id: paper:2606.06475
  confidence: high
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
- type: related_to
  target: '[[rredcot]]'
  target_id: method:rredcot
  confidence: medium
---

A set of 30 competition-mathematics problems drawn from the annual AIME exam, used as a reasoning benchmark for LLMs; yearly variants (AIME24, AIME25, AIME26) serve as held-out test sets for math RL fine-tuning evaluation.

**Why it matters here:** Widely used hard-reasoning evaluation for long-context CoT models; problems require multi-step integer arithmetic and are difficult to solve by memorization alone, making them a demanding test of genuine reasoning improvement.

**Lineage:** Based on the official AMC/AIME competition series; adopted as an LLM benchmark in the DeepSeek and Qwen reasoning model literature.
