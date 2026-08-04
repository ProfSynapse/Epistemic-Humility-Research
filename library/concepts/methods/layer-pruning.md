---
aliases:
- Layer Pruning
- similarity-informed layer pruning
tags:
- kg/method
- concept
- method
kg:
  id: method:layer-pruning
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
- '[[qlora]]'
- '[[angular-distance]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2403.17887--unreasonable-ineffectiveness-deeper-layers]]'
  target_id: paper:2403.17887
  confidence: high
- type: required_by
  target: '[[qlora]]'
  target_id: method:qlora
  confidence: medium
- type: related_to
  target: '[[angular-distance]]'
  target_id: metric:angular-distance
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Layer pruning removes a contiguous block of transformer layers from a
pretrained model and reconnects the remaining layers directly, then applies a
small amount of parameter-efficient finetuning ("healing") to repair the
resulting distribution shift. The block to remove is chosen by an
angular-distance similarity search over layers rather than removed uniformly
or at random: for each candidate block size n, the algorithm picks the start
layer whose input and output hidden states are most similar, on the
assumption that highly-similar blocks contribute the least to the
computation and are safest to drop.

**Why it matters here:** This is the paper's central method. Combined with
[[qlora]] healing, it is used to show that up to roughly half of a model's
layers can be removed with only minimal loss in QA-benchmark accuracy for
some model families, and to expose a divide between smoothly-degrading
autoregressive loss and sharply-transitioning downstream accuracy.

**Lineage:** proposed in arXiv:2403.17887; related in spirit to
[[layer-skipping]] and [[layer-order-permutation]] as depth-manipulation
probes of transformer redundancy, but distinguished by its similarity-guided
block selection and post-hoc healing step.
