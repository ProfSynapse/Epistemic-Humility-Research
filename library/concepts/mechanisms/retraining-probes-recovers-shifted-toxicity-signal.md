---
aliases:
- Retraining probes recovers the shifted toxicity signal
- A hidden-state probe remains useful after model training
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:retraining-probes-recovers-shifted-toxicity-signal
  type: mechanism
  status: canonical
cause: "New [[linear-probe]] classifiers are fit on activations collected after probe-based fine-tuning."
effect: "High toxicity-detection AUC is recovered despite reduced accuracy of probes fit before training."
polarity: enables
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[linear-probe]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

Retrained-probe AUC remained between 0.957 and 0.973 across the SFT
conditions. In the DPO conditions it was 0.926 for one-probe training and
0.992 for ten-probe training.
