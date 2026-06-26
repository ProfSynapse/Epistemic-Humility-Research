---
aliases:
- ILSVRC
- ImageNet-1K classification
- ImageNet-1K
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:imagenet
  type: dataset
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]]'
- '[[top-k-sparse-autoencoder]]'
- '[[monosemanticity-score]]'
relationships:
- type: related_to
  target: '[[top-k-sparse-autoencoder]]'
  target_id: method:top-k-sparse-autoencoder
---

ImageNet-1K (ILSVRC) is a large-scale image classification benchmark containing roughly 1.28 million training images distributed across 1000 object categories, with a 50,000-image validation split; it is the canonical pre-training and evaluation corpus for vision models. In the context of sparse autoencoders trained on vision features, it provides both the activation distribution over which SAE latents are learned and the class-purity and linear-probing evaluation splits used to assess feature quality.

**Why it matters here:** the diversity of visual concepts in ImageNet-1K makes it a demanding test for SAE feature monosemanticity; improvements in [[monosemanticity-score]] measured on this distribution are taken as evidence that auxiliary regularizers produce more interpretable latent representations.

**Lineage:** no direct lineage; used as the training and evaluation corpus in [[2606.27321--beyond-hard-budget-sparsity-regularizers-more-interpretable]].
