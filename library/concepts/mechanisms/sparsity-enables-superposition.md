---
aliases:
- Feature Sparsity Enables Superposition
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sparsity-enables-superposition
  type: mechanism
  status: canonical
cause: High sparsity of input features -- features that are rarely active simultaneously
effect: Neural networks represent more features than hidden dimensions by storing them as nearly-orthogonal overlapping directions, accepting bounded interference costs
polarity: enables
related:
- '[[tc2022--toy-models-of-superposition]]'
- '[[superposition-hypothesis]]'
- '[[sparse-autoencoder]]'
relationships:
- type: supported_by
  target: '[[tc2022--toy-models-of-superposition]]'
  target_id: paper:tc2022
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
---

When features are sparse -- rarely co-active -- the expected interference between overlapping representations is low, making it beneficial for a neural network to pack more features into fewer dimensions than a strict orthogonal basis would allow. Elhage et al. (tc2022) demonstrate this in toy models: networks with sparse features develop superposition, whereas networks with dense features do not. The degree of superposition scales with sparsity, providing a theoretical account of why polysemanticity is pervasive in models trained on natural language.
