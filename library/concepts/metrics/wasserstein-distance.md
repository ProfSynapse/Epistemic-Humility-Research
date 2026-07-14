---
aliases:
- Wasserstein distance
- Wasserstein-1 distance
- W1 distance
- earth mover's distance
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:wasserstein-distance
  type: metric
  status: canonical
area: metrics
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[activation-steering]]'
relationships:
- type: measured_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: medium
---

Wasserstein distance measures the minimum transport cost needed to transform one probability distribution into another. The first-order form, W1, gives a distribution-level measure of how far judge scores move under a text or activation intervention.

**Why it matters here:** Xu et al. use W1 both to optimize steering strength under validity and rank-preservation constraints and to compare fitted bias directions with random and wrong-type controls.

**Lineage:** A standard optimal-transport metric applied here to score distributions produced by [[activation-steering]].
