---
aliases:
- An auxiliary prediction head prevents overfitting to the covered subset
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:auxiliary-head-prevents-covered-subset-overfit
  type: mechanism
  status: canonical
cause: "Adding an auxiliary prediction head that is trained on the full (unfiltered) data distribution alongside the coverage-constrained selective objective."
effect: "The shared representation stays generally predictive and does not overfit to the easy covered subset, stabilizing selective performance."
polarity: prevents
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selectivenet]]'
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
---

The selective objective alone would let the body specialize to the covered subset
and lose general signal; SelectiveNet's auxiliary head h, trained on all examples,
regularizes the shared representation so it remains broadly predictive, which the
ablation shows is necessary for the selective head to work well (Geifman and
El-Yaniv 2019).
