---
aliases:
- UAcc
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:uncertainty-aware-accuracy
  type: metric
  status: canonical
area: metrics
related:
- '[[2401.12794--llm-uncertainty-bench-conformal]]'
- '[[conformal-prediction-for-llm-uncertainty]]'
- '[[calibration]]'
- '[[abstention-rate]]'
- '[[reliable-accuracy]]'
relationships:
- type: proposed_by
  target: '[[2401.12794--llm-uncertainty-bench-conformal]]'
  target_id: paper:2401.12794
  confidence: high
- type: related_to
  target: '[[conformal-prediction-for-llm-uncertainty]]'
  target_id: method:conformal-prediction-for-llm-uncertainty
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[reliable-accuracy]]'
  target_id: metric:reliable-accuracy
  confidence: medium
---

A composite metric defined as UAcc = (Acc / SS) * sqrt(|C|), where Acc is prediction accuracy, SS is the average conformal prediction set size, and |C| is the number of answer choices. UAcc rewards models with low uncertainty and penalizes those with high uncertainty, and can take values larger or smaller than Acc depending on SS relative to sqrt(|C|).

**Why it matters here:** Makes the accuracy-uncertainty tradeoff explicit in a single scalar: it can amplify or shrink relative accuracy differences between models and can reverse rank orderings when one model is more accurate but substantially more uncertain. Relevant to the locked training-regimen study as a candidate composite metric for evaluating abstention-training arms.

**Lineage:** Proposed in Ye et al. (2024), 2401.12794.
