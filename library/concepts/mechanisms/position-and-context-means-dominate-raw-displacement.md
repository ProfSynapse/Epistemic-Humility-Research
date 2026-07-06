---
aliases:
- global mean plus positional and context means explain most raw hidden-state variation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:position-and-context-means-dominate-raw-displacement
  type: mechanism
  status: canonical
cause: "decomposing hidden states into global mean, positional mean, context mean, and residual."
effect: "a large low-rank positional spiral, a topic-clustered context offset, and a dominant global mean absorb most raw variation, leaving a small residual as the candidate signal."
polarity: enables
related:
- '[[2310.04861--uncovering-hidden-geometry-transformers-disentangling-position-context]]'
- '[[position-context-decomposition]]'
relationships:
- type: supported_by
  target: '[[2310.04861--uncovering-hidden-geometry-transformers-disentangling-position-context]]'
  target_id: paper:2310.04861
  confidence: high
- type: related_to
  target: '[[position-context-decomposition]]'
  target_id: method:position-context-decomposition
  confidence: high
---

Song and Zhong show that the positional basis is low-rank (estimated rank 8 to
12) and low-frequency, tracing a spiral, that the context basis clusters by
topic, and that the two are nearly orthogonal, so a large fraction of raw hidden-
state displacement is boring structural bookkeeping that must be subtracted
before the residual can be treated as candidate signal.
