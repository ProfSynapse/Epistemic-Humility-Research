---
aliases:
- RLHF
- Reinforcement Learning from Human Feedback (RLHF)
- human feedback RL
- learning from human feedback
- RLHF fine-tuning
- RLHF-LM
tags:
- kg/method
- concept
- method
kg:
  id: method:reinforcement-learning-from-human-feedback
  type: method
  status: canonical
area: methods
related:
- '[[2203.02155--instructgpt-rlhf]]'
- '[[proximal-policy-optimization]]'
- '[[reward-model]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: proposed_by
  target: '[[2203.02155--instructgpt-rlhf]]'
  target_id: paper:2203.02155
  confidence: high
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
---

Reinforcement Learning from Human Feedback is a three-stage alignment pipeline: start from a pretrained model, fine-tune it on demonstrations (SFT), train a reward model on human preference pairs, then use RL (typically PPO) to optimize the policy against the reward model subject to a KL-divergence penalty that prevents the policy from drifting too far from the SFT reference. [[direct-preference-optimization]] and [[kahneman-tversky-optimization]] both derive from the KL-constrained RLHF objective, replacing the RL loop with a closed-form classification loss.

**Why it matters here:** RLHF is the ancestor of the DPO and KTO arms in the locked training-regimen SFT-vs-DPO-vs-KTO abstention study. Understanding how both methods simplify away the reward model and RL loop contextualizes why they are cheaper to train while still inheriting the RLHF alignment objective.

**Lineage:** [[proximal-policy-optimization]] is the canonical RL optimizer used in the RL stage; [[direct-preference-optimization]] and [[kahneman-tversky-optimization]] are offline descendants that eliminate the reward model.
