---
aliases:
- Top-k SAE
- k-sparse autoencoder
- Top-k Sparse Autoencoder
tags:
- kg/method
- concept
- method
kg:
  id: method:top-k-sparse-autoencoder
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-autoencoder]]'
- '[[off-support-l1-regularizer]]'
- '[[l1-l2-ratio-regularizer]]'
relationships:
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

A Top-k Sparse Autoencoder enforces sparsity architecturally: for each input, the encoder retains only the k latent units with the largest pre-activation values and zeros all others, imposing a hard per-sample sparsity budget. Unlike L1-penalized SAEs, the Top-k constraint does not shrink the magnitude of selected activations, preserving the scale of the latent representation while controlling code density. The reconstruction objective trains only over the selected units, leaving off-support units without a direct gradient signal and creating an unconstrained region that auxiliary regularizers can exploit.

**Why it matters here:** controlled per-sample sparsity in learned feature dictionaries is a prerequisite for monosemantic, human-interpretable representations; Top-k SAEs are the architectural foundation on which [[off-support-l1-regularizer]] and [[l1-l2-ratio-regularizer]] are built.

**Lineage:** extends [[sparse-autoencoder]]; [[off-support-l1-regularizer]] and [[l1-l2-ratio-regularizer]] are auxiliary regularizers designed for this architecture's unconstrained off-support region.
