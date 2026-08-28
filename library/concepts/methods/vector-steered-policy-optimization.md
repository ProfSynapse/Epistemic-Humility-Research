---
aliases:
- VSPO
- Vector-Steered Policy Optimization
- Reinforcement learning with activation steering removed at deployment
- Training-time activation steering with unsteered deployment
tags:
- kg/method
- concept
- method
kg:
  id: method:vector-steered-policy-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
- '[[group-relative-policy-optimization]]'
- '[[on-policy-distillation]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
  target_id: paper:2605.15604
  confidence: high
- type: derived_from
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
- type: variation_of
  target: '[[on-policy-distillation]]'
  target_id: method:on-policy-distillation
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Vector-Steered Policy Optimization generates each GRPO rollout group under a
range of positive, zero, and negative steering-vector intensities. It rewards
task quality together with the steering coefficient, then updates the
unsteered policy from the steered trajectories.

**Why it matters here:** VSPO uses an activation intervention only during
training and distills useful steered behaviors into a policy that needs no
intervention at deployment.

**Lineage:** It modifies [[group-relative-policy-optimization]] with structured
latent exploration and is framed as [[on-policy-distillation]].
