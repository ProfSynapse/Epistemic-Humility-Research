---
aliases:
- scale-invariant tail accuracy
- scaling does not help tail knowledge
- parametric scaling limited to popular entities
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:scaling-fails-on-long-tail-knowledge
  type: mechanism
  status: canonical
cause: "Increasing LM parameter count"
effect: "Negligible accuracy gain on low-popularity factual questions; GPT-Neo 6B to GPT-3 davinci-003 accuracy on 4,000 least-popular PopQA questions spans only 15-19%"
polarity: mediates
related:
- '[[2212.10511--popqa-when-not-to-trust]]'
- '[[entity-popularity-predicts-parametric-memorization]]'
- '[[knowledge-boundary]]'
- '[[dominant-uncertainty-source-shifts-with-model-scale]]'
- '[[popqa]]'
relationships:
- type: supported_by
  target: '[[2212.10511--popqa-when-not-to-trust]]'
  target_id: paper:2212.10511
  confidence: high
- type: related_to
  target: '[[entity-popularity-predicts-parametric-memorization]]'
  target_id: mechanism:entity-popularity-predicts-parametric-memorization
  confidence: high
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: high
- type: related_to
  target: '[[dominant-uncertainty-source-shifts-with-model-scale]]'
  target_id: mechanism:dominant-uncertainty-source-shifts-with-model-scale
  confidence: high
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: high
---

Scaling up model parameters improves factual QA accuracy predominantly on high-popularity questions (above log-popularity threshold of 4). On the lowest-popularity tail of PopQA, accuracy is nearly flat (15-19%) across a 10x parameter range. This decouples scale-driven knowledge gain from tail-knowledge coverage, suggesting that the long tail requires non-parametric memory rather than larger parameters.
