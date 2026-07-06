---
aliases:
- multi-dimensional feature
- multidimensional feature
- irreducible feature
- circular feature
- circular representation
tags:
- kg/term
- concept
- term
kg:
  id: term:multi-dimensional-feature
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2405.14860--not-all-language-model-features-one-dimensionally]]'
- '[[linear-representation-hypothesis]]'
- '[[representation-manifold]]'
- '[[superposition-hypothesis]]'
- '[[sparse-autoencoder]]'
relationships:
- type: proposed_by
  target: '[[2405.14860--not-all-language-model-features-one-dimensionally]]'
  target_id: paper:2405.14860
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: high
- type: related_to
  target: '[[representation-manifold]]'
  target_id: term:representation-manifold
  confidence: high
- type: related_to
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
  confidence: medium
---

A multi-dimensional feature is a concept represented in a low-dimensional but
not one-dimensional linear subspace of activation space. Engels et al. call a
feature irreducible when no rotation plus translation makes its coordinates
either separable (independent marginals) or a mixture (non-co-occurring
lower-dimensional parts), so it cannot be decomposed into lower-dimensional
features. Their SAE-clustering method auto-discovers such features, most vividly
circular features for days of the week, months, and years, and interventions on
only the circular subspace nearly match patching the whole layer, showing these
rings are causally used for modular arithmetic in GPT-2, Mistral 7B, and Llama 3
8B.

**Why it matters here:** a multi-dimensional feature is the interesting
alternative identity for out-of-span displacement. If a slice of the census
residual traces a curved, low-dimensional shape (a ring or simplex) that no
single named axis captures, it may be a genuine multi-dimensional epistemic
feature worth adding to the knob screen, not a nuisance.

**Lineage:** refines the [[linear-representation-hypothesis]] (features are
linear subspaces but not always one-dimensional); the flat-space special case of
a [[representation-manifold]]; packed via a multi-dimensional generalization of
the [[superposition-hypothesis]]; discovered with [[sparse-autoencoder]]
clustering.
