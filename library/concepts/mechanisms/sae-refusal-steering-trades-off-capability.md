---
title: SAE Refusal Steering Trades Off Capability
aliases:
  - SAE refusal features are capability-entangled
tags:
  - kg/mechanism
  - concept
  - mechanism
kg:
  id: mechanism:sae-refusal-steering-trades-off-capability
  type: mechanism
  status: canonical
cause: Amplifying sparse-autoencoder refusal features at inference time.
effect: Jailbreak robustness can improve while benchmark capability degrades.
polarity: trades_off
related:
  - '[[2411.11296--steering-refusal-with-sparse-autoencoders]]'
  - '[[sparse-autoencoder]]'
  - '[[safety-refusal]]'
relationships:
  - type: supported_by
    target: '[[2411.11296--steering-refusal-with-sparse-autoencoders]]'
    target_id: paper:2411.11296
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

This mechanism records the encoder/SAE caution for Phase 3: even when a sparse
feature is behaviorally active, steering it may harm unrelated capabilities.

