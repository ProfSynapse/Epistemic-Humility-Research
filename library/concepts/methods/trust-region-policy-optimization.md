---
aliases:
- TRPO
- Trust Region Policy Optimization (TRPO)
tags:
- kg/method
- concept
- method
kg:
  id: method:trust-region-policy-optimization
  type: method
  status: canonical
area: methods
---

Trust Region Policy Optimization (Schulman et al. 2015) is a policy gradient algorithm that enforces each update to stay within a KL-divergence trust region, solved via conjugate gradient and line search, which guarantees monotonic policy improvement but at substantial per-step computational cost.

**Why it matters here:** TRPO is the theoretical precursor to PPO; understanding the trust-region idea clarifies why [[proximal-policy-optimization]] approximates it cheaply with a clipped surrogate, which in turn motivates why offline preference methods like DPO and KTO are attractive alternatives for fine-tuning scale.

**Lineage:** extended by [[proximal-policy-optimization]] via the [[clipped-surrogate-objective]].
