---
aliases:
- LEAst-squares Concept Erasure
- LEACE (LEAst-squares Concept Erasure)
tags:
- kg/method
- concept
- method
kg:
  id: method:leace
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
- '[[rlace]]'
- '[[inlp]]'
- '[[linear-guardedness]]'
relationships:
- type: proposed_by
  target: '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
  target_id: paper:2306.03819
  confidence: high
- type: derived_from
  target: '[[rlace]]'
  target_id: method:rlace
- type: derived_from
  target: '[[inlp]]'
  target_id: method:inlp
- type: related_to
  target: '[[linear-guardedness]]'
  target_id: term:linear-guardedness
---

LEACE computes the unique closed-form affine projection that removes all linearly
decodable information about a concept from an embedding while minimising
mean-squared distortion from the original embedding. The procedure de-means and
whitens the input, projects out the cross-covariance subspace spanned by the
class-conditional means, then reverses the whitening, provably satisfying
[[linear-guardedness]]: no linear classifier can detect the concept above chance
after the projection is applied.

**Why it matters here:** LEACE is the workhorse erasure primitive for
[[concept-scrubbing]], enabling layer-by-layer removal of a target concept
across a full transformer forward pass; applying it to epistemic axes (such as
the doubt or answerability subspace) is the basis for testing whether those axes
are causally active rather than merely correlated with behaviour.

**Lineage:** extends [[rlace]] and [[inlp]]; used as the per-layer operator by
[[concept-scrubbing]].
