---
aliases:
- sink ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:sink-ratio
  type: metric
  status: canonical
area: metrics
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[attention-sink]]'
relationships:
- type: measured_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
---

Sink ratio is the fraction of total attention mass a model directs at
designated sink tokens (typically the start token and early delimiters),
aggregated across heads and layers, used as the primary scalar readout of
attention-sink strength.

**Why it matters here:** Sun et al. use sink ratio as the outcome variable
across all ablations: it drops from roughly 46% to 1.2-13.0% under
long-range-only training, to 4.5-6.4% under input-conditioned attention gating,
and stays largely unchanged under normalization ablations that nonetheless
collapse spike magnitude, letting the paper separate which interventions
decouple sinks from massive activations versus which eliminate sinks outright.

**Lineage:** no formal derivation edges recorded in this vault yet.
