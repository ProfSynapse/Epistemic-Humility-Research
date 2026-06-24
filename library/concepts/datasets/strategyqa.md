---
aliases:
- StrategyQA
- Strategy QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:strategyqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.18183--reasoning-models-dont-know]]'
- '[[gpqa]]'
- '[[simpleqa]]'
- '[[mmlu]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2506.18183--reasoning-models-dont-know]]'
  target_id: paper:2506.18183
  confidence: high
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: medium
- type: related_to
  target: '[[simpleqa]]'
  target_id: dataset:simpleqa
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A yes/no QA benchmark requiring implicit multi-hop reasoning strategies that are not explicitly stated in the question. Questions are designed so that answering requires decomposing the question into implicit sub-questions and combining information across them.

**Why it matters here:** Used in calibration studies (arXiv:2506.18183) as a benchmark where reasoning models are overconfident but accuracy is moderate, making it distinct from high-accuracy saturated benchmarks. IUQ-High slightly worsens calibration on StrategyQA, showing that excessive conservatism in introspection can backfire on reasoning tasks.

**Lineage:** Introduced by Geva et al. (2021). Used in arXiv:2506.18183 alongside GPQA and SimpleQA.
