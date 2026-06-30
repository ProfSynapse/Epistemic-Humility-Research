---
aliases:
- Misclassified in-distribution examples are a training proxy for OOD calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:misclassified-examples-proxy-for-ood-calibration
  type: mechanism
  status: canonical
cause: "Treating the model's own hard / misclassified in-distribution examples as the supervision signal that drives down the learned confidence scalar."
effect: "The confidence estimator generalizes to assign low confidence on genuinely out-of-distribution inputs, so no separate OOD data is needed at training time."
polarity: enables
related:
- '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
- '[[learned-confidence-branch]]'
- '[[out-of-distribution-detection]]'
relationships:
- type: supported_by
  target: '[[1802.04865--learning-confidence-out-distribution-detection-neural-networks]]'
  target_id: paper:1802.04865
  confidence: high
- type: related_to
  target: '[[learned-confidence-branch]]'
  target_id: method:learned-confidence-branch
  confidence: high
- type: related_to
  target: '[[out-of-distribution-detection]]'
  target_id: term:out-of-distribution-detection
  confidence: medium
---

Because the confidence branch is pushed low precisely on the in-distribution
inputs the model finds hardest (those it would misclassify), the learned signal
becomes a usable detector for inputs outside the training distribution as well -
hard in-distribution examples act as a free proxy for the unseen OOD regime
(DeVries and Taylor 2018).
