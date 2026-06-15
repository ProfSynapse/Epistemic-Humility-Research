---
aliases:
- DPO reparameterization eliminates the reward model
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-eliminates-reward-model
  type: mechanism
  status: canonical
cause: Reparameterizing the [[reinforcement-learning-from-human-feedback]] constrained-reward-maximization objective using the optimal policy's closed-form relationship to the reference policy
effect: The reward function is implicitly represented by the language model itself, removing the need for a separately trained [[reward-model]] or RL optimization loop
polarity: enables
related:
- '[[2305.18290--direct-preference-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[reward-model]]'
relationships:
- type: supported_by
  target: '[[2305.18290--direct-preference-optimization]]'
  target_id: paper:2305.18290
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
---

[[direct-preference-optimization]] reparameterizes the RLHF objective so the optimal policy is expressed directly in terms of the reference policy and the reward, eliminating the need to train a separate reward model. Because the loss collapses to a binary cross-entropy over preference pairs, no RL environment or reward-model inference step is required at training time. This is supported by the DPO paper (arXiv:2305.18290), which derives the equivalence analytically and demonstrates competitive alignment without a critic.
