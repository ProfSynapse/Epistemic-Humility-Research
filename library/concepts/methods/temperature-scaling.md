---
aliases:
- temp scaling
- logit temperature
- temperature calibration
- Platt scaling (scalar)
tags:
- kg/method
- concept
- method
kg:
  id: method:temperature-scaling
  type: method
  status: canonical
area: methods
related:
- '[[1706.04599--on-calibration-of-modern-neural-networks]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[overconfidence]]'
- '[[nll-overfitting-degrades-calibration]]'
- '[[high-capacity-training-degrades-calibration]]'
- '[[rlhf-policy-miscalibration-temperature]]'
relationships:
- type: proposed_by
  target: '[[1706.04599--on-calibration-of-modern-neural-networks]]'
  target_id: paper:1706.04599
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[nll-overfitting-degrades-calibration]]'
  target_id: mechanism:nll-overfitting-degrades-calibration
  confidence: medium
- type: related_to
  target: '[[high-capacity-training-degrades-calibration]]'
  target_id: mechanism:high-capacity-training-degrades-calibration
  confidence: medium
- type: related_to
  target: '[[rlhf-policy-miscalibration-temperature]]'
  target_id: mechanism:rlhf-policy-miscalibration-temperature
  confidence: medium
---

A single-parameter post-hoc calibration method that divides a classifier's logit vector by a learned scalar T before the softmax, optimizing T on a held-out validation set by minimizing NLL. T > 1 softens the distribution (reduces overconfidence); T = 1 recovers the original probabilities. Class predictions are unchanged because T does not affect the argmax.

**Why it matters here:** Temperature scaling is the dominant post-hoc calibration baseline in the literature and the cheapest recovery step after training-induced miscalibration. Any locked training-regimen arm that worsens ECE should be compared against what a simple temperature rescale achieves, to separate training-time versus inference-time fixes.

**Lineage:** Introduced as 'temperature scaling' by Guo et al. (arXiv:1706.04599) as the simplest extension of Platt scaling to multi-class problems; related to knowledge distillation temperature (Hinton et al. 2015) and statistical-mechanics softmax. Recovered by [[verbalized-prob-generalizes-logit-overfits-distribution-shift]] as the logit-calibration approach that fails under distribution shift.
