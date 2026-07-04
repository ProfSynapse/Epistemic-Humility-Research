---
aliases:
- Relaxed Linear Adversarial Concept Erasure
- RLACE (Relaxed Linear Adversarial Concept Erasure)
tags:
- kg/method
- concept
- method
kg:
  id: method:rlace
  type: method
  status: canonical
area: methods
related:
- '[[2201.12091--linear-adversarial-concept-erasure]]'
- '[[inlp]]'
- '[[linear-concept-erasure]]'
relationships:
- type: proposed_by
  target: '[[2201.12091--linear-adversarial-concept-erasure]]'
  target_id: paper:2201.12091
  confidence: high
- type: derived_from
  target: '[[inlp]]'
  target_id: method:inlp
- type: derived_from
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
- type: variation_of
  target: '[[inlp]]'
  target_id: method:inlp
---

RLACE solves the linear maximin concept-erasure game by relaxing the search
space from the set of rank-(D-K) orthogonal projection matrices to the Fantope,
their convex hull, and then running alternating minimisation over the adversarial
classifier parameters and the projection matrix. For K=1, a single
gradient-descent-ascent loop reliably identifies a one-dimensional bias subspace;
projecting out that subspace prevents any linear predictor from recovering the
target concept while minimally distorting the rest of the representation.

**Why it matters here:** RLACE provides the first efficient, provably complete
single-direction erasure and directly enables probing studies that need to remove
a confounding concept before asking whether a second concept is causally active,
which is a design pattern relevant to disentangling epistemic signals.

**Lineage:** extends [[inlp]] and [[linear-concept-erasure]]; the closed-form
distortion-minimising successor is [[leace]].
