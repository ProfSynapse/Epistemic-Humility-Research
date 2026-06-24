---
aliases:
- PPO-M
- PPO with Calibrated Reward Modeling
tags:
- kg/method
- concept
- method
kg:
  id: method:ppo-m-calibrated-reward-modeling
  type: method
  status: canonical
area: methods
related:
- '[[2410.09724--taming-overconfidence-rlhf]]'
- '[[proximal-policy-optimization]]'
- '[[reward-model]]'
- '[[verbalized-confidence]]'
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
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
---

PPO-M fine-tunes an existing reward model on an augmented dataset where each
response appears paired with both high and low random confidence scores, adding a
calibration loss that teaches the reward model to prefer high confidence on chosen
responses and low confidence on rejected ones. The calibrated reward model then
replaces the vanilla one in the standard PPO loop.

**Why it matters here:** it strips the confidence-score bias out of the reward
model before that bias can propagate into the policy, improving verbalized
calibration with no ground-truth accuracy labels and no change to the PPO pipeline.
It is one half of the answer to why RLHF produces
[[overconfidence]], paired with [[ppo-c-calibrated-reward-calculation]].

**Lineage:** a reward-modeling-stage intervention on
[[proximal-policy-optimization]], proposed alongside PPO-C and the DPO port
[[cdpo-calibrated-dpo]].
