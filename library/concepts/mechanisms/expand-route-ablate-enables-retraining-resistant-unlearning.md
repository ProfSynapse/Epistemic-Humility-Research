---
aliases:
- Expand Route Ablate enables retraining-resistant unlearning
- ERA localizes removable capabilities
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:expand-route-ablate-enables-retraining-resistant-unlearning
  type: mechanism
  status: canonical
cause: "Selected training gradients are routed into added neurons, which are deleted after training and followed by a short retain-data repair phase."
effect: "Forget-set performance remains degraded after limited retraining, especially when forget labels are incomplete."
polarity: enables
related:
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
- '[[expand-route-ablate]]'
- '[[wmdp-bio]]'
relationships:
- type: supported_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: related_to
  target: '[[expand-route-ablate]]'
  target_id: method:expand-route-ablate
  confidence: high
- type: related_to
  target: '[[wmdp-bio]]'
  target_id: dataset:wmdp-bio
  confidence: high
---

The paper reports ERA advantages over filtering and post-hoc baselines under incomplete TinyStories labels, plus a 0.7-billion-parameter virology experiment. The method also degrades retain performance, and its tradeoff depends on routing hyperparameters.
