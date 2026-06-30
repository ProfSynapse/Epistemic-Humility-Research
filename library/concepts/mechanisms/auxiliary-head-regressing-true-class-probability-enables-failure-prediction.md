---
aliases:
- An auxiliary head regressing the true-class probability enables failure prediction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:auxiliary-head-regressing-true-class-probability-enables-failure-prediction
  type: mechanism
  status: canonical
cause: "Training an auxiliary head to regress the classifier's true-class probability (TCP) on top of a frozen-then-finetuned encoder."
effect: "The learned scalar ranks correct above incorrect predictions far better than max-softmax, improving failure-prediction AUPR / AUROC and selective-classification."
polarity: enables
related:
- '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
- '[[confidnet]]'
- '[[true-class-probability]]'
- '[[max-confidence-scoring]]'
relationships:
- type: supported_by
  target: '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
  target_id: paper:1910.04851
  confidence: high
- type: related_to
  target: '[[confidnet]]'
  target_id: method:confidnet
  confidence: high
- type: related_to
  target: '[[true-class-probability]]'
  target_id: term:true-class-probability
  confidence: high
---

Corbiere et al. 2019 show that because TCP cleanly separates correct from
incorrect predictions (unlike max-softmax, which is high even on errors), an
auxiliary head trained to regress TCP gives a confidence score whose ranking
improves failure prediction and selective classification over the max-class-
probability baseline.
