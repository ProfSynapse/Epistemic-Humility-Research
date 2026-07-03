---
aliases:
- orthogonality loss
- L_orth
- composition token orthogonality
- Orthogonality Regularization for Composition Tokens
tags:
- kg/method
- concept
- method
kg:
  id: method:orthogonality-regularization-steering
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

A regularization term added during composition-token training that penalizes cosine
similarity between the composition-token embedding and all frozen behavior-token
embeddings: L_orth = sum_b (e_and dot e_b / (||e_and|| ||e_b||))^2. Combined with
the distillation loss as L = L_dist + lambda L_orth (default lambda=0.5). The
penalty prevents the composition token from collapsing into any single behavior
representation and is the mechanism that enables compositional generalization to
unseen behavior pairs.

**Why it matters here:** Geometric orthogonality between the composition operator and
individual behavior embeddings mirrors the [[representational-independence]] principle,
ensuring that distinct epistemic dispositions (hedging, task compliance) can co-exist
as non-interfering directions in input space.

**Lineage:** required by [[compositional-steering-tokens]]; the geometric motivation
parallels [[orthogonality-enables-compositional-generalization]] in the steering
literature.
