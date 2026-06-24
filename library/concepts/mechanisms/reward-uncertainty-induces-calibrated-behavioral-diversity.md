---
aliases:
- diversity as rational response to reward uncertainty
- reward-distribution diversity mechanism
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reward-uncertainty-induces-calibrated-behavioral-diversity
  type: mechanism
  status: canonical
cause: "Replacing the scalar RL reward with a distribution over reward functions and applying a nonlinear objective over sets of actions (the ROSA objective)"
effect: "Calibrated behavioral diversity emerges naturally, remains controllable through the reward function distribution, and is obtained without sacrificing expected reward"
polarity: enables
related:
- '[[2606.03962--reward-uncertainty-behavioral-diversity]]'
- '[[rosa]]'
- '[[policy-gradient]]'
- '[[reward-model]]'
- '[[reward-model-overestimation-undermines-rl-factuality]]'
- '[[conservative-reward-model]]'
relationships:
- type: supported_by
  target: '[[2606.03962--reward-uncertainty-behavioral-diversity]]'
  target_id: paper:2606.03962
  confidence: high
- type: related_to
  target: '[[rosa]]'
  target_id: method:rosa
  confidence: high
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
  confidence: high
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: high
- type: related_to
  target: '[[reward-model-overestimation-undermines-rl-factuality]]'
  target_id: mechanism:reward-model-overestimation-undermines-rl-factuality
  confidence: high
- type: related_to
  target: '[[conservative-reward-model]]'
  target_id: method:conservative-reward-model
  confidence: high
---

When the reward function is not perfectly known, a rational agent should maintain uncertainty over which actions are best, making diversity the natural response rather than a penalty term to be tuned. The ROSA framework formalizes this by defining the objective over distributions of reward functions, so the gradient estimator automatically accounts for reward uncertainty when shaping the policy. Unlike entropy regularization, which forces stochasticity regardless of reward structure, or diversity bonuses, which apply heuristic metrics that can misalign policy rankings, the ROSA objective ties diversity directly to the structure of reward uncertainty. Calibration of the diversity is then controllable by choosing the reward function distribution rather than by tuning auxiliary hyperparameters.
