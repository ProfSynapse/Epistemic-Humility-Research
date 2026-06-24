---
aliases:
- polysemantic neuron
- polysemantic neurons
- feature superposition
tags:
- kg/term
- concept
- term
kg:
  id: term:polysemanticity
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[superposition-hypothesis]]'
- '[[sparse-autoencoder]]'
- '[[monosemanticity]]'
relationships:
- type: required_by
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
---

Polysemanticity is the property of a single model component (neuron, attention head, or direction) responding to multiple unrelated semantic concepts simultaneously. It arises because models represent more features than they have dimensions via superposition, forcing concepts to share neural real estate. Polysemanticity makes circuit nodes difficult to interpret and complicates causal interventions, since ablating one "neuron" disturbs multiple independent features at once.

**Why it matters here:** Polysemanticity is a direct obstacle to mechanistic accounts of epistemic humility: if the "I don't know" direction is entangled with unrelated features in a polysemantic neuron, targeted steering or ablation will have unpredictable side effects on unrelated capabilities.

**Lineage:** a necessary consequence of the [[superposition-hypothesis]]; [[sparse-autoencoder]] methods decompose polysemantic neurons into monosemantic directions; [[monosemanticity]] is the desirable counterpart.
