---
aliases:
- k-sparse linear probing
- k-sparse probe
- sparse linear classifier
tags:
- kg/method
- concept
- method
kg:
  id: method:sparse-probing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
- '[[superposition-hypothesis]]'
- '[[neuron-ablation]]'
relationships:
- type: proposed_by
  target: '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
  target_id: paper:2305.01610
  confidence: high
- type: variation_of
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[neuron-ablation]]'
  target_id: method:neuron-ablation
---

Sparse probing trains k-sparse linear classifiers (with at most k non-zero weights) on LLM neuron activations to predict the presence of human-interpretable features. By sweeping k from large down to 1, the method localizes the individual neurons most relevant to a feature and quantifies how sparsely that feature is represented across the network. At k=1, a single neuron is identified as the top feature detector, giving a direct neuron-to-concept attribution.

**Why it matters here:** Sparse probing provides a principled way to ask whether a model has localized representations of concepts such as "I don't know," which is foundational for understanding how epistemic states are encoded and whether targeted interventions on those neurons can shift abstention behavior.

**Lineage:** operationalizes the [[superposition-hypothesis]] by measuring the sparsity of feature representations; pairs naturally with [[neuron-ablation]] to move from correlation to causal claim.
