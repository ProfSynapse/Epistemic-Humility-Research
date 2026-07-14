---
aliases:
- Spearman rank correlation
- Spearman's rho
- rank correlation
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:spearman-rank-correlation
  type: metric
  status: canonical
area: metrics
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[wasserstein-distance]]'
relationships:
- type: measured_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[wasserstein-distance]]'
  target_id: metric:wasserstein-distance
  confidence: medium
---

Spearman rank correlation measures monotonic agreement between two rankings. In judge-bias steering, it constrains an intervention to preserve the baseline ordering of answers while changing the score distribution.

**Why it matters here:** A rank-preservation floor helps distinguish targeted score movement from indiscriminate corruption of the judge's outputs.

**Lineage:** Used as a feasibility constraint alongside [[wasserstein-distance]] in the steering-strength search.
