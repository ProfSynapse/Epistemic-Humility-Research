---
aliases:
- GRPO distills steered behavior into the unsteered policy
- Activation steering during reinforcement learning needs no deployment intervention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:policy-optimization-internalizes-steered-behavior
  type: mechanism
  status: canonical
cause: "[[vector-steered-policy-optimization]] computes advantages on steered self-rollouts but recomputes token probabilities under the unsteered policy."
effect: "The policy weights learn to produce selected target behaviors without steering at inference time."
polarity: causes
related:
- '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
- '[[vector-steered-policy-optimization]]'
- '[[steering-vector-distillation]]'
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
  target: '[[steering-vector-distillation]]'
  target_id: method:steering-vector-distillation
  confidence: high
---

The intervention changes only rollout generation. GRPO updates use the
unsteered policy probabilities, so the deployed policy inherits the selected
behavior without an activation hook. Experiments report stronger behavioral
control and equal or higher task accuracy than the compared baselines.
