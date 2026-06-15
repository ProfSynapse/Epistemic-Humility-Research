---
aliases:
- PPO clipping prevents destabilizing large policy updates
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ppo-clip-prevents-large-policy-updates
  type: mechanism
  status: canonical
cause: '[[clipped-surrogate-objective]] bounding the probability ratio within [1-epsilon, 1+epsilon]'
effect: Policy updates remain within a trust region without requiring expensive second-order optimization, preserving training stability
polarity: prevents
related:
- '[[1707.06347--proximal-policy-optimization]]'
- '[[clipped-surrogate-objective]]'
relationships:
- type: supported_by
  target: '[[1707.06347--proximal-policy-optimization]]'
  target_id: paper:1707.06347
  confidence: high
- type: related_to
  target: '[[clipped-surrogate-objective]]'
  target_id: term:clipped-surrogate-objective
---

[[proximal-policy-optimization]] clips the importance-sampling ratio between the new and old policy so that no single gradient step can move the policy arbitrarily far. This first-order approximation to [[trust-region-policy-optimization]] achieves similar stability guarantees at a fraction of the computational cost. The PPO paper (arXiv:1707.06347) demonstrates that clipping alone is sufficient to match or exceed TRPO on continuous control and Atari benchmarks.
