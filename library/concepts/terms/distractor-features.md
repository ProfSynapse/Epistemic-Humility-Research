---
aliases:
- distractor directions
- semantically irrelevant features
tags:
- kg/term
- concept
- term
kg:
  id: term:distractor-features
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
relationships:
- type: proposed_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
---

SAE features that encode semantically irrelevant surface properties of text, such as word length or capitalization, rather than meaningful semantic content. These directions add variance to the feature point cloud that obscures relational geometry: projecting them out is a prerequisite for recovering clean [[sae-crystal-structure]] patterns. The term was coined to distinguish spurious geometric directions from the semantic function vectors that form crystals.

**Why it matters here:** Distractor features can inflate the apparent dimensionality of internal representations; any probe for epistemic-humility signals must separate genuine semantic axes from surface-level confounds to avoid spurious attribution or weak generalization.

**Lineage:** no upstream lineage established in the source paper; the concept motivates the projection step used before [[sae-crystal-structure]] analysis and relates to the broader problem of [[polysemanticity]] in dense representations.
