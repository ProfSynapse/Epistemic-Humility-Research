---
aliases:
- Regularizer 1
- off-support L1 penalty
- pre-selection L1 regularizer
- Off-Support L1 Regularizer (Top-k SAE)
tags:
- kg/method
- concept
- method
kg:
  id: method:off-support-l1-regularizer
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
- '[[top-k-sparse-autoencoder]]'
- '[[l1-l2-ratio-regularizer]]'
- '[[monosemanticity-score]]'
relationships:
- type: proposed_by
  target: '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
  target_id: paper:2606.27321
  confidence: high
- type: variation_of
  target: '[[top-k-sparse-autoencoder]]'
  target_id: method:top-k-sparse-autoencoder
---

The off-support L1 regularizer adds an L1 penalty to the pre-activation values of latent units that are not selected by the Top-k operator for a given input (off-support units), restricted to batch-active units. Because standard Top-k SAE training provides no reconstruction-loss gradient to off-support activations, their pre-activation magnitudes are otherwise unconstrained; the penalty drives sub-threshold responses toward zero, sharpening each unit's selectivity. Restricting the penalty to batch-active units avoids wasting capacity on permanently dead latents.

**Why it matters here:** sharper unit selectivity maps directly to higher [[monosemanticity-score]], a condition under which individual latent features correspond to interpretable concepts rather than superpositions, supporting auditable mechanistic explanations of model behavior.

**Lineage:** augments [[top-k-sparse-autoencoder]] by constraining its off-support region; introduced in [[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]] alongside [[l1-l2-ratio-regularizer]].
