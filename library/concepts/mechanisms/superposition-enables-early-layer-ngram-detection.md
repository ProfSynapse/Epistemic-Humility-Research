---
aliases:
- Superposition enables early-layer n-gram detection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:superposition-enables-early-layer-ngram-detection
  type: mechanism
  status: canonical
cause: Early LLM layers representing many n-gram (compound word) features via sparse combinations of polysemantic neurons in superposition
effect: Individual neurons appear monosemantic on a narrow probe dataset but are revealed to be polysemantic across a large corpus; large input weight norms and negative biases serve as a mechanistic fingerprint of this superposition
polarity: enables
related:
- '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
- '[[superposition-hypothesis]]'
- '[[polysemanticity]]'
- '[[sparse-probing]]'
relationships:
- type: supported_by
  target: '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
  target_id: paper:2305.01610
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: related_to
  target: '[[sparse-probing]]'
  target_id: method:sparse-probing
---

Sparse probing experiments on Pythia models reveal that early layers represent large numbers of n-gram features via [[superposition-hypothesis]]: many compound-word and token-sequence features are jointly encoded by overlapping combinations of neurons rather than each feature occupying a dedicated neuron (arXiv:2305.01610). A neuron that appears monosemantic on a curated narrow probe set is often revealed to be polysemantic when probed across a large diverse corpus, with a mechanistic fingerprint of large input weight norms and strongly negative biases identifying superposition-implicated neurons. This mechanism allows the model to detect far more lexical patterns in early layers than its neuron count would permit under a one-feature-per-neuron encoding.
