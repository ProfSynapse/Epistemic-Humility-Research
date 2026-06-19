---
title: SAE Features Mediate Refusal
aliases:
  - sparse features mediate refusal behavior
tags:
  - kg/mechanism
  - concept
  - mechanism
kg:
  id: mechanism:sae-features-mediate-refusal
  type: mechanism
  status: canonical
cause: Intervening on sparse-autoencoder features associated with refusal.
effect: Refusal behavior changes during generation.
polarity: mediates
related:
  - '[[2505.23556--understanding-refusal-with-sparse-autoencoders]]'
  - '[[sparse-autoencoder]]'
  - '[[safety-refusal]]'
relationships:
  - type: supported_by
    target: '[[2505.23556--understanding-refusal-with-sparse-autoencoders]]'
    target_id: paper:2505.23556
    confidence: medium
  - type: related_to
    target: '[[sparse-autoencoder]]'
    target_id: method:sparse-autoencoder
    confidence: high
  - type: related_to
    target: '[[safety-refusal]]'
    target_id: term:safety-refusal
    confidence: high
---

This mechanism is a Phase 3 candidate for future SAE work. It is about
safety-refusal features in aligned models, not yet about epistemic abstention
or known/unknown calibration in this project.

