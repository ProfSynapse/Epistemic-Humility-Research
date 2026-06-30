---
aliases:
- Training for a specific target coverage reallocates model capacity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:coverage-specific-capacity-reallocation
  type: mechanism
  status: canonical
cause: "Optimizing the network for a specific target coverage rather than a single coverage-agnostic confidence ranking."
effect: "Capacity is reallocated toward the inputs that will be answered at that coverage, so a model trained for the operating coverage beats a single ranking thresholded to many coverages."
polarity: increases
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selectivenet]]'
- '[[selective-risk]]'
relationships:
- type: supported_by
  target: '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
  target_id: paper:1901.09192
  confidence: high
- type: related_to
  target: '[[selectivenet]]'
  target_id: method:selectivenet
  confidence: medium
- type: related_to
  target: '[[selective-risk]]'
  target_id: metric:selective-risk
  confidence: medium
---

Because SelectiveNet bakes the target coverage into its objective, it tailors the
representation and gate to the inputs it will actually answer at that coverage;
the paper finds a model trained for its operating coverage outperforms one trained
once and thresholded to that coverage, evidencing coverage-specific capacity
reallocation (Geifman and El-Yaniv 2019).
