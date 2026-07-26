---
aliases:
- RMSNorm and FFN jointly drive massive-activation emergence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rmsnorm-ffn-jointly-drive-massive-activation-emergence
  type: mechanism
  status: canonical
cause: "at a single, model-consistent Massive Emergence (ME) Layer, the RMSNorm and FFN parameters act jointly on the first token's hidden state."
effect: "the first token's hidden state is amplified by hundreds of times, producing a massive activation that then propagates unchanged through the residual stream to all deeper layers."
polarity: enables
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[massive-emergence-layer]]'
- '[[massive-activations]]'
- '[[residual-stream]]'
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
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Shi et al. localize massive-activation emergence to a single layer per model,
the ME Layer, and show that neither RMSNorm nor the FFN alone explains the
amplification: it is their joint action within that one layer that inflates
the first token's hidden state by hundreds of times. This single-layer origin
holds consistently across model families and sizes, and once the massive
activation is formed it is passed forward largely unchanged through the
residual stream.

**Lineage:** established by
[[2605.08504--single-layer-explain-them-all-understanding-massive]]; localizes
where [[massive-activations]] originate within the [[residual-stream]], at the
[[massive-emergence-layer]].
