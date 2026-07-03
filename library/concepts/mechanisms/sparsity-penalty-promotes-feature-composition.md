---
aliases:
- Sparsity Penalty Promotes Feature Composition over Atomicity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sparsity-penalty-promotes-feature-composition
  type: mechanism
  status: canonical
cause: "L0/L1 sparsity penalty in [[sparse-autoencoder]] training combined with increased dictionary size"
effect: "Larger SAE latents encode compositions of multiple smaller-SAE features rather than novel atomic properties, as revealed by meta-SAE decompositions"
polarity: enables
related:
- '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
- '[[sparse-autoencoder]]'
- '[[feature-splitting]]'
- '[[monosemanticity]]'
relationships:
- type: supported_by
  target: '[[2502.04878--sparse-autoencoders-do-not-find-canonical-units]]'
  target_id: paper:2502.04878
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
---

The sparsity objective in SAE training rewards representing activations with as few latent features as possible, which encourages the dictionary to retain compositional features that fire across multiple related contexts rather than discovering finer-grained atomic units. Meta-SAE analysis (arXiv:2502.04878) shows that when a small-dictionary SAE's features are decomposed by a larger-dictionary SAE, many large-SAE latents correspond directly to linear combinations of small-SAE latents rather than to genuinely novel atomic properties. This implies that the [[canonical-units-of-analysis]] expected from sparsity training are confounded by the incentive to compose rather than decompose.
