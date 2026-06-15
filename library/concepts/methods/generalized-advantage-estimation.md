---
aliases:
- GAE
- Generalized Advantage Estimation (GAE)
tags:
- kg/method
- concept
- method
kg:
  id: method:generalized-advantage-estimation
  type: method
  status: canonical
area: methods
related:
- '[[proximal-policy-optimization]]'
- '[[policy-gradient]]'
relationships:
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
---

Generalized Advantage Estimation (GAE) computes a weighted sum of multi-step
temporal-difference (TD) residuals, controlled by a parameter lambda between 0
and 1. When lambda equals 0, the estimator collapses to a one-step TD target
(low variance, high bias); when lambda equals 1, it reduces to a full
Monte-Carlo return (low bias, high variance). Practitioners set lambda to an
intermediate value to navigate this trade-off and stabilize policy-gradient
training.

**Why it matters here:** GAE is the advantage estimator used inside PPO, which
is the RL backbone the study compares against DPO and KTO; understanding GAE
clarifies why PPO requires a trained critic (value network) while
[[group-relative-policy-optimization]] replaces it with group-level reward
statistics.

**Lineage:** used by [[proximal-policy-optimization]] as its advantage estimator;
part of the broader family of [[policy-gradient]] variance-reduction techniques.
