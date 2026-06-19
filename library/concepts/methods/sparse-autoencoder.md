---
title: Sparse Autoencoder
aliases:
  - SAE
  - sparse autoencoders
tags:
  - kg/method
  - concept
  - method
kg:
  id: method:sparse-autoencoder
  type: method
  status: canonical
area: methods
related:
  - '[[refusal-direction]]'
  - '[[steering-vector]]'
  - '[[safety-refusal]]'
relationships:
  - type: related_to
    target: '[[refusal-direction]]'
    target_id: term:refusal-direction
    confidence: medium
  - type: related_to
    target: '[[steering-vector]]'
    target_id: term:steering-vector
    confidence: medium
  - type: applied_to
    target: '[[safety-refusal]]'
    target_id: term:safety-refusal
    confidence: medium
---

Sparse autoencoders are representation-learning tools used to decompose dense
model activations into sparse latent features. In this project they are a Phase
3 candidate only after simpler direction and probability-slice diagnostics find
a stable intervention target.

