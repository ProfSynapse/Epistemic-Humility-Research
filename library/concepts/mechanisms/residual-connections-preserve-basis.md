---
aliases:
- Residual Connections Preserve Embedding Basis Across Layers
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:residual-connections-preserve-basis
  type: mechanism
  status: canonical
cause: Residual (skip) connections combined with weight decay during transformer training
effect: The model maintains a consistent vector-space basis across all layers, making intermediate activations interpretable when projected back to vocabulary space via the [[unembedding-matrix]]
polarity: enables
related:
- '[[ll2020--interpreting-gpt-the-logit-lens]]'
- '[[residual-stream]]'
- '[[unembedding-matrix]]'
- '[[logit-lens]]'
relationships:
- type: supported_by
  target: '[[ll2020--interpreting-gpt-the-logit-lens]]'
  target_id: paper:ll2020
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[unembedding-matrix]]'
  target_id: term:unembedding-matrix
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
---

Nostalgebraist (ll2020) observes that residual connections force each layer's output to remain in the same vector space as the token embeddings, because each layer adds to (rather than replaces) the residual stream. Combined with weight decay, this ensures the embedding and unembedding matrices remain the de-facto coordinate system throughout the network. As a direct consequence, the logit lens -- projecting intermediate residual states through the unembedding matrix -- yields interpretable token probability distributions at every layer.
