---
aliases:
- SAE features enable finer causal localisation of model behaviour than PCA
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sae-features-enable-finer-causal-localisation
  type: mechanism
  status: canonical
cause: Using sparse autoencoder features as the intervention basis for activation patching on the IOI task
effect: Fewer feature patches are required to reach a given KL divergence from the target output, and smaller edit magnitudes achieve the same degree of counterfactual behaviour, compared to PCA components
polarity: enables
related:
- '[[2309.08600--sparse-autoencoders-interpretable-features]]'
- '[[sparse-autoencoder]]'
- '[[activation-patching]]'
- '[[indirect-object-identification]]'
- '[[sae-sparsity-increases-feature-interpretability]]'
relationships:
- type: supported_by
  target: '[[2309.08600--sparse-autoencoders-interpretable-features]]'
  target_id: paper:2309.08600
  confidence: high
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: related_to
  target: '[[indirect-object-identification]]'
  target_id: dataset:indirect-object-identification
---

On the [[indirect-object-identification]] (IOI) task, using [[sparse-autoencoder]] features as intervention units in activation patching requires fewer patched features to achieve a given KL divergence from the target output than using PCA components of the same activation space (arXiv:2309.08600). Additionally, smaller absolute edit magnitudes are needed per SAE feature to produce equivalent counterfactual behavior, indicating that SAE features are more causally concentrated on the behavior of interest. This finer causal localization makes SAE features preferable to PCA for circuit-level mechanistic analysis.
