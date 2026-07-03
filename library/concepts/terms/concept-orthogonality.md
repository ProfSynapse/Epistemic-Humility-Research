---
aliases:
- orthogonal concept representations
- independent concepts are orthogonal
- near-orthogonal unrelated concepts
tags:
- kg/term
- concept
- term
kg:
  id: term:concept-orthogonality
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[linear-representation-hypothesis]]'
relationships:
- type: derived_from
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
---

Concept orthogonality is the empirical and theoretical finding that semantically unrelated (statistically independent) concepts tend to be represented as approximately orthogonal vectors in the unembedding space of large language models. Formally, the result follows from the latent conditional model via a theorem showing that the inner product between the unembedding vectors of statistically independent concepts decays toward zero as training under the next-token-prediction objective continues. Empirical validation in models such as LLaMA-2 confirms that cross-category concept vectors are nearly perpendicular while within-category vectors are nontrivially aligned, with the degree of orthogonality tracking statistical independence in the training corpus.

**Why it matters here:** Concept orthogonality implies that a linear probe for one epistemic property (e.g., answerability) should not spuriously encode an unrelated property (e.g., topic domain), which supports the interpretive validity of the two-signal readout probes central to this project.

**Lineage:** derived from [[linear-representation-hypothesis]]; the orthogonality result follows when the linear hypothesis holds and concepts are statistically independent in the training distribution.
