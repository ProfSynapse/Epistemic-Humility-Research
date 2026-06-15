---
aliases:
- PPO
- PPO-Clip
- Proximal Policy Optimization (PPO)
- PPO-ptx
tags:
- kg/method
- concept
- method
kg:
  id: method:proximal-policy-optimization
  type: method
  status: canonical
area: methods
related:
- '[[1707.06347--proximal-policy-optimization]]'
- '[[trust-region-policy-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[generalized-advantage-estimation]]'
- '[[clipped-surrogate-objective]]'
relationships:
- type: proposed_by
  target: '[[1707.06347--proximal-policy-optimization]]'
  target_id: paper:1707.06347
  confidence: high
- type: derived_from
  target: '[[trust-region-policy-optimization]]'
  target_id: method:trust-region-policy-optimization
- type: required_by
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[generalized-advantage-estimation]]'
  target_id: method:generalized-advantage-estimation
- type: related_to
  target: '[[clipped-surrogate-objective]]'
  target_id: term:clipped-surrogate-objective
---

Proximal Policy Optimization (Schulman et al. 2017) is an on-policy RL algorithm that optimises the policy using a clipped surrogate objective, preventing update steps from moving the policy too far from the previous iterate without the expensive constraint-solving of TRPO. In the InstructGPT RLHF pipeline (PPO-ptx), a per-token KL penalty against the SFT reference model is added to the reward signal to prevent reward over-optimisation, and a fraction of pretraining gradient is mixed in to reduce performance regressions on public benchmarks.

**Why it matters here:** PPO is the RL backbone that RLHF-based alignment uses; DPO and KTO were both designed partly to sidestep its instability and computational overhead, so understanding PPO situates why offline preference optimisation methods are attractive for the abstention study.

**Lineage:** derives from [[trust-region-policy-optimization]] via the [[clipped-surrogate-objective]]; is a prerequisite of [[reinforcement-learning-from-human-feedback]]; replaced by [[group-relative-policy-optimization]] in GRPO/DeepSeekMath.
