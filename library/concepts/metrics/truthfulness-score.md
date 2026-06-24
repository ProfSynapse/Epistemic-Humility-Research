---
aliases:
- truthfulness score
- T score
- T metric
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:truthfulness-score
  type: metric
  status: canonical
area: metrics
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[hallucination]]'
- '[[abstention]]'
- '[[honesty-score]]'
- '[[truthrl]]'
- '[[crag]]'
relationships:
- type: proposed_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[honesty-score]]'
  target_id: metric:honesty-score
  confidence: medium
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: medium
- type: related_to
  target: '[[crag]]'
  target_id: dataset:crag
  confidence: medium
---

A composite scalar T = w1*accuracy + w2*uncertainty_rate - w3*hallucination_rate, with weights w1, w2, w3 >= 0. Following Yang et al. 2024a (CRAG), TruthRL sets w1=1, w2=0, w3=1, so T = accuracy - hallucination_rate. T can be negative when hallucination rate exceeds accuracy. It differs from the honesty-score in that abstention (uncertainty) enters with zero weight; only correct answers and hallucinations determine T.

**Why it matters here:** The primary optimization target and evaluation metric in TruthRL; operationalizes truthfulness as a balance between factual correctness and hallucination avoidance without treating abstention as directly beneficial to the score.

**Lineage:** Defined in TruthRL Section 2.1, following Yang et al. 2024a (CRAG paper); distinct from honesty-score (which weights abstention positively) and from pure accuracy metrics.
