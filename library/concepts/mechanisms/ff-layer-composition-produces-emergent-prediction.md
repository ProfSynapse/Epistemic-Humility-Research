---
aliases:
- Feed-Forward Layer Composition Produces Emergent Predictions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:ff-layer-composition-produces-emergent-prediction
  type: mechanism
  status: canonical
cause: Weighted aggregation of hundreds of simultaneously active memory cells within a single [[transformer-feed-forward-layer]]
effect: Layer output prediction differs from all individual memory cells' top predictions in at least 68% of examples, producing emergent compositional outputs not attributable to any single memory
polarity: enables
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[transformer-feed-forward-layer]]'
- '[[intra-layer-memory-composition]]'
relationships:
- type: supported_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
- type: related_to
  target: '[[intra-layer-memory-composition]]'
  target_id: term:intra-layer-memory-composition
---

Each transformer feed-forward layer activates hundreds of memory cells simultaneously, and their weighted outputs are summed to produce the layer's contribution to the residual stream. Geva et al. (arXiv:2012.14913) show that in at least 68% of examples the final layer prediction does not match the top prediction of any individual memory cell, indicating that emergent compositional outputs arise from the aggregation rather than from any dominant cell. This mechanism implies that feed-forward knowledge is distributed and context-dependent, not reducible to single stored associations.
