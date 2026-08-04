---
aliases:
- optimized latents most strongly influence reasoning-connector tokens
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:latent-optimization-concentrates-influence-on-reasoning-connectors
  type: mechanism
  status: canonical
cause: "Intermediate latent states are optimized from sequence-level reward through continuation-token gradients."
effect: "Their largest measured first-order influence falls on reasoning-connector tokens rather than uniformly across token categories."
polarity: mediates
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[gradcuit]]'
- '[[chain-of-thought-prompting]]'
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
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
  confidence: high
---

In Section 3.4 and Figure 4, the gradient norm from continuation-token
log-probabilities to all optimized latent states is largest for rule-defined
reasoning connectors such as `because`, `therefore`, and `then` on all three
benchmarks. This is a sensitivity result, not proof that those tokens are the
sole causal mediators of accuracy gains.
