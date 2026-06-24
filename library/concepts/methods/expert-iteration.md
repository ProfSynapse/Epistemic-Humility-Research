---
aliases:
- EI
- expert iteration RL
tags:
- kg/method
- concept
- method
kg:
  id: method:expert-iteration
  type: method
  status: canonical
area: methods
related:
- '[[2406.10162--sycophancy-to-subterfuge]]'
- '[[proximal-policy-optimization]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2406.10162--sycophancy-to-subterfuge]]'
  target_id: paper:2406.10162
  confidence: high
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
---

An RL algorithm that iterates between generating N candidate responses per prompt, selecting the best subset using a reward signal, and fine-tuning the policy on the selected winners; alternates between search and supervised learning phases.

**Why it matters here:** The primary training algorithm in 2406.10162; produces reward-tampering generalization and is compared to PPO; broadly used as an alternative to PPO for aligning LLM assistants.

**Lineage:** Algorithm from Anthony et al. 2017; used in 2406.10162 with N=64 and P=1024.
