---
aliases:
- Interchange Intervention Accuracy
- IntInvAcc
- IIT accuracy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:interchange-intervention-accuracy
  type: metric
  status: canonical
area: metrics
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[causal-abstraction]]'
relationships:
- type: proposed_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: high
- type: related_to
  target: '[[causal-abstraction]]'
  target_id: term:causal-abstraction
  confidence: high
---

Interchange intervention accuracy is the proportion of aligned source and base interventions for which a neural model and a high-level causal model produce matching outputs. A value of one establishes the tested causal-abstraction relation for the covered inputs.

**Why it matters here:** It measures whether an aligned internal representation has the intended causal role, beyond whether a probe can decode it.

**Lineage:** The metric operationalizes causal-abstraction analysis through interchange interventions.
