---
aliases:
- truth cone
- multi-dimensional truth cone
- concept cone for truthfulness
tags:
- kg/term
- concept
- term
kg:
  id: term:truth-concept-cone
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
- '[[refusal-concept-cone]]'
- '[[truth-direction]]'
relationships:
- type: proposed_by
  target: '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
  target_id: paper:2505.21800
  confidence: high
- type: derived_from
  target: '[[refusal-concept-cone]]'
  target_id: term:refusal-concept-cone
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
---

A truth concept cone is a multi-dimensional polyhedral cone in an LLM's activation space, spanned by an orthonormal basis of up to five vectors, such that every nonnegative combination of the basis directions causally mediates propositional truth-related behavior: adding a combination to a false-statement activation flips the model toward "true", and ablating the same combination from a true-statement activation flips it toward "false". It extends the earlier single linear truth direction to a subspace-level account of truthfulness.

**Why it matters here:** it is the closest published prior art to the claim that a correctness signal occupies a subspace rather than a single axis, since it demonstrates causal, cross-architecture multi-dimensionality for a closely related construct (propositional truth rather than answer correctness).

**Lineage:** derives from [[refusal-concept-cone]] by extending the concept-cone framework from refusal to propositional truth; related to [[truth-direction]], the single-axis account it generalizes.
