---
aliases:
- evidence integration task
- sequential evidence aggregation
- multi-task evidence accumulation
tags:
- kg/term
- concept
- term
kg:
  id: term:evidence-accumulation-task
  type: term
  status: canonical
area: neuroscience
related: []
relationships: []
---

The evidence-accumulation task is a canonical neuroscience paradigm in which an agent
receives a sequence of noisy observations, each partially informative about a hidden
ground-truth state, and must integrate them over time before committing to a decision at
trial end. In the multi-task framing of arXiv:2209.07431, observations carry information
about multiple latent factors simultaneously, requiring a joint estimate of all factors to
be maintained throughout the trial. This structure is exactly the setting in which
[[multi-task-learning]] pressure provably induces [[disentangled-representation|disentangled
representations]] and, in RNNs, spontaneously produces a [[continuous-attractor]] geometry.

**Why it matters here:** Sequential evidence integration is a mechanistic analogy for how
language models accumulate context tokens before generating a response, suggesting that
transformers may similarly form well-calibrated internal estimates of what they know
through an implicit accumulation process.

**Lineage:** no upstream lineage; provides the training framework within which
[[continuous-attractor]] dynamics and [[disentangled-representation|disentanglement]] are
jointly observed.
