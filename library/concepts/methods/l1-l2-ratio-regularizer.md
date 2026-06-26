---
aliases:
- Regularizer 2
- Hoyer-Square regularizer for Top-k SAE
- l1/l2 ratio penalty
- L1/L2-Ratio Regularizer (Top-k SAE)
tags:
- kg/method
- concept
- method
kg:
  id: method:l1-l2-ratio-regularizer
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
- '[[top-k-sparse-autoencoder]]'
- '[[off-support-l1-regularizer]]'
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

The L1/L2-ratio regularizer penalizes the ratio of the L1 norm to the L2 norm of the pre-selection activation vector (restricted to batch-active units), an adaptation of the Hoyer-Square differentiable L0 surrogate. Minimizing this ratio concentrates activation mass onto fewer effective units across the code, increasing global sparsity in expectation and making reconstruction more robust when inference-time k varies. Unlike the [[off-support-l1-regularizer]], it operates over the full distribution of pre-activation values rather than targeting only the off-support subset.

**Why it matters here:** robustness to k variation is practically important for deployable sparse feature dictionaries; combined with [[off-support-l1-regularizer]], the two regularizers provide complementary local and global handles on sparsity, both improving [[monosemanticity-score]].

**Lineage:** augments [[top-k-sparse-autoencoder]] via a scale-invariant global penalty; introduced in [[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]] alongside [[off-support-l1-regularizer]].
