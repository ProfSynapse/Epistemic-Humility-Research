---
aliases:
- ConfidNet
- True Class Probability confidence network
tags:
- kg/method
- concept
- method
kg:
  id: method:confidnet
  type: method
  status: canonical
area: methods
related:
- '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
- '[[true-class-probability]]'
- '[[max-confidence-scoring]]'
- '[[learned-confidence-branch]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
  target_id: paper:1910.04851
  confidence: high
- type: related_to
  target: '[[true-class-probability]]'
  target_id: term:true-class-probability
  confidence: high
- type: related_to
  target: '[[max-confidence-scoring]]'
  target_id: method:max-confidence-scoring
  confidence: high
- type: related_to
  target: '[[learned-confidence-branch]]'
  target_id: method:learned-confidence-branch
  confidence: medium
---

ConfidNet is an auxiliary confidence head that learns to regress a classifier's
true-class probability (TCP) via an L2/MSE objective, attached on top of a frozen
encoder and then fine-tuned. Because TCP separates correct from incorrect
predictions far better than the max softmax probability, a head trained to
predict it yields a confidence score whose ranking is well-suited to failure
prediction (deciding which predictions to trust).

**Why it matters here:** ConfidNet is the closest method-level ancestor of the
experiment's confidence-readout head: an auxiliary scalar head, trained with a
proper-scoring-style regression target, that reads an existing network's internal
representation to produce a calibrated trust signal. It directly motivates
"train a head to predict a correctness/answerability target" over thresholding
the model's own softmax.

**Lineage:** Corbiere et al. 2019; improves on the max-softmax-response baseline
([[max-confidence-scoring]]) and is conceptually adjacent to the
[[learned-confidence-branch]] of DeVries and Taylor.
