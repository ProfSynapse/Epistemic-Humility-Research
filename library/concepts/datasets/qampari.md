---
aliases:
- QAMPARI
- Qampari
- QAMPARI benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:qampari
  type: dataset
  status: canonical
area: datasets
related:
- '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
- '[[verbalized-confidence]]'
- '[[calibration]]'
relationships:
- type: related_to
  target: '[[2503.02623--rewarding-doubt-reinforcement-learning-approach-calibrated-confidence]]'
  target_id: paper:2503.02623
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
---

QAMPARI is an open-domain question-answering benchmark where a query can have multiple correct answer items. In confidence-calibration work, it stresses whether a model can express uncertainty over multiple factual claims rather than only over a single final answer.

**Why it matters here:** Rewarding Doubt uses QAMPARI to test whether direct confidence RL transfers from single-answer factual QA to multi-answer factual generation.
