---
aliases:
- Multi-Task Bayesian In-Context Learning
- amortized hierarchical Bayesian in-context learning
tags:
- kg/method
- concept
- method
kg:
  id: method:multi-task-bayesian-in-context-learning
  type: method
  status: canonical
area: methods
related:
- '[[2606.20538--multi-task-bayesian-in-context-learning]]'
- '[[in-context-learning]]'
- '[[prior-data-fitted-network]]'
- '[[uncertainty-quantification]]'
relationships:
- type: proposed_by
  target: '[[2606.20538--multi-task-bayesian-in-context-learning]]'
  target_id: paper:2606.20538
  confidence: high
- type: derived_from
  target: '[[prior-data-fitted-network]]'
  target_id: method:prior-data-fitted-network
  confidence: high
- type: derived_from
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: medium
- type: related_to
  target: '[[uncertainty-quantification]]'
  target_id: term:uncertainty-quantification
  confidence: high
---

Multi-task Bayesian in-context learning is an amortized framework for
hierarchical Bayesian predictive inference. It encodes prior information as a
prefix of in-context datasets and trains a transformer on sequences of prior and
target tasks, so the model learns to map a dataset plus a prior directly to a
predictive distribution. Because the prior is supplied in context, the same
network adapts across families of priors at test time, including priors outside
its meta-training distribution, instead of being locked to the support of a
single training prior.

**Why it matters here:** it is an instance of a model adjusting its own
predictive uncertainty to the regime it is placed in, reaching an oracle Bayesian
posterior orders of magnitude faster than exact inference. That is the
grounded-confidence property the epistemic-humility work cares about, expressed
in a Bayesian regression setting rather than in language-model question
answering.

**Lineage:** an amortized, prior-conditioned extension of
[[prior-data-fitted-network]] that inherits the dataset-to-prediction mapping of
[[in-context-learning]] and adds explicit adaptation to new priors.
