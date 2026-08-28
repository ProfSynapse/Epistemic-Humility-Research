---
aliases:
- GradCuit
- gradient through circuit
- Credit-Assigned Gradient Flow
tags:
- kg/method
- concept
- method
kg:
  id: method:gradcuit
  type: method
  status: canonical
area: methods
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[activation-intervention]]'
- '[[chain-of-thought-prompting]]'
- '[[policy-gradient]]'
relationships:
- type: proposed_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: variation_of
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: medium
- type: related_to
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
  confidence: high
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
  confidence: high
---

GradCuit is a test-time latent-reasoning method that freezes a Transformer and
optimizes an instance-specific offset to a short prefix's hidden states at a
selected intermediate layer. Because the prefix states participate in causal
self-attention, the log-probability of every continuation token is
differentiable with respect to every preceding latent, allowing a
sequence-level reward to update the latents directly.

**Why it matters here:** It provides an inference-time write interface that can
be paired with answerability, correctness, abstention, or calibration rewards
without retraining the base model. That makes it a candidate instrument for
testing whether internal epistemic readouts can be coupled to selective
behavior during inference.

**Lineage:** It combines an [[activation-intervention]]-like internal-state
write with a [[policy-gradient]] objective and contrasts with explicit
[[chain-of-thought-prompting]] and sampling-based test-time scaling.
