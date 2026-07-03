---
aliases:
- PS
- Parallelism Score metric
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:parallelism-score
  type: metric
  status: canonical
area: neuroscience
related:
- '[[abstract-representations]]'
relationships:
- type: related_to
  target: '[[abstract-representations]]'
  target_id: term:abstract-representations
  confidence: high
---

The Parallelism Score (PS) is the average cosine similarity between linear decoder vectors (coding directions) for the same rule dichotomy measured across different task contexts, averaged over all context pairs within a rule domain. A PS of 1 indicates that the representational shift produced by changing one rule variable is identical in direction regardless of what other rule variables are active, which is the geometric signature of [[abstract-representations]]. PS is computable from both fMRI BOLD voxel activations and artificial neural network hidden-layer activations, enabling direct biological-to-artificial comparison.

**Why it matters here:** PS provides a quantitative, geometry-grounded handle on whether a network's internal representations support compositional reuse. A high PS implies that rule knowledge is encoded independently of context, a prerequisite for the kind of reliable, calibrated generalization studied in epistemic-humility research.

**Lineage:** operationalizes [[abstract-representations]]; used in [[c-pro-task]] experiments to compare human fMRI, [[primitives-pretraining]] ANNs, and baseline ANNs on compositional generalization.
