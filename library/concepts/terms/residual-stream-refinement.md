---
aliases:
- inter-layer refinement
- residual prediction refinement
- layer-wise prediction updating
- Residual Stream Prediction Refinement
tags:
- kg/term
- concept
- term
kg:
  id: term:residual-stream-refinement
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[intra-layer-memory-composition]]'
- '[[transformer-feed-forward-layer]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[intra-layer-memory-composition]]'
  target_id: term:intra-layer-memory-composition
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

The mechanism by which a transformer's final output distribution is constructed incrementally: each feed-forward layer writes an update to the residual stream that nudges the running next-token prediction, rather than replacing it outright. Empirically, roughly one-third of final predictions are already dominant by the lowest layers, and feed-forward layers typically produce "compromise" distributions that blend the residual's current prediction with a layer-specific proposal. This bottom-up accumulation is the basis for logit-lens and tuned-lens analysis.

**Why it matters here:** If predictions crystallize gradually across layers, then interventions (probing, activation patching, knowledge editing) must be applied at the right depth to affect the target fact, which directly constrains where abstention or calibration signals can be injected.

**Lineage:** characterised in [[2012.14913--transformer-ff-layers-key-value-memories]]; related to [[intra-layer-memory-composition]] (how memory coefficients inside one layer combine); exploited by [[residual-stream]] analysis tools such as the logit lens.
