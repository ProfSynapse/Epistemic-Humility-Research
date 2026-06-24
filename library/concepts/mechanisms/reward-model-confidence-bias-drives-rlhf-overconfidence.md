---
aliases:
- Reward-model confidence bias drives RLHF overconfidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reward-model-confidence-bias-drives-rlhf-overconfidence
  type: mechanism
  status: canonical
cause: "Reward models trained on standard pairwise preference data without confidence conditioning systematically prefer responses that express high confidence, regardless of whether those responses are correct."
effect: "PPO policy optimization amplifies verbalized overconfidence, because high-confidence outputs receive higher reward and are reinforced."
polarity: increases
related:
- '[[2410.09724--taming-overconfidence-rlhf]]'
- '[[reward-model]]'
- '[[rlhf-degrades-conditional-calibration]]'
relationships:
- type: supported_by
  target: '[[2410.09724--taming-overconfidence-rlhf]]'
  target_id: paper:2410.09724
  confidence: high
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: high
- type: related_to
  target: '[[rlhf-degrades-conditional-calibration]]'
  target_id: mechanism:rlhf-degrades-conditional-calibration
  confidence: high
---

Leng et al. document on RewardBench that assigning a high confidence score to a
rejected response, or a low score to a chosen one, substantially distorts a reward
model's preference ranking: the model prefers confident phrasing independent of
correctness. Because PPO maximizes reward, this bias is reinforced into the policy
as verbalized [[overconfidence]]. The mechanism sits upstream of
[[rlhf-degrades-conditional-calibration]] and extends it from token-probability
calibration to the verbalized-confidence domain.
