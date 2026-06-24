---
aliases:
- ARC-Challenge
- ARC Challenge
- AI2 Reasoning Challenge
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:arc-challenge
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.18183--reasoning-models-dont-know]]'
- '[[mmlu]]'
- '[[gpqa]]'
- '[[strategyqa]]'
- '[[calibration]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2506.18183--reasoning-models-dont-know]]'
  target_id: paper:2506.18183
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: medium
- type: related_to
  target: '[[strategyqa]]'
  target_id: dataset:strategyqa
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

The challenging subset of the AI2 Reasoning Challenge dataset, consisting of grade-school science multiple-choice questions that require more than simple retrieval to answer correctly. Introduced by Clark et al. (2018).

**Why it matters here:** Serves as a benchmark where reasoning models achieve near-perfect accuracy and consequently appear well-calibrated, illustrating how benchmark saturation can mask underlying overconfidence tendencies. Used in arXiv:2506.18183 to contrast against harder unsaturated benchmarks.

**Lineage:** Introduced by Clark et al. (2018), arXiv:1803.05457. Used in arXiv:2506.18183 as a saturated benchmark contrast case.
