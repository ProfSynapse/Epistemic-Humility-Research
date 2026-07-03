---
aliases:
- negentropy
- SAE clustering entropy
- k-NN entropy deficit
- Clustering Entropy (Negentropy)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:clustering-entropy
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[sae-eigenvalue-power-law]]'
relationships:
- type: related_to
  target: '[[sae-eigenvalue-power-law]]'
  target_id: term:sae-eigenvalue-power-law
---

Clustering entropy (negentropy) measures the degree to which an SAE feature point cloud departs from a multivariate Gaussian with the same covariance matrix: a higher value means the distribution is more structured or clustered than an isotropic baseline. It is estimated using the k-nearest-neighbor method on the set of unit-normalized feature directions. A Gaussian reference point cloud of the same dimension and covariance has negentropy zero by definition, so the metric quantifies excess structure.

**Why it matters here:** As a geometry-agnostic index of distributional structure in representation space, clustering entropy offers a single-number summary of how non-randomly organized a model's internal feature set is, which is relevant when assessing whether epistemic-state directions form coherent clusters or are scattered uniformly.

**Lineage:** companion measure to [[sae-eigenvalue-power-law]]; both characterize global point-cloud geometry of SAE features from [[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]].
