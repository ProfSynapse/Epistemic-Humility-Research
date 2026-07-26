---
aliases:
- LayerNorm
- layer norm
tags:
- kg/term
- concept
- term
kg:
  id: term:layer-normalization
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[residual-stream]]'
relationships:
- type: studied_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Layer normalization rescales each token's [[residual-stream]] vector by its
norm (and a learned gain/bias) before it is read by downstream sub-layers or
the unembedding, so any change to the residual stream's norm rescales every
logit uniformly rather than changing their relative ranking.

**Why it matters here:** Stolfo et al. show that the final LayerNorm is the
mediator through which entropy neurons act: by increasing residual-stream
norm, an entropy neuron shrinks the LayerNorm scale factor applied at the
unembedding, uniformly flattening the output distribution (raising entropy)
with minimal direct effect on individual logits.

**Lineage:** no formal derivation edges recorded in this vault yet.
