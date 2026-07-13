---
aliases:
- A-Acc
- Abstain Accuracy (A-Acc)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:abstain-accuracy
  type: metric
  status: canonical
area: metrics
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
relationships:
- type: proposed_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
---

Abstain Accuracy (A-Acc) is an AbstainQA metric computed as the number of
correct answers plus correct abstentions divided by the total number of
questions. It evaluates whether the model's decision to answer or abstain is
itself correct, independent of raw QA performance.

**Why it matters here:** A-Acc separates the quality of the abstain/answer
decision from accuracy on attempted items, which is essential for the locked training-regimen
study comparing how SFT, DPO, and KTO affect the calibration of abstention
decisions rather than just downstream answer rates.

**Lineage:** pairs with [[reliable-accuracy]] to give a two-dimensional view of
abstention quality: A-Acc covers the decision layer while R-Acc covers the
response layer.
