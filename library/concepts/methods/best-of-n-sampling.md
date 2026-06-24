---
aliases:
- BoN
- rejection sampling
- Bo16
- best-of-N
tags:
- kg/method
- concept
- method
kg:
  id: method:best-of-n-sampling
  type: method
  status: canonical
area: methods
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[reward-model]]'
- '[[supervised-finetuning]]'
- '[[proximal-policy-optimization]]'
- '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
relationships:
- type: proposed_by
  target: '[[2310.06452--rlhf-generalisation-diversity]]'
  target_id: paper:2310.06452
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
  confidence: medium
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: medium
- type: related_to
  target: '[[rlhf-rl-optimisation-collapses-per-input-diversity]]'
  target_id: mechanism:rlhf-rl-optimisation-collapses-per-input-diversity
  confidence: medium
---

An inference-time policy that generates N outputs from a base model and returns the one ranked highest by a reward model. Requires no RL training; used as an analysis baseline to isolate reward-model effects from RL-optimisation effects. High inference cost makes it impractical as a deployed policy.

**Why it matters here:** Because BoN uses the reward model without RL optimisation, comparing BoN and RLHF on diversity and generalisation isolates which differences are attributable to reward-model filtering versus the RL training loop itself.

**Lineage:** Described in Menick et al. (2022) and Nakano et al. (2022); used as analysis baseline in Kirk et al. (2023) (arXiv 2310.06452) and Rafailov et al. (2023) (DPO).
