---
aliases:
- nonlinear SAE error
- nonlinear reconstruction error
- dense activation component
tags:
- kg/term
- concept
- term
kg:
  id: term:nonlinear-sae-error
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
- '[[sae-dark-matter]]'
- '[[sparse-autoencoder]]'
relationships:
- type: proposed_by
  target: '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
  target_id: paper:2410.14670
  confidence: high
- type: related_to
  target: '[[sae-dark-matter]]'
  target_id: term:sae-dark-matter
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: high
---

Nonlinear SAE error is the part of the sparse-autoencoder reconstruction error
that remains after removing the component linearly predictable from the input
activation. Engels et al. show it is qualitatively different from the linear
part: it fails the linear-norm-predictability test, so it is not a sparse sum of
near-orthogonal linear features; SAEs trained directly on it converge to a
worse fraction of variance unexplained (roughly 0.59 versus 0.54); and it stays
approximately constant as SAE width grows at fixed sparsity, unlike the
linearly predictable and absent-feature parts, which shrink with scale. It
behaves like a denser residual component rather than a low-dimensional linear
subspace.

**Why it matters here:** in the displacement census this is the residual we
cannot linearly explain away. A dense component that is not linearly predictable
from the input, does not shrink with SAE width, and lacks a low-dimensional
subspace signature is consistent with nonlinear SAE error and should be treated
as a nuisance floor, not a new steerable direction.

**Lineage:** the residual of [[sae-dark-matter]] after its linearly predictable
part is subtracted; contrasts with the [[linear-representation-hypothesis]]
picture that treats activations as sparse sums of linear features.
