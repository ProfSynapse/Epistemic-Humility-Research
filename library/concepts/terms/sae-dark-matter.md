---
aliases:
- SAE dark matter
- dark matter of sparse autoencoders
- SAE reconstruction error structure
tags:
- kg/term
- concept
- term
kg:
  id: term:sae-dark-matter
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
- '[[sparse-autoencoder]]'
- '[[linear-representation-hypothesis]]'
- '[[nonlinear-sae-error]]'
- '[[fraction-of-variance-unexplained]]'
relationships:
- type: proposed_by
  target: '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
  target_id: paper:2410.14670
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: high
- type: related_to
  target: '[[nonlinear-sae-error]]'
  target_id: term:nonlinear-sae-error
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: medium
---

SAE dark matter is the unexplained variance in a model activation that a sparse
autoencoder fails to reconstruct: the residual error vector left after the SAE's
sparse linear features are subtracted, and specifically the below-asymptote
component of the SAE width-versus-MSE power law that scaling does not remove.
Engels et al. find that about half of this error vector and more than 90% of its
norm are linearly predictable from the initial activation, so the error is
structured rather than pure noise; the decomposition splits it into absent
features, a linearly predictable component, and a denser [[nonlinear-sae-error]]
component that is not a sparse sum of linear features.

**Why it matters here:** our generation-time displacement census finds ~99% of
hidden-state movement outside the span of all named epistemic axes. SAE dark
matter is the leading candidate identity for the linearly predictable part of
that remainder: if the out-of-span displacement is largely recoverable by a
linear map from the input activation, it is bookkeeping the named-axis basis
simply does not cover, not a new interpretable knob.

**Lineage:** names the residual of [[sparse-autoencoder]] reconstruction;
decomposes into [[nonlinear-sae-error]] plus a linearly predictable part;
measured with [[fraction-of-variance-unexplained]]; builds on the
[[linear-representation-hypothesis]] to model what the linear part is.
