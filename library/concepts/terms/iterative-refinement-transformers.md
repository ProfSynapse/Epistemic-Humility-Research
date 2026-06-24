---
aliases:
- thinking in predictive space
- progressive guess refinement
- Iterative Refinement in Transformers
tags:
- kg/term
- concept
- term
kg:
  id: term:iterative-refinement-transformers
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[logit-lens]]'
- '[[residual-stream]]'
- '[[input-discarding]]'
- '[[unembedding-matrix]]'
- '[[prediction-depth]]'
relationships:
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[input-discarding]]'
  target_id: term:input-discarding
- type: related_to
  target: '[[unembedding-matrix]]'
  target_id: term:unembedding-matrix
- type: related_to
  target: '[[prediction-depth]]'
  target_id: metric:prediction-depth
---

Iterative refinement in transformers is the view that a transformer's forward
pass can be understood as a sequence of progressive updates to a probability
distribution over the output vocabulary, starting from rough early-layer guesses
and converging to the final output distribution at the last layer. Each
transformer block refines the running prediction rather than performing a
fundamentally different type of computation. The logit lens makes this
refinement trajectory directly observable by decoding intermediate residual-stream
states with the unembedding matrix at every layer.

**Why it matters here:** If the forward pass is best understood as iterative
refinement, then uncertainty signals, factual associations, and abstention
decisions are not localized to a single layer but emerge gradually, which informs
where probing and editing interventions should be targeted and why
[[prediction-depth]] correlates with example difficulty.

**Lineage:** motivated by [[input-discarding]] observations via [[logit-lens]];
made observable by applying [[unembedding-matrix]] to [[residual-stream]] states;
connects to [[prediction-depth]] as a layer-resolved measure of refinement
completeness.
