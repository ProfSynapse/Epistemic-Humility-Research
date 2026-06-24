---
aliases:
- linguistic confidence coarseness bottleneck
- confidence granularity bottleneck
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:coarse-linguistic-confidence-degrades-selective-classification
  type: mechanism
  status: canonical
cause: "Closed-source LLMs emitting linguistically verbalized confidence scores that cluster at a small number of discrete values (e.g., GPT-4 outputs 0.9 for 50% of examples, only 8 unique values across 12 datasets)"
effect: "Severe ceiling on selective-classification AUC and AUROC because tied confidence scores prevent the model from discriminating between correct and incorrect answers within the dominant confidence bin, leaving tie-breaking to random noise"
polarity: decreases
related:
- '[[2311.08877--llamas-know-what-gpts-dont-show]]'
- '[[verbalized-confidence]]'
- '[[surrogate-confidence-estimation]]'
- '[[selective-classification-auc]]'
- '[[auroc]]'
- '[[question-difficulty-transfer]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[2311.08877--llamas-know-what-gpts-dont-show]]'
  target_id: paper:2311.08877
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[surrogate-confidence-estimation]]'
  target_id: method:surrogate-confidence-estimation
  confidence: high
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
- type: related_to
  target: '[[question-difficulty-transfer]]'
  target_id: term:question-difficulty-transfer
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
---

When a model's verbalized confidence distribution is highly concentrated, many correct and incorrect answers share an identical score. The AUC computation must break these ties randomly, effectively degrading the signal for the largest slice of the data. Even a tiny injection of a surrogate's continuous probability (alpha = 0.001) resolves the ties and recovers most of the information loss, showing that the bottleneck is granularity rather than mean accuracy of the linguistic signal.
