---
aliases:
- A fixed steering direction creates an implicit RL curriculum
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fixed-steering-vector-induces-policy-curriculum
  type: mechanism
  status: canonical
cause: "A fixed [[steering-vector]] remains aligned as policy weights change during [[vector-steered-policy-optimization]]."
effect: "The same intervention elicits progressively stronger target behavior and supplies increasingly informative self-distillation examples."
polarity: enables
related:
- '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
- '[[vector-steered-policy-optimization]]'
- '[[steering-vector]]'
relationships:
- type: supported_by
  target: '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
  target_id: paper:2605.15604
  confidence: high
- type: related_to
  target: '[[vector-steered-policy-optimization]]'
  target_id: method:vector-steered-policy-optimization
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Across VSPO checkpoints, the fixed expertise vector continued to move outputs
toward the target style, with stronger effects later in training. The authors
interpret this persistence as an automatic curriculum rather than evidence that
all steering directions will remain stable.
