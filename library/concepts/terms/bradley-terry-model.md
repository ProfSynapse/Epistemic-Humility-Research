---
aliases:
- Bradley-Terry model
- preference model
- reward model
- Bradley-Terry Preference Model
tags:
- kg/term
- concept
- term
kg:
  id: term:bradley-terry-model
  type: term
  status: canonical
area: methods
related:
- '[[direct-preference-optimization]]'
- '[[reward-model]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
- type: related_to
  target: '[[reward-model]]'
  target_id: method:reward-model
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
---

The Bradley-Terry model assigns a scalar score to each item and models the probability that one item is preferred over another as a softmax over the score difference. In the RLHF and DPO context the "score" is a reward value, making the model a principled way to convert human pairwise comparisons into a continuous reward signal. DPO reparameterizes the Bradley-Terry reward in terms of the policy itself, eliminating the need to train and query a separate reward model at inference time.

**Why it matters here:** The Bradley-Terry assumption underlies the [[direct-preference-optimization]] loss used in the DPO arm of the locked training-regimen experiment, so its distributional assumptions (transitivity, scale-free rewards) implicitly constrain what DPO can learn from abstention preference pairs.

**Lineage:** used as the statistical backbone of [[direct-preference-optimization]]; relates to [[reward-model]] as the parameterization that reward models instantiate.
