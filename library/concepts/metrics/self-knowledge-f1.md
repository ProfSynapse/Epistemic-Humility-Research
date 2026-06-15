---
aliases:
- self-knowledge score
- F1 score on unanswerable detection
- Self-Knowledge F1
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:self-knowledge-f1
  type: metric
  status: canonical
area: metrics
related:
- '[[2305.18153--selfaware-know-what-they-dont-know]]'
relationships:
- type: proposed_by
  target: '[[2305.18153--selfaware-know-what-they-dont-know]]'
  target_id: paper:2305.18153
  confidence: high
---

Self-Knowledge F1 is an F1 score computed by treating unanswerable questions as the positive class, measuring how well a model's response expresses uncertainty relative to a set of reference uncertain-meaning sentences drawn from a similarity-based classifier. Precision captures whether uncertainty expressions are appropriate, recall captures whether the model catches all truly unanswerable inputs, and the harmonic mean balances both. The metric was introduced alongside the SelfAware benchmark and is the primary quantitative handle for self-knowledge evaluation on that dataset.

**Why it matters here:** Because the SFT-vs-DPO-vs-KTO abstention study needs a well-defined signal for whether a model knows what it does not know, Self-Knowledge F1 provides a standard reference point for comparing abstention quality against prior self-knowledge literature.

**Lineage:** proposed by [[2305.18153--selfaware-know-what-they-dont-know]] as the evaluation protocol for [[selfaware]].
