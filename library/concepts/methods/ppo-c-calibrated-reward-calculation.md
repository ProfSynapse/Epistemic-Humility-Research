---
aliases:
- PPO-C
- PPO with Calibrated Reward Calculation
tags:
- kg/method
- concept
- method
kg:
  id: method:ppo-c-calibrated-reward-calculation
  type: method
  status: canonical
area: methods
related:
- '[[2410.09724--taming-overconfidence-rlhf]]'
- '[[proximal-policy-optimization]]'
- '[[ppo-m-calibrated-reward-modeling]]'
relationships:
- type: proposed_by
  target: '[[2410.09724--taming-overconfidence-rlhf]]'
  target_id: paper:2410.09724
  confidence: high
- type: derived_from
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: high
- type: related_to
  target: '[[ppo-m-calibrated-reward-modeling]]'
  target_id: method:ppo-m-calibrated-reward-modeling
  confidence: high
---

PPO-C leaves the reward model unchanged but adjusts the reward at training time:
it compares the current unbiased reward (computed after stripping the expressed
confidence token) to an exponential moving average of past rewards, giving
above-average responses a bonus proportional to their expressed confidence and
below-average ones a matching penalty. This couples the reward to whether the
model's confidence tracks its relative performance.

**Why it matters here:** it is a reward-model-free alternative to
[[ppo-m-calibrated-reward-modeling]]: any PPO setup can adopt it as a small reward
post-processing step, with no reward-model retraining and no extra labeled data,
making it a cheap calibration intervention to consider for preference-tuned arms.

**Lineage:** a reward-calculation-stage intervention on
[[proximal-policy-optimization]], complementary to the reward-modeling-stage PPO-M.
