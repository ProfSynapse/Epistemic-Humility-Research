---
aliases:
- Distractor Projection Reveals SAE Crystals
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:distractor-projection-reveals-crystals
  type: mechanism
  status: canonical
cause: "Linear discriminant analysis that projects out semantically irrelevant [[distractor-features]] directions (e.g., word length) from the [[sparse-autoencoder]] activation space"
effect: "Parallelogram and trapezoid quality of SAE crystal structures improves dramatically, revealing relational semantic geometry that was previously hidden by distractor variance"
polarity: enables
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[sparse-autoencoder]]'
- '[[sae-crystal-structure]]'
- '[[distractor-features]]'
relationships:
- type: supported_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[sae-crystal-structure]]'
  target_id: term:sae-crystal-structure
- type: related_to
  target: '[[distractor-features]]'
  target_id: term:distractor-features
---

SAE feature clouds contain directions driven by superficial token properties (e.g., word length or position) that inflate variance along axes irrelevant to the semantic content of interest. When these distractor directions are removed via linear discriminant projection, the residual feature cloud reveals parallelogram and trapezoid crystals whose geometric quality (measured by parallelism and congruence scores) improves markedly (arXiv:2410.19750). This demonstrates that relational semantic geometry is present in the SAE feature space all along but is masked by competing distractor variance unless explicitly removed.
