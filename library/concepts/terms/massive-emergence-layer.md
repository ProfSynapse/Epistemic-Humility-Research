---
aliases:
- ME Layer
- Massive Emergence Layer
tags:
- kg/term
- concept
- term
kg:
  id: term:massive-emergence-layer
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
- '[[massive-activations]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2605.08504--single-layer-explain-them-all-understanding-massive]]'
  target_id: paper:2605.08504
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

The Massive Emergence Layer (ME Layer) is the single layer, consistent across
model families and sizes, at which massive activations first appear in the
first token's hidden state and are subsequently propagated to deeper layers
through the residual stream. Within this layer both the RMSNorm and FFN
parameters jointly amplify the first token's representation by hundreds of
times; once formed, the resulting activation direction stays largely invariant
across all later layers.

**Why it matters here:** the ME Layer gives a single, localized intervention
point for massive-activation phenomena rather than treating them as diffuse
across the network, which is what motivates weight-guided masking as a
targeted mitigation.

**Lineage:** introduced by
[[2605.08504--single-layer-explain-them-all-understanding-massive]]; the
locus at which [[massive-activations]] emerge within the [[residual-stream]].
