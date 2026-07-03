---
aliases:
- crystal
- SAE crystals
- parallelogram structure
- trapezoid structure
tags:
- kg/term
- concept
- term
kg:
  id: term:sae-crystal-structure
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[linear-representation-hypothesis]]'
relationships:
- type: proposed_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: derived_from
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

Geometric structures in the SAE feature point cloud where groups of four feature vectors form approximate parallelograms or trapezoids, reflecting semantic relational structure analogous to classic word-vector analogies (man is to woman as king is to queen). Parallelograms indicate two independent semantic transformations acting in orthogonal directions; trapezoids indicate one shared transformation. The term was coined for the recurrent shapes found after projecting out [[distractor-features]] from the full feature space.

**Why it matters here:** Crystal structures imply that semantic relationships between concepts are geometrically organized, meaning uncertainty-related features may form relational lattices rather than isolated directions, with implications for how probing or steering should target epistemic-humility signals.

**Lineage:** derives from [[linear-representation-hypothesis]], which predicts that concepts occupy linear subspaces; crystal structures are an empirical confirmation of that prediction at the level of individual SAE features.
