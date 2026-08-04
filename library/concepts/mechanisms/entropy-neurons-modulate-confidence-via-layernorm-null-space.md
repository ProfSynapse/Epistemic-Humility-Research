---
aliases:
- Entropy Neurons Modulate Confidence Via LayerNorm Null Space
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entropy-neurons-modulate-confidence-via-layernorm-null-space
  type: mechanism
  status: canonical
cause: An entropy neuron writes its output weights almost exclusively into the unembedding matrix's effective null space, increasing residual-stream norm with minimal direct effect on any logit
effect: The final LayerNorm's scale factor shrinks in response, uniformly flattening (or sharpening) the output distribution and changing its entropy while leaving the ranking of logits largely intact
polarity: mediates
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[entropy-neurons]]'
- '[[unembedding-null-space]]'
- '[[layer-normalization]]'
relationships:
- type: supported_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[entropy-neurons]]'
  target_id: term:entropy-neurons
  confidence: high
- type: related_to
  target: '[[unembedding-null-space]]'
  target_id: term:unembedding-null-space
  confidence: high
- type: related_to
  target: '[[layer-normalization]]'
  target_id: term:layer-normalization
  confidence: high
---

Stolfo et al. use causal mediation analysis to show that entropy neurons'
effect on loss and output entropy is mediated by the final LayerNorm rather
than by directly shifting logits: their total effect greatly exceeds their
LayerNorm-held-constant direct effect, while random neurons show no such gap.
The null-space write is the geometric mechanism that lets a neuron change
residual-stream norm (and so the LayerNorm scale) almost independently of the
logits themselves.
