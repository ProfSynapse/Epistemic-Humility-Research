---
aliases:
- Jointly training a selection head lowers selective risk at fixed coverage
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:joint-selection-head-training-lowers-selective-risk
  type: mechanism
  status: canonical
cause: "Training a selection (reject-option) head jointly with the predictor under a selective loss with an explicit target-coverage constraint, rather than thresholding a post-hoc confidence score."
effect: "Lower selective risk (error on the answered subset) at any fixed coverage, dominating softmax-response and MC-dropout reject baselines."
polarity: decreases
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selectivenet]]'
- '[[selective-risk]]'
- '[[selective-prediction]]'
relationships:
- type: supported_by
  target: '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
  target_id: paper:1901.09192
  confidence: high
- type: related_to
  target: '[[selectivenet]]'
  target_id: method:selectivenet
  confidence: high
- type: related_to
  target: '[[selective-risk]]'
  target_id: metric:selective-risk
  confidence: high
---

Geifman and El-Yaniv 2019 show that optimizing the selection head end-to-end with
the predictor under a coverage-constrained selective loss yields lower risk at
each target coverage than thresholding a separately-obtained confidence score,
because the model can shape its representation around the coverage it must hit.
