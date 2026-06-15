---
aliases:
- ORM
- outcome supervision
- outcome reward
- Outcome Reward Model (ORM)
tags:
- kg/term
- concept
- term
kg:
  id: term:outcome-reward-model
  type: term
  status: canonical
area: methods
related:
- '[[reward-model]]'
- '[[group-relative-policy-optimization]]'
relationships:
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[group-relative-policy-optimization]]'
  target_id: method:group-relative-policy-optimization
---

An outcome reward model assigns a single scalar reward to a complete reasoning chain based solely on whether the final answer is correct, without scoring intermediate steps. This contrasts with a process reward model, which supervises each reasoning step individually. ORMs are simpler to construct (they require only final-answer labels) but may reinforce flawed reasoning chains that happen to reach a correct answer.

**Why it matters here:** GRPO in the DeepSeekMath study uses an ORM signal to train mathematical reasoning, illustrating how outcome-only feedback shapes policy behavior differently from step-level supervision.

**Lineage:** related to [[reward-model]] (the general class of preference predictors); [[group-relative-policy-optimization]] uses ORM scores as the reward signal in its clipped policy update.
