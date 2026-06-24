---
aliases:
- monosemantic neuron
- monosemantic neurons
- context neurons
tags:
- kg/term
- concept
- term
kg:
  id: term:monosemanticity
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[polysemanticity]]'
- '[[superposition-hypothesis]]'
- '[[sparse-autoencoder]]'
relationships:
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

Monosemanticity is the property of a neuron that responds selectively to a single, well-defined semantic feature. Context neurons in the middle layers of LLMs, which activate for high-level sequence-level properties such as natural language or programming language, are canonical examples. A neuron earns its own dedicated dimension (rather than sharing via superposition) when its feature is sufficiently important or frequent that the model cannot afford cross-feature interference.

**Why it matters here:** Monosemantic neurons are the cleanest targets for mechanistic interpretability studies of epistemic states: a neuron that tracks "model uncertainty" or "known vs. unknown" without cross-feature contamination enables reliable causal ablations and probing experiments relevant to abstention research.

**Lineage:** the desirable counterpart to [[polysemanticity]]; the [[superposition-hypothesis]] predicts monosemanticity is reserved for high-importance features; [[sparse-autoencoder]] methods recover approximately monosemantic directions from polysemantic activation space.
