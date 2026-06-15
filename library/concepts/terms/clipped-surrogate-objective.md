---
aliases:
- PPO clip objective
- clip ratio
- epsilon clipping
tags:
- kg/term
- concept
- term
kg:
  id: term:clipped-surrogate-objective
  type: term
  status: canonical
area: methods
related:
- '[[1707.06347--proximal-policy-optimization]]'
- '[[trust-region-policy-optimization]]'
relationships:
- type: proposed_by
  target: '[[1707.06347--proximal-policy-optimization]]'
  target_id: paper:1707.06347
  confidence: high
- type: variation_of
  target: '[[trust-region-policy-optimization]]'
  target_id: method:trust-region-policy-optimization
---

The clipped surrogate objective is the core PPO training loss: min(r_t * A_t, clip(r_t, 1-epsilon, 1+epsilon) * A_t), where r_t is the probability ratio of the new policy to the old policy and A_t is the estimated advantage. Clipping removes any gradient incentive to push the ratio outside the interval [1-epsilon, 1+epsilon], enforcing a soft first-order trust region without requiring constraint optimisation.

**Why it matters here:** The clipped objective is what makes PPO tractable for RLHF at language-model scale; DPO eliminates the need for it entirely by reparameterising the objective as a classification loss, which is part of why DPO is simpler to implement than the PPO-based RLHF alternative compared in the abstention study.

**Lineage:** introduced in [[1707.06347--proximal-policy-optimization]] as a practical variant of [[trust-region-policy-optimization]].
