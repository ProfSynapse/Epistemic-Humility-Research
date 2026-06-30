---
aliases:
- Max-class-probability overconfidence degrades failure ranking
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:max-class-probability-overconfidence-degrades-failure-ranking
  type: mechanism
  status: canonical
cause: "Using the maximum softmax class probability as the confidence score for deciding which predictions to trust."
effect: "Confident errors receive high scores too, compressing the gap between correct and wrong predictions and degrading failure-prediction ranking."
polarity: decreases
related:
- '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
- '[[max-confidence-scoring]]'
- '[[true-class-probability]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[1910.04851--addressing-failure-prediction-learning-model-confidence]]'
  target_id: paper:1910.04851
  confidence: high
- type: related_to
  target: '[[max-confidence-scoring]]'
  target_id: method:max-confidence-scoring
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

The max softmax probability is large even on misclassified inputs, so it assigns
high confidence to confident errors; Corbiere et al. 2019 use this to motivate
regressing TCP instead, since the overconfidence of the max-class probability is
exactly what makes it a poor failure-prediction signal.
