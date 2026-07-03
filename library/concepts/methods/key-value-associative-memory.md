---
aliases:
- KV memory
- associative memory circuit
- transformer associative memory
- Key-Value Associative Memory (Transformer)
tags:
- kg/method
- concept
- method
kg:
  id: method:key-value-associative-memory
  type: method
  status: canonical
area: methods
related:
- '[[truth-direction]]'
- '[[two-phase-memorization-encoding]]'
- '[[ffn-as-key-value-memory]]'
- '[[transformer-feed-forward-layer]]'
relationships:
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
- type: related_to
  target: '[[two-phase-memorization-encoding]]'
  target_id: term:two-phase-memorization-encoding
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
---

The key-value associative memory view treats transformer feed-forward and attention layers as content-addressable stores: the first linear projection acts as a pattern-matching key that detects a semantic context (for example, "capital of France"), and the second linear projection retrieves the associated output embedding (for example, the token distribution peaked at "Paris"). This framing, formalized by Geva et al. (2021), makes factual recall a retrieval problem localized to specific layers, with mid-to-upper feed-forward layers concentrating the highest recall signal. Subject enrichment across early attention heads fills in the key before mid-layer MLPs emit the value.

**Why it matters here:** The KV-memory framing predicts that subject enrichment and attribute extraction are mechanistically distinct stages, informing where epistemic humility interventions (probing, steering, surgery) are most likely to succeed or fail along the residual stream.

**Lineage:** prerequisite for understanding [[two-phase-memorization-encoding]] and for interpreting [[truth-direction]] as stored in specific layer-value subspaces; formalized in [[ffn-as-key-value-memory]] and realized through [[transformer-feed-forward-layer]] computations.
