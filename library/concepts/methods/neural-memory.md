---
aliases:
- key-value memory network
- memory network
- Sukhbaatar memory
- Neural Memory (End-to-End Memory Networks)
tags:
- kg/method
- concept
- method
kg:
  id: method:neural-memory
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[ffn-as-key-value-memory]]'
- '[[transformer-feed-forward-layer]]'
relationships:
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
---

A neural architecture that explicitly stores d_m key-value pairs: a query vector is compared to all keys (typically via inner product followed by softmax), producing a coefficient vector, and the output is the weighted sum of corresponding value vectors. Proposed by Sukhbaatar et al. (2015) in the End-to-End Memory Networks framework as an approach to multi-hop reasoning over external memory. The structural equivalence between this architecture and the transformer feed-forward sublayer (first weight matrix as keys, second as values) is the central observation of Geva et al. (2020).

**Why it matters here:** Framing FFN layers as key-value memories makes it natural to ask which keys encode factual associations, enabling targeted interventions for correcting hallucinations or eliciting abstention.

**Lineage:** precursor to [[transformer-feed-forward-layer]]'s key-value reinterpretation; the equivalence argument is developed in [[ffn-as-key-value-memory]].
