---
aliases:
- L1/L2-ratio concentration enables robustness to inference-time k
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:l1-l2-ratio-enables-k-robustness
  type: mechanism
  status: canonical
cause: Penalizing the L1/L2-norm ratio of activations before Top-k selection, concentrating the code onto fewer effective units
effect: Reconstruction quality becomes more robust to inference-time choices of k that differ from the training value, and discriminative information is front-loaded into fewer leading activations
polarity: enables
related:
- '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
- '[[top-k-sparse-autoencoder]]'
- '[[l1-l2-ratio-regularizer]]'
- '[[monosemanticity-score]]'
relationships:
- type: supported_by
  target: '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
  target_id: paper:2606.27321
  confidence: high
- type: related_to
  target: '[[top-k-sparse-autoencoder]]'
  target_id: method:top-k-sparse-autoencoder
- type: related_to
  target: '[[l1-l2-ratio-regularizer]]'
  target_id: method:l1-l2-ratio-regularizer
- type: related_to
  target: '[[monosemanticity-score]]'
  target_id: metric:monosemanticity-score
---

Standard [[top-k-sparse-autoencoder]] training fixes k during training, so reconstruction degrades sharply if a different k is used at inference. The [[l1-l2-ratio-regularizer]] penalizes the ratio of L1 to L2 norm of the pre-gate activations, encouraging the encoder to concentrate energy into a small core of highly active units while pushing the remainder toward near-zero (arXiv:2606.27321). This concentration front-loads the most discriminative information into the leading activations, so that using fewer units at inference time drops less useful signal and reconstruction quality remains stable across a broader k range.
