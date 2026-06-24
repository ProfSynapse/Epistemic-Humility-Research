---
aliases:
- Superposition causes polysemanticity in neurons
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:superposition-causes-polysemanticity
  type: mechanism
  status: canonical
cause: Neural networks representing more features than dimensions (superposition) by storing features as non-orthogonal directions
effect: Individual neurons activate for multiple unrelated semantic contexts (polysemanticity), obscuring their interpretability
polarity: enables
related:
- '[[2309.08600--sparse-autoencoders-interpretable-features]]'
- '[[superposition-hypothesis]]'
- '[[polysemanticity]]'
- '[[monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[tc2022--toy-models-of-superposition]]'
relationships:
- type: supported_by
  target: '[[2309.08600--sparse-autoencoders-interpretable-features]]'
  target_id: paper:2309.08600
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: supported_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
---

When a neural network must represent more features than it has dimensions, the [[superposition-hypothesis]] predicts that it will pack features as non-orthogonal directions in activation space, causing any given neuron (basis direction) to be the sum of contributions from multiple features (arXiv:2309.08600). This geometric packing directly produces [[polysemanticity]]: the same neuron achieves high activation for semantically unrelated inputs that happen to share contributions from their respective superimposed feature directions. Sparse autoencoders recover the underlying monosemantic features by finding a higher-dimensional sparse basis that disentangles the superposition.
