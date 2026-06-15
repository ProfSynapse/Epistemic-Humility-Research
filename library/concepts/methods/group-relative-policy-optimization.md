---
aliases:
- GRPO
- Group Relative Policy Optimization (GRPO)
tags:
- kg/method
- concept
- method
kg:
  id: method:group-relative-policy-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2402.03300--deepseekmath-grpo]]'
- '[[proximal-policy-optimization]]'
- '[[direct-preference-optimization]]'
relationships:
- type: proposed_by
  target: '[[2402.03300--deepseekmath-grpo]]'
  target_id: paper:2402.03300
  confidence: high
- type: derived_from
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
---

Group Relative Policy Optimization (GRPO) is a PPO variant that removes the
separately-trained critic (value network) by estimating the advantage baseline
from the mean and standard deviation of rewards collected across a group of
sampled outputs for the same input question. This group-level normalization
replaces the per-state value function, cutting GPU memory and compute
significantly while preserving the clipped-surrogate stability of PPO.

**Why it matters here:** GRPO is the training algorithm used in DeepSeekMath and
later adopted by reasoning-focused LLMs, making it a relevant data point for
understanding online RL post-training as a complement to the offline
preference-optimization methods (DPO, KTO) studied in the Phase 1 abstention
experiment.

**Lineage:** derives from [[proximal-policy-optimization]] (clips the policy
ratio, uses a group-relative baseline instead of a critic); related to
[[direct-preference-optimization]] as an alternative paradigm for reward-signal
integration.
