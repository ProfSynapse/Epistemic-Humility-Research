---
aliases:
- Stochastic Depth
tags:
- kg/method
- concept
- method
kg:
  id: method:stochastic-depth
  type: method
  status: canonical
area: methods
related:
- '[[2103.17239--going-deeper-image-transformers]]'
relationships:
- type: used_by
  target: '[[2103.17239--going-deeper-image-transformers]]'
  target_id: paper:2103.17239
  confidence: high
---

Stochastic depth is a training-time regularizer that randomly drops entire
residual blocks (bypassing them via the skip connection) with some probability
per training step, then uses the full network at inference. It shortens the
effective network during training while keeping the nominal depth intact.

**Why it matters here:** the paper uses stochastic depth alongside
[[layerscale]] as part of the regularization recipe for training its deepest
[[class-attention-in-image-transformers]] models, complementing LayerScale's
optimization-stability fix rather than substituting for it.

**Lineage:** a general residual-network regularizer, applied here to
transformer-based image classifiers.
