---
aliases:
- Residual Connection Refines Rather Than Overrides Prediction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:residual-connection-refines-not-overrides
  type: mechanism
  status: canonical
cause: Interaction between the [[residual-stream]] and feed-forward layer output at each [[transformer-feed-forward-layer]]
effect: Model output is refined bottom-up with roughly one-third of predictions stabilized in lower layers and the majority before the final layer; the feed-forward layer rarely overrides the residual outright and instead produces compromise predictions
polarity: enables
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[residual-stream]]'
- '[[transformer-feed-forward-layer]]'
- '[[residual-stream-refinement]]'
relationships:
- type: supported_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
---

Geva et al. (arXiv:2012.14913) trace the evolution of token predictions across layers and find that the residual stream progressively accumulates information rather than being overwritten. About one-third of final predictions are already stable by the lower layers, and most are set before the last layer, with feed-forward contributions acting as targeted refinements to an existing trajectory. When the feed-forward layer disagrees with the residual, the combination typically lands between the two rather than fully adopting either, indicating a cooperative rather than competitive update rule.
