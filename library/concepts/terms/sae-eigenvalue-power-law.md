---
aliases:
- galaxy-scale structure
- SAE feature point cloud power law
- fractal cucumber
tags:
- kg/term
- concept
- term
kg:
  id: term:sae-eigenvalue-power-law
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[clustering-entropy]]'
relationships:
- type: proposed_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: related_to
  target: '[[clustering-entropy]]'
  target_id: metric:clustering-entropy
---

The SAE eigenvalue power law is the finding that the eigenvalue spectrum of the covariance matrix of SAE feature directions decays as a power law rather than the flat Marchenko-Pastur profile expected for isotropic random data. The decay is steepest in middle network layers, and SAE feature directions show a substantially steeper slope than raw model activations at the same layer. The informally named "fractal cucumber" shape refers to the elongated, hierarchically structured geometry of the resulting feature point cloud.

**Why it matters here:** A non-trivial covariance structure in feature space implies that information is not uniformly distributed across directions, motivating targeted steering along high-variance axes rather than random probes when trying to influence epistemic states.

**Lineage:** described in [[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]; companion to [[clustering-entropy]] as a complementary global-structure measure; related to [[middle-layers-steepen-eigenvalue-power-law]].
