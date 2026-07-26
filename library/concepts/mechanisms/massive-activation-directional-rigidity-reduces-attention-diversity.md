---
aliases:
- massive-activation directional rigidity reduces attention diversity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:massive-activation-directional-rigidity-reduces-attention-diversity
  type: mechanism
  status: canonical
cause: "once formed at the ME Layer, the massive-activation token's hidden-state direction stays stable across subsequent layers and is near-identical across different input instances."
effect: "the diversity of hidden representations passed to the attention module is reduced, because the same near-invariant direction is presented regardless of input."
polarity: decreases
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[massive-emergence-layer]]'
- '[[massive-activations]]'
- '[[attention-sink]]'
relationships:
- type: supported_by
  target: '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
  target_id: paper:2605.08504
  confidence: high
- type: related_to
  target: '[[massive-emergence-layer]]'
  target_id: term:massive-emergence-layer
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: medium
---

Shi et al. show that once a massive activation forms at the ME Layer, the
token's hidden-state direction becomes rigid: it is stable across all later
layers and nearly identical across different input instances. Because
attention reads this near-invariant direction regardless of the actual input,
the diversity of hidden representations reaching the attention module is
reduced, motivating weight-guided masking as a way to relax the rigidity.

**Lineage:** established by
[[2605.08504--single-layer-explain-them-all-understanding-massive]]; a
consequence of [[massive-activations]] formed at the
[[massive-emergence-layer]], and connected to [[attention-sink]] formation in
the following layer.
