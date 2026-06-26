---
aliases:
- DPO-derived token rewards enable RL policy optimization
- preference-derived token rewards feed policy optimization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-token-rewards-enable-rl-policy-optimization
  type: mechanism
  status: canonical
cause: "A DPO-trained policy ratio is reused as a token-wise implicit reward signal."
effect: "A later RL policy-optimization stage can optimize dense token-level feedback rather than only sparse sentence-level preferences."
polarity: enables
related:
- '[[2404.18922--dpo-meets-ppo-reinforced-token-optimization-rlhf]]'
- '[[reinforced-token-optimization]]'
- '[[direct-preference-optimization]]'
- '[[proximal-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[2404.18922--dpo-meets-ppo-reinforced-token-optimization-rlhf]]'
  target_id: paper:2404.18922
  confidence: high
- type: related_to
  target: '[[reinforced-token-optimization]]'
  target_id: method:reinforced-token-optimization
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: high
---

Zhong et al. argue that DPO's policy-ratio form can be interpreted as a token-wise quality signal, then used as dense reward feedback for PPO-style optimization. In their experiments, the resulting RTO method outperformed PPO and direct preference-learning baselines on instruction-following and summarization evaluations.
