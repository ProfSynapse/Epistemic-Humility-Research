---
aliases:
- self-distillation for steering tokens
- KL-distillation from instruction teacher
- Compositional Self-Distillation
tags:
- kg/method
- concept
- method
kg:
  id: method:compositional-self-distillation
  type: method
  status: canonical
area: steering
related:
- '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
- '[[compositional-steering-tokens]]'
relationships:
- type: proposed_by
  target: '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
  target_id: paper:2601.05062
  confidence: high
- type: required_by
  target: '[[compositional-steering-tokens]]'
  target_id: method:compositional-steering-tokens
---

Two-stage training procedure for [[compositional-steering-tokens]]. Stage 1 trains
individual behavior tokens by minimizing KL-divergence between an instruction-prompted
teacher LLM and a steering-token-prompted student (same frozen LLM), using high
temperature (T=10) and 10 instruction paraphrases per behavior. Stage 2 trains the
composition token on two-behavior combinations while keeping all behavior token
embeddings and the LLM frozen, allowing the composition token to learn a
behavior-independent composition concept.

**Why it matters here:** The distillation objective transfers behavioral knowledge from
an explicit natural-language instruction into a compact embedding; this provides a
principled mechanism for encoding epistemic dispositions (expressing uncertainty,
refusing unanswerable questions) as controllable input-space vectors that can be
toggled without modifying the underlying policy.

**Lineage:** required by [[compositional-steering-tokens]]; the composition token is
additionally shaped by [[orthogonality-regularization-steering]] during Stage 2
training.
