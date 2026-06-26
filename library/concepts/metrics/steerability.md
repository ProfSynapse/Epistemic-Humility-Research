---
aliases:
- steerability
- per-input steerability
- propensity-curve slope
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:steerability
  type: metric
  status: canonical
area: metrics
related:
- '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
- '[[steering-vector]]'
- '[[contrastive-activation-addition]]'
relationships:
- type: proposed_by
  target: '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
  target_id: paper:2407.12404
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
---

Steerability is Tan et al.'s per-input measure of how strongly a steering vector
moves a model's behavior: the slope of the propensity curve, i.e. the change in
the model's log-probability of the target behavior as the steering multiplier is
swept. It is defined per input, so its distribution (not just its mean) exposes
how reliable a steering direction is across a dataset.

**Why it matters here:** Steerability makes the sign and reliability of a
steering direction measurable per item. A direction can have positive mean
steerability yet a large fraction of negatively-steerable ("anti-steerable")
inputs, which is exactly the probe-vs-causal sign-dissociation regime the
H_monitor read-out must contend with.

**Lineage:** Defined for [[contrastive-activation-addition]] steering vectors;
generalizes the qualitative "does steering work" question into a per-input
distributional quantity.
