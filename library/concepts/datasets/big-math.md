---
aliases:
- Big Math
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:big-math
  type: dataset
  status: canonical
area: datasets
related:
- '[[2507.16806--rlcr-beyond-binary-rewards]]'
- '[[rlcr]]'
- '[[gsm8k]]'
- '[[math-benchmark]]'
- '[[gpqa]]'
- '[[brier-score]]'
relationships:
- type: proposed_by
  target: '[[2507.16806--rlcr-beyond-binary-rewards]]'
  target_id: paper:2507.16806
  confidence: high
- type: related_to
  target: '[[rlcr]]'
  target_id: method:rlcr
  confidence: medium
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: medium
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
  confidence: medium
---

A large-scale, high-quality math dataset for reinforcement learning in language models (Albalak et al., 2025). RLCR uses a 15,000-problem subset selected by quality criteria for RL training; correctness is computed using math-verify.

**Why it matters here:** Provides a diverse math RL training set covering multi-step and scientific reasoning where uncertainty accumulates across steps, enabling evaluation of calibration under complex reasoning demands.

**Lineage:** Albalak et al. 2025; used alongside Math-500, GSM8K, and GPQA for in-domain and OOD evaluation in the RLCR math experiments.
