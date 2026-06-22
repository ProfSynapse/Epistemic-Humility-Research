---
aliases:
- Claude 3.0 Sonnet
tags:
- kg/model
- concept
- model
kg:
  id: model:claude-3-sonnet
  type: model
  status: canonical
area: language-models
related:
- '[[reinforcement-learning-from-human-feedback]]'
- '[[sparse-autoencoder]]'
- '[[sycophancy-feature]]'
relationships:
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[sycophancy-feature]]'
  target_id: term:sycophancy-feature
---

Claude 3 Sonnet is Anthropic's medium-scale production language model released
March 4, 2024, trained with RLHF and constitutional AI methods. It serves as the
primary subject in the Scaling Monosemanticity paper, where sparse autoencoders
were applied to its mid-layer residual stream activations to identify
interpretable features at scale.

**Why it matters here:** Claude 3 Sonnet is the model in which sycophancy
features, safety-relevant features, and other behaviorally significant directions
were mechanistically identified, making it an empirical anchor for claims about
how alignment-related behaviors are represented internally.

**Lineage:** trained via [[reinforcement-learning-from-human-feedback]]; studied
through [[sparse-autoencoder]] probes in the Scaling Monosemanticity line of work.
