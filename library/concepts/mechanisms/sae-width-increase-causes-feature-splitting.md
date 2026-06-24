---
aliases:
- SAE Width Increase Causes Feature Splitting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-width-increase-causes-feature-splitting
  type: mechanism
  status: canonical
cause: Increasing the [[sparse-autoencoder]] dictionary size from a 1x expansion factor to 256x (512 to 131,072 features)
effect: Coarse features split into finer sub-features; at 131,072 features the autoencoder recovers 94.5% of MLP log-likelihood loss versus 79% at 4,096 features
polarity: enables
related:
- '[[tc2023--towards-monosemanticity]]'
- '[[sparse-autoencoder]]'
- '[[feature-splitting]]'
- '[[monosemanticity]]'
relationships:
- type: supported_by
  target: '[[tc2023--towards-monosemanticity]]'
  target_id: paper:tc2023
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
---

Bricken et al. (tc2023) train sparse autoencoders of varying widths on a one-layer transformer MLP and observe that expanding the dictionary causes previously merged feature detectors to split into more specific sub-features. The largest dictionary (131,072 features, 256x expansion) recovers 94.5% of the MLP's contribution to log-likelihood, substantially more than the 79% recovered at 4,096 features. This suggests that the granularity of learned features is limited by dictionary capacity, and that hierarchical feature structure emerges naturally as capacity increases.
