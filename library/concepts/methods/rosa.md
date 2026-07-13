---
aliases:
- Randomized Objectives Set Actions
- ROSA+Max
- ROSA+Softmax
- reward-uncertainty RL objective
tags:
- kg/method
- concept
- method
kg:
  id: method:rosa
  type: method
  status: canonical
area: methods
related:
- '[[2606.03962--reward-uncertainty-behavioral-diversity]]'
- '[[policy-gradient]]'
- '[[reward-model]]'
- '[[reward-model-overestimation-undermines-rl-factuality]]'
- '[[reward-uncertainty-induces-calibrated-behavioral-diversity]]'
relationships:
- type: proposed_by
  target: '[[2606.03962--reward-uncertainty-behavioral-diversity]]'
  target_id: paper:2606.03962
  confidence: high
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[reward-model-overestimation-undermines-rl-factuality]]'
  target_id: mechanism:reward-model-overestimation-undermines-rl-factuality
  confidence: medium
- type: related_to
  target: '[[reward-uncertainty-induces-calibrated-behavioral-diversity]]'
  target_id: mechanism:reward-uncertainty-induces-calibrated-behavioral-diversity
  confidence: medium
---

A reformulation of the reinforcement learning objective that replaces the scalar reward with a distribution over reward functions and applies a nonlinear objective over sets of actions rather than single actions. Working in the contextual bandit setting, the framework derives a principled gradient estimator and proves the objective generalizes both vanilla policy gradient and action-set approaches. Two concrete empirical variants are ROSA+Max (maximum reward under the distribution) and ROSA+Softmax (softmax aggregation over reward samples).

**Why it matters here:** Provides a theoretically grounded mechanism for inducing calibrated behavioral diversity from reward uncertainty alone, without the fragile trade-offs of entropy regularization or heuristic diversity bonuses. Relevant to the locked training-regimen study because reward model imperfection is the practical motivation for studying abstention training: ROSA's framing predicts that a policy trained under a distribution of reward functions will exhibit wider behavioral coverage than a policy trained against a fixed scalar reward.

**Lineage:** Extends policy-gradient and action-set RL approaches; proposed in arXiv:2606.03962 by GX-Chen et al. (NYU / Google DeepMind, 2026).
