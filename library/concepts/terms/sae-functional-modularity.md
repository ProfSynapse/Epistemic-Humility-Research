---
aliases:
- brain-scale structure
- SAE lobes
- meso-scale modular structure
- feature lobes
tags:
- kg/term
- concept
- term
kg:
  id: term:sae-functional-modularity
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[sae-crystal-structure]]'
relationships:
- type: proposed_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: related_to
  target: '[[sae-crystal-structure]]'
  target_id: term:sae-crystal-structure
---

SAE functional modularity is the empirical finding that SAE features sharing functional similarity (measured by co-occurrence within documents) also cluster spatially in the SAE feature point cloud, forming distinct regions called "lobes" analogous to functional regions in biological brains. For Gemma-2-2b Layer 12, code and math features form a lobe that is geometrically separable from language features. This meso-scale structure sits between individual feature geometry ([[sae-crystal-structure]]) and the global eigenvalue spectrum.

**Why it matters here:** Functional lobes suggest that internal representations are organized into interpretable, purpose-segregated zones, which bears on whether a model's epistemic-state features (such as doubt or known-unknown discrimination) might occupy a localized, steerable subregion rather than being diffusely distributed.

**Lineage:** related to [[sae-crystal-structure]]; described in [[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]].
