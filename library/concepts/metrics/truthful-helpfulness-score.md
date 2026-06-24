---
aliases:
- THS
- Truthful Helpfulness Score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:truthful-helpfulness-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2410.06913--craft]]'
- '[[honesty-score]]'
- '[[over-abstention]]'
- '[[abstention-rate]]'
- '[[effective-reliability]]'
- '[[over-conservativeness-score]]'
- '[[refusal-aware-instruction-tuning]]'
relationships:
- type: proposed_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[honesty-score]]'
  target_id: metric:honesty-score
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
- type: related_to
  target: '[[abstention-rate]]'
  target_id: metric:abstention-rate
  confidence: medium
- type: related_to
  target: '[[effective-reliability]]'
  target_id: metric:effective-reliability
  confidence: medium
- type: related_to
  target: '[[over-conservativeness-score]]'
  target_id: metric:over-conservativeness-score
  confidence: medium
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: medium
---

A composite metric for refusal-aware evaluation that measures model performance as a geometric quantity in the (P_correct, P_wrong) space, based on the cross-product magnitude of the correctness and wrong-answer probability vectors, designed to simultaneously reward helpfulness (correct answers) and penalize both hallucination (wrong answers) and over-refusal.

**Why it matters here:** The paper demonstrates that all seven incumbent refusal-aware metrics fail to rank at least one pair of model variants correctly; THS is proposed as a unified replacement and is a candidate primary metric for the Phase 1 SFT-vs-DPO-vs-KTO evaluation.

**Lineage:** proposed in 2410.06913 as an alternative to honesty-score and related metrics; related to effective-reliability and over-abstention
