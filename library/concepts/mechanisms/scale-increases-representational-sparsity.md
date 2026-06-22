---
aliases:
- Model scale increases representational sparsity on average
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:scale-increases-representational-sparsity
  type: mechanism
  status: canonical
cause: Increasing LLM parameter count (model scale) from 70M to 6.9B
effect: 'Average representational sparsity increases (features can be decoded by fewer neurons), but with heterogeneous dynamics: programming language and factual features become sparser while plain-text features may not; neuron splitting causes some features to require more neurons at larger scale'
polarity: increases
related:
- '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
- '[[representational-sparsity]]'
- '[[pythia-suite]]'
- '[[sparse-probing]]'
relationships:
- type: supported_by
  target: '[[2305.01610--finding-neurons-haystack-sparse-probing]]'
  target_id: paper:2305.01610
  confidence: high
- type: related_to
  target: '[[representational-sparsity]]'
  target_id: metric:representational-sparsity
- type: related_to
  target: '[[pythia-suite]]'
  target_id: model:pythia-suite
- type: related_to
  target: '[[sparse-probing]]'
  target_id: method:sparse-probing
---

Probing the [[pythia-suite]] from 70M to 6.9B parameters with sparse linear classifiers reveals that average [[representational-sparsity]] -- the minimum number of neurons needed to decode a feature above threshold -- increases with scale, meaning larger models pack features into fewer neurons on average (arXiv:2305.01610). However, the effect is heterogeneous: programming language and factual features become markedly sparser at scale, while plain-text and syntactic features show flatter or even reversed trends; some features undergo neuron splitting across scale, requiring more neurons at larger model sizes before reconcentrating. This heterogeneity cautions against treating scale effects on representation as uniform across feature types.
