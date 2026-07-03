---
aliases:
- concept dynamics model
- latent variable model for next-token prediction
tags:
- kg/method
- concept
- method
kg:
  id: method:latent-conditional-model
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2403.03867--origins-linear-representations-large-language-models]]'
- '[[next-token-prediction]]'
relationships:
- type: proposed_by
  target: '[[2403.03867--origins-linear-representations-large-language-models]]'
  target_id: paper:2403.03867
  confidence: high
- type: related_to
  target: '[[next-token-prediction]]'
  target_id: method:next-token-prediction
---

A Latent Conditional Model is a discrete latent variable framework that formalizes LLM next-token prediction: context sentences and tokens are jointly generated from binary latent concept variables via a deterministic map, allowing formal derivation of what representations a model must learn to minimize cross-entropy. The framework proves that linear concept representations arise as a consequence of the [[next-token-prediction]] objective combined with the implicit bias of gradient descent, without any representational inductive bias in the architecture itself.

**Why it matters here:** The proof that knowledge-state structure must be linearly recoverable from residual activations provides theoretical grounding for the known-unknown direction and answerability probe work: linear readout is not merely an empirical observation but a predicted consequence of pretraining.

**Lineage:** introduced in [[2403.03867--origins-linear-representations-large-language-models]]; formally grounds the empirical success of [[next-token-prediction]]-derived linear probes.
