---
aliases:
- Vector steering reveals rare useful behavior during RL
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:vector-steering-exposes-rare-high-reward-rollouts
  type: mechanism
  status: canonical
cause: "Rollouts are sampled at multiple intensities along a behavior-linked [[steering-vector]]."
effect: "Rare target-behavior trajectories appear more often and provide informative relative advantages for [[group-relative-policy-optimization]]."
polarity: enables
related:
- '[[2605.15604--vspo-vector-steered-policy-optimization-behavioral-control]]'
- '[[vector-steered-policy-optimization]]'
- '[[steering-vector]]'
- '[[group-relative-policy-optimization]]'
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
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
  confidence: high
---

VSPO generated structured variation in expertise, verbosity, and resistance to
misleading context where ordinary sampling provided sparse reward signal. The
paper proves a faster iteration bound than reward-shaped GRPO under a bandit
condition that requires steering-induced distributions to align with reward.
