---
aliases:
- self-attention gives every continuation token a gradient path to every inserted latent
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:self-attention-routes-token-credit-to-intermediate-latents
  type: mechanism
  status: canonical
cause: "Instance-specific latent states are inserted before the continuation at an intermediate Transformer layer."
effect: "Causal self-attention gives every continuation-token log-probability a differentiable path to every preceding latent state."
polarity: enables
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[gradcuit]]'
- '[[policy-gradient]]'
relationships:
- type: supported_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: related_to
  target: '[[gradcuit]]'
  target_id: method:gradcuit
  confidence: high
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
  confidence: high
---

GradCuit's factorization keeps the inserted states inside the remaining
Transformer computation. Equations 4-7 show that sequence-wide,
reward-weighted token gradients can therefore be accumulated directly on each
latent rather than being restricted to a separately decoded prefix token.
