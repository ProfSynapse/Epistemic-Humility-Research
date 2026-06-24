---
aliases:
- CCS
- Contrast Consistent Search
tags:
- kg/method
- concept
- method
kg:
  id: method:contrast-consistent-search
  type: method
  status: canonical
area: methods
related:
- '[[2212.03827--ccs-discovering-latent-knowledge]]'
- '[[linear-probe]]'
- '[[mass-mean-probing]]'
- '[[truth-direction]]'
- '[[generation-discrimination-gap]]'
- '[[contrastive-representation-clustering]]'
- '[[negation-consistency-loss-separates-latent-knowledge-from-output-imitation]]'
relationships:
- type: proposed_by
  target: '[[2212.03827--ccs-discovering-latent-knowledge]]'
  target_id: paper:2212.03827
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[mass-mean-probing]]'
  target_id: method:mass-mean-probing
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[contrastive-representation-clustering]]'
  target_id: method:contrastive-representation-clustering
  confidence: medium
- type: related_to
  target: '[[negation-consistency-loss-separates-latent-knowledge-from-output-imitation]]'
  target_id: mechanism:negation-consistency-loss-separates-latent-knowledge-from-output-imitation
  confidence: medium
---

An unsupervised linear probing method that recovers a model's latent knowledge from hidden-state activations by learning a probe satisfying two consistency constraints: negation consistency (p(statement) + p(negation) = 1) and confidence (predictions are decisive). No labels, model outputs, or weight updates are used.

**Why it matters here:** Provides a zero-label upper bound on what activation-space knowledge extraction can achieve, and is the canonical baseline for all subsequent latent-knowledge and representation-reading methods in the epistemic-humility literature.

**Lineage:** Introduced by Burns et al. (2022) as the empirical counterpart to the theoretical Eliciting Latent Knowledge (ELK) problem; preceded by zero-shot and calibrated zero-shot baselines it outperforms; extended by ITI (2306.03341) which uses it as an ablation direction estimator.
