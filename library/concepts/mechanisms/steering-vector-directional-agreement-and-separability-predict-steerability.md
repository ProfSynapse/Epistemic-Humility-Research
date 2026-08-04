---
aliases:
- directional agreement and separability predict steerability
- cosine similarity and d' predict steering effectiveness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:steering-vector-directional-agreement-and-separability-predict-steerability
  type: mechanism
  status: canonical
cause: "A behavior dataset's per-sample activation differences have high cosine similarity to the aggregate contrastive-activation-addition steering vector, and its positive/negative activations are well separated (high discriminability index d') along the difference-of-means line."
effect: "The resulting steering vector produces a larger average steering effect size and a smaller fraction of anti-steerable samples than datasets with dispersed, low-cosine-similarity activation differences or overlapping, high-variance activations."
polarity: enables
related:
- '[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]'
- '[[cosine-similarity]]'
- '[[discriminability-index]]'
- '[[steerability]]'
- '[[steering-vector]]'
- '[[contrastive-activation-addition]]'
relationships:
- type: supported_by
  target: '[[2505.22637--understanding-un-reliability-steering-vectors-language-models]]'
  target_id: paper:2505.22637
  confidence: high
- type: related_to
  target: '[[cosine-similarity]]'
  target_id: metric:cosine-similarity
  confidence: high
- type: related_to
  target: '[[discriminability-index]]'
  target_id: metric:discriminability-index
  confidence: high
- type: related_to
  target: '[[steerability]]'
  target_id: metric:steerability
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
---

Braun et al. identify two correlated geometric predictors of how reliably a
contrastive-activation-addition steering vector works: (1) directional
agreement, the [[cosine-similarity]] between individual training samples'
activation differences and the aggregate steering vector, and (2) separability,
the [[discriminability-index]] (d') of positive versus negative activations
projected onto the difference-of-means line. Datasets where samples agree in
direction and separate cleanly yield larger steering effects and fewer
anti-steerable samples; datasets with dispersed or orthogonal per-sample
differences and overlapping activation clusters are unreliable to steer even
though the aggregate vector still has a net-positive average effect. This
complements
[[steering-vector-steerability-is-high-variance-and-sign-unstable]] by
supplying the geometric explanation for *why* steerability varies so much
across datasets rather than only documenting that it does.
