---
aliases:
- fraction of variance unexplained
- FVU
- unexplained variance
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:fraction-of-variance-unexplained
  type: metric
  status: canonical
area: metrics
related:
- '[[2410.14670--decomposing-dark-matter-sparse-autoencoders]]'
- '[[sae-dark-matter]]'
- '[[sparse-autoencoder]]'
relationships:
- type: related_to
  target: '[[sae-dark-matter]]'
  target_id: term:sae-dark-matter
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: medium
---

Fraction of variance unexplained (FVU) is one minus the coefficient of
determination, the share of activation variance a reconstruction fails to
capture. It is the primary reconstruction-quality metric for sparse
autoencoders and the quantity whose residual defines SAE dark matter. Engels et
al. further split FVU into an absent-features term, a linear-error term, and a
nonlinear-error term, and define FVU_nonlinear as the variance unexplained by
the sum of the SAE output and an optimal linear projection of the input.

**Why it matters here:** FVU (and its participation-ratio or effective-dimension
cousins) is the natural yardstick for reporting how much of the out-of-span
generation-time displacement is captured by a candidate low-dimensional model
versus left as a dense floor.

**Lineage:** defines the residual named by [[sae-dark-matter]]; measured against
[[sparse-autoencoder]] reconstructions.
