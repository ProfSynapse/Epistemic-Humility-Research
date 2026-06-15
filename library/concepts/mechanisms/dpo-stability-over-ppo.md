---
aliases:
- DPO training stability vs PPO
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-stability-over-ppo
  type: mechanism
  status: canonical
cause: Framing preference alignment as a binary classification loss over [[preference-pair-data]] rather than an RL problem
effect: More stable training without the sensitivity to reward hacking and hyperparameter tuning that [[proximal-policy-optimization]] requires
polarity: enables
related:
- '[[2305.18290--direct-preference-optimization]]'
- '[[preference-pair-data]]'
- '[[proximal-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[2305.18290--direct-preference-optimization]]'
  target_id: paper:2305.18290
  confidence: high
- type: related_to
  target: '[[preference-pair-data]]'
  target_id: dataset:preference-pair-data
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
---

[[direct-preference-optimization]] avoids the instability sources inherent to [[proximal-policy-optimization]]: there is no reward model to overfit, no critic to maintain, and no clipping schedule to tune. The single-stage classification objective converges more reliably across hyperparameter settings. The DPO paper (arXiv:2305.18290) demonstrates this empirically by showing competitive or superior performance on summarization and dialogue tasks without the tuning burden of PPO.
