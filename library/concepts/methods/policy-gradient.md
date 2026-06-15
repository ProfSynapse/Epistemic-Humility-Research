---
aliases:
- policy gradient methods
- policy gradient RL
tags:
- kg/term
- concept
- term
kg:
  id: term:policy-gradient
  type: term
  status: canonical
area: methods
related:
- '[[proximal-policy-optimization]]'
- '[[group-relative-policy-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
---

Policy gradient methods are a class of reinforcement learning algorithms that
directly optimize a parameterized policy by estimating the gradient of expected
cumulative reward with respect to policy parameters. The core insight is that
the gradient of the expected return can be written as an expectation over
trajectories sampled from the policy itself, enabling gradient descent without
a learned transition model. REINFORCE is the simplest member; actor-critic
variants reduce variance by subtracting a learned baseline (the critic) from the
raw return.

**Why it matters here:** PPO and GRPO are both policy-gradient methods, and they
sit at the RL end of the training-objective spectrum that the SFT vs DPO vs KTO
abstention study contrasts against offline preference-optimization approaches.

**Lineage:** foundational RL framework; [[proximal-policy-optimization]] and
[[group-relative-policy-optimization]] are constrained variants; [[generalized-advantage-estimation]]
is the standard variance-reduction add-on.
