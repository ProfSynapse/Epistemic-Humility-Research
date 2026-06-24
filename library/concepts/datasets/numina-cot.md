---
aliases:
- Numina CoT dataset
- long-CoT math training set
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:numina-cot
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.06475--stepwise-trace-scoring]]'
- '[[aime]]'
- '[[rredcot]]'
- '[[math-benchmark]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[2606.06475--stepwise-trace-scoring]]'
  target_id: paper:2606.06475
  confidence: high
- type: related_to
  target: '[[aime]]'
  target_id: dataset:aime
  confidence: medium
- type: related_to
  target: '[[rredcot]]'
  target_id: method:rredcot
  confidence: medium
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: medium
---

A math reasoning training dataset consisting of problems paired with long chain-of-thought solutions (up to 25k tokens), used in this paper as the training distribution for Qwen3-4B RREDCoT experiments.

**Why it matters here:** Provides the long-generation training regime needed to evaluate reward redistribution methods at realistic CoT lengths where variance in terminal-only reward becomes acute.

**Lineage:** Part of the NuminaMath / Numina open math dataset family used in reasoning-model RL fine-tuning.
