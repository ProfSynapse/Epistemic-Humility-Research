---
aliases:
- SAE decomposability regularizer
- meta-reconstruction penalty
tags:
- kg/method
- concept
- method
kg:
  id: method:decomposability-penalty
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
- '[[metasae]]'
- '[[phi-coefficient-cooccurrence]]'
relationships:
- type: proposed_by
  target: '[[2604.03436--metasaes-joint-training-decomposability-penalty-produces-more]]'
  target_id: paper:2604.03436
  confidence: high
- type: variation_of
  target: '[[metasae]]'
  target_id: method:metasae
---

A per-feature loss term p_i = exp(-||W_dec[i] - W_hat_dec[i]||^2 / sigma^2)
added to the primary SAE loss with strength lambda_2. p_i approaches 1 when the
meta SAE reconstructs feature i easily (the decoder direction lies in the
meta-feature subspace) and approaches 0 when the feature is novel relative to
the meta dictionary. Minimizing the mean penalty pushes primary decoder columns
into directions that are mutually independent and resist sparse meta-compression,
directly penalizing subspace blending during training rather than diagnosing it
post-hoc.

**Why it matters here:** The penalty operationalizes the intuition that a
well-decomposed latent space should have features that are not linear combinations
of each other, which is a prerequisite for clean mechanistic probes of internal
model states (including epistemic signals such as uncertainty or answerability).

**Lineage:** core loss component of [[metasae]]; designed to minimize
[[phi-coefficient-cooccurrence]] across the dictionary; the two are introduced
together in the same paper.
