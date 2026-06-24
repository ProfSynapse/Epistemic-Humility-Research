---
aliases:
- iterative refinement of predictions
- layer-as-incremental-update
- Iterative Inference (transformers)
tags:
- kg/term
- concept
- term
kg:
  id: term:iterative-inference
  type: term
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

Iterative inference is a theoretical framing of transformer forward passes as a
sequence of incremental updates to a latent prediction of the next token: each
layer refines a probability distribution over the vocabulary, advancing the
representation step by step toward the final output at the last layer. Under
this framing the residual stream carries an evolving "guess" that the model
progressively sharpens rather than building a representation from scratch at the
end.

**Why it matters here:** If predictions are formed iteratively, intermediate
layers already encode partial confidence about an answer, which means
calibration and known-unknown signals may be readable well before the final
layer. This motivates lens-based probing of early layers for epistemic state.

**Lineage:** the framing motivates tools such as [[logit-lens]] and
[[tuned-lens]], which make the intermediate predictions explicit by projecting
hidden states to vocabulary space at each layer.
