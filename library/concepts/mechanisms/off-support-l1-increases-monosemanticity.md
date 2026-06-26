---
aliases:
- Off-support L1 penalty sharpens latent selectivity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:off-support-l1-increases-monosemanticity
  type: mechanism
  status: canonical
cause: Applying an L1 penalty to the pre-selection activations of units not chosen by the Top-k operator (off-support units) in a Top-k SAE
effect: Increased monosemanticity scores and class purity of learned latent features, with no cost to reconstruction quality
polarity: increases
related:
- '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
- '[[top-k-sparse-autoencoder]]'
- '[[off-support-l1-regularizer]]'
- '[[monosemanticity-score]]'
- '[[monosemanticity]]'
relationships:
- type: supported_by
  target: '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
  target_id: paper:2606.27321
  confidence: high
- type: related_to
  target: '[[top-k-sparse-autoencoder]]'
  target_id: method:top-k-sparse-autoencoder
- type: related_to
  target: '[[off-support-l1-regularizer]]'
  target_id: method:off-support-l1-regularizer
- type: related_to
  target: '[[monosemanticity-score]]'
  target_id: metric:monosemanticity-score
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
---

In a [[top-k-sparse-autoencoder]], the Top-k gate already forces exactly k units to fire, but the remaining off-support activations can still carry large residual magnitudes that introduce ambiguity about which concepts each unit represents. Adding an [[off-support-l1-regularizer]] to those non-selected activations pressures the encoder to produce sharper separation between active and inactive units, raising [[monosemanticity-score]] and class purity without degrading reconstruction (arXiv:2606.27321). The improvement isolates to the off-support entries: penalizing on-support activations instead yields no benefit, confirming that the mechanism is specifically about sharpening the inactive tail rather than rescaling active features.
