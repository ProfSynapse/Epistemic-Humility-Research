---
aliases:
- FFN
- position-wise feed-forward network
- feed-forward sublayer
- Transformer Feed-Forward Layer
tags:
- kg/term
- concept
- term
kg:
  id: term:transformer-feed-forward-layer
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[ffn-as-key-value-memory]]'
- '[[neural-memory]]'
- '[[residual-stream-refinement]]'
relationships:
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
- type: related_to
  target: '[[neural-memory]]'
  target_id: method:neural-memory
- type: related_to
  target: '[[residual-stream-refinement]]'
  target_id: term:residual-stream-refinement
---

The position-wise two-matrix sublayer in a transformer block, applied independently to each token position with the form FF(x) = f(x * K^T) * V. It constitutes roughly two-thirds of a standard transformer's parameters (approximately 8d^2 per layer versus 4d^2 for self-attention), making it the parameter-dominant component of the architecture. Geva et al. (2020) showed that this sublayer is structurally equivalent to a neural key-value memory, where the first matrix acts as keys and the second as values.

**Why it matters here:** Understanding what information feed-forward layers store and how they update predictions is foundational to locating and editing factual knowledge, a prerequisite for studying over-confidence and abstention at the representational level.

**Lineage:** structurally equivalent to [[neural-memory]] (Sukhbaatar et al. 2015); the key-value interpretation is developed in [[ffn-as-key-value-memory]]; participates in [[residual-stream-refinement]] by updating the residual stream prediction at each layer.
