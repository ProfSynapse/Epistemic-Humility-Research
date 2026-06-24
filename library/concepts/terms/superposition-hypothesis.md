---
aliases:
- superposition
- representational superposition
- feature superposition
- neural superposition
tags:
- kg/term
- concept
- term
kg:
  id: term:superposition-hypothesis
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[polysemanticity]]'
- '[[sparse-autoencoder]]'
- '[[representational-sparsity]]'
relationships:
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[representational-sparsity]]'
  target_id: metric:representational-sparsity
---

The superposition hypothesis holds that neural networks represent more features than they have neurons by encoding multiple features in overlapping, non-orthogonal directions in activation space. A layer of n neurons can respond to m >> n features simultaneously, necessarily causing polysemanticity by the pigeonhole principle. The mechanistic fingerprint of superposition includes large input weight norms and large negative biases, which implement an implicit thresholding operation.

**Why it matters here:** If epistemic states such as self-knowledge or uncertainty are stored in superposition, then single-neuron ablations or probes may fail to capture the full signal, and sparse autoencoders or multi-neuron decomposition methods may be needed to cleanly isolate them.

**Lineage:** predicts [[polysemanticity]] as a downstream consequence; motivates [[sparse-autoencoder]] as the primary tool for recovering monosemantic feature directions; connects to [[representational-sparsity]] as the empirical correlate of the degree of superposition.
