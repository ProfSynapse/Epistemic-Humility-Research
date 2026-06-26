---
aliases:
- SAE monosemanticity score
- Pach monosemanticity score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:monosemanticity-score
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[monosemanticity]]'
- '[[polysemanticity]]'
- '[[off-support-l1-regularizer]]'
- '[[l1-l2-ratio-regularizer]]'
- '[[top-k-sparse-autoencoder]]'
relationships:
- type: related_to
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: related_to
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
---

The monosemanticity score (Pach et al. 2025) quantifies how visually and semantically coherent the examples that most strongly activate a given SAE latent unit are, computed as the mean pairwise embedding similarity of top-activating samples. Higher values indicate a more concept-selective, monosemantic unit. The metric enables large-scale automated comparison of SAE configurations without requiring manual feature labeling.

**Why it matters here:** monosemanticity is a central desideratum in mechanistic interpretability because it determines whether learned features can serve as a reliable, human-auditable basis for understanding model behavior; the score provides an operationalization of that desideratum applicable to vision SAEs.

**Lineage:** no direct methodological lineage; used as the primary interpretability measure for evaluating [[off-support-l1-regularizer]] and [[l1-l2-ratio-regularizer]] on [[top-k-sparse-autoencoder]] models.
