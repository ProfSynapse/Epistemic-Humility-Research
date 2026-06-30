---
aliases:
- Selective Risk
- risk-coverage curve
- risk at coverage
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:selective-risk
  type: metric
  status: canonical
area: metrics
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selective-prediction]]'
- '[[selectivenet]]'
- '[[selective-classification-auc]]'
relationships:
- type: proposed_by
  target: '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
  target_id: paper:1901.09192
  confidence: medium
- type: related_to
  target: '[[selective-prediction]]'
  target_id: term:selective-prediction
  confidence: high
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
  confidence: high
---

Selective risk is the average loss computed over only the covered (non-rejected)
inputs of a selective predictor, reported as a function of coverage (the fraction
of inputs answered). Plotting selective risk against coverage gives the
risk-coverage curve; a better abstention policy achieves lower risk at any fixed
coverage.

**Why it matters here:** It is the natural scoring surface for an
answer/abstain policy: it quantifies how much error a model avoids by deferring,
and whether the confidence head's gate orders inputs so that the answered subset
is reliably more correct.

**Lineage:** El-Yaniv and Wiener 2010; optimized directly by [[selectivenet]] and
summarized in aggregate by the [[selective-classification-auc]] (area under the
risk-coverage curve).
