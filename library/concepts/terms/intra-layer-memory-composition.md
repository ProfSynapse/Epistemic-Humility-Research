---
aliases:
- memory aggregation
- compositional memory output
- weighted memory combination
- Intra-Layer Memory Composition
tags:
- kg/term
- concept
- term
kg:
  id: term:intra-layer-memory-composition
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
relationships:
- type: proposed_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
---

Intra-layer memory composition is the process by which a single feed-forward layer combines hundreds of simultaneously active memory cells via weighted summation to produce a layer-level output distribution. In practice, 10-50% of the d_m=4096 memory dimensions activate together, and their weighted sum yields a prediction that is qualitatively different from what any individual cell would produce alone: in at least 68% of examples, the layer's top-predicted token differs from every individual memory cell's top prediction.

**Why it matters here:** Understanding how FF layers aggregate sub-predictions into a combined output is directly relevant to calibration research: if a model's expressed confidence reflects a blend of many partially-active memories rather than a single decisive retrieval, that compositional structure may explain why models are overconfident or miscalibrated on borderline questions.

**Lineage:** concept introduced in [[2012.14913--transformer-ff-layers-key-value-memories]]; closely related to the broader notion of [[ffn-as-key-value-memory]] and situated within [[transformer-feed-forward-layer]] mechanics.
