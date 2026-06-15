---
aliases:
- RM
- preference model
- reward modeling
tags:
- kg/method
- concept
- method
kg:
  id: method:reward-model
  type: method
  status: canonical
area: methods
related:
- '[[reinforcement-learning-from-human-feedback]]'
- '[[proximal-policy-optimization]]'
- '[[bradley-terry-model]]'
- '[[outcome-reward-model]]'
relationships:
- type: derived_from
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
- type: related_to
  target: '[[bradley-terry-model]]'
  target_id: term:bradley-terry-model
- type: related_to
  target: '[[outcome-reward-model]]'
  target_id: term:outcome-reward-model
---

A reward model is trained on human pairwise comparisons of model outputs to predict which response a human labeler would prefer, producing a scalar reward for any given (prompt, response) pair. In the InstructGPT pipeline, a 6B SFT model with its unembedding layer replaced by a scalar head is trained on a comparison dataset using a Bradley-Terry-style cross-entropy objective. The scalar output then serves as the reward signal for the PPO fine-tuning stage.

**Why it matters here:** The reward model is the component that [[direct-preference-optimization]] eliminates: DPO reparameterizes the RLHF objective so that preference learning collapses into a single classification loss, removing the need to train and query a separate RM. Understanding this architectural role clarifies the practical and stability advantages DPO claims over PPO-based RLHF.

**Lineage:** extends [[reinforcement-learning-from-human-feedback]]; [[bradley-terry-model]] is the pairwise comparison model underlying the RM loss; acts as prerequisite-of [[proximal-policy-optimization]] in the RLHF pipeline.
