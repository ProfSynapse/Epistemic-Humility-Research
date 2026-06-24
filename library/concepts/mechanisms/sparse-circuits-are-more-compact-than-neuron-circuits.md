---
aliases:
- Sparse feature circuits are more compact than neuron circuits
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sparse-circuits-are-more-compact-than-neuron-circuits
  type: mechanism
  status: canonical
cause: Using SAE features (monosemantic) instead of neurons as the unit of circuit analysis
effect: Majority of model performance on subject-verb agreement explained by fewer than 100 feature nodes versus approximately 1500 neurons for equivalent faithfulness
polarity: decreases
related:
- '[[2403.19647--sparse-feature-circuits]]'
- '[[sparse-feature-circuits]]'
- '[[sparse-autoencoder]]'
- '[[circuit-faithfulness]]'
- '[[attribution-patching]]'
relationships:
- type: supported_by
  target: '[[2403.19647--sparse-feature-circuits]]'
  target_id: paper:2403.19647
  confidence: high
- type: related_to
  target: '[[sparse-feature-circuits]]'
  target_id: method:sparse-feature-circuits
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
- type: related_to
  target: '[[attribution-patching]]'
  target_id: method:attribution-patching
---

Circuit discovery using [[sparse-autoencoder]] features as nodes produces substantially more compact circuits than equivalent neuron-level analysis: on a subject-verb agreement task, the majority of model performance can be explained by fewer than 100 SAE feature nodes, compared to approximately 1500 neurons required to achieve equivalent [[circuit-faithfulness]] (arXiv:2403.19647). The compactness arises because monosemantic features carve the computation at semantically natural joints, whereas polysemantic neurons conflate multiple distinct computational roles that require many nodes to jointly represent. This compactness gain is what makes sparse feature circuits tractable for human inspection and targeted intervention.
