---
aliases:
- Middle LLM Layers Produce Steeper Eigenvalue Power Law in SAE Features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:middle-layers-steepen-eigenvalue-power-law
  type: mechanism
  status: canonical
cause: "Processing in the middle transformer layers of an LLM (e.g., layer 12 of Gemma-2-2b) producing more concentrated residual-stream representations"
effect: "Steeper power-law decay in the eigenvalue spectrum of the [[sparse-autoencoder]] feature covariance matrix, indicating more structured and concentrated feature representations"
polarity: increases
related:
- '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
- '[[sparse-autoencoder]]'
- '[[sae-eigenvalue-power-law]]'
relationships:
- type: supported_by
  target: '[[2410.19750--geometry-concepts-sparse-autoencoder-feature-structure]]'
  target_id: paper:2410.19750
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[sae-eigenvalue-power-law]]'
  target_id: term:sae-eigenvalue-power-law
---

When SAEs are fit at different depths of an LLM, the eigenvalue spectrum of the resulting feature covariance matrix varies systematically across layers. Middle layers produce a steeper power-law decay, indicating that a smaller number of dominant directions account for a larger fraction of total feature variance (arXiv:2410.19750). This layer-dependent geometry suggests that intermediate representations are more structured and semantically concentrated than early or late layers, consistent with the view that middle layers perform the bulk of semantic transformation.
