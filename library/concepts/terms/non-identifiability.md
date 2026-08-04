---
aliases:
- non-identifiable
- identifiability failure
- non-identifiable steering vectors
tags:
- kg/term
- concept
- term
kg:
  id: term:non-identifiability
  type: term
  status: canonical
area: terms
related:
- '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
- '[[steering-vector]]'
- '[[orthogonal-perturbation-test]]'
relationships:
- type: proposed_by
  target: '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
  target_id: paper:2602.06801
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[orthogonal-perturbation-test]]'
  target_id: method:orthogonal-perturbation-test
  confidence: high
---

Non-identifiability, applied to steering vectors, describes the property that
a behaviorally observed intervention (e.g. a [[steering-vector]] that shifts a
model's output toward some trait) does not uniquely determine an underlying
internal direction. Under white-box single-layer access, many geometrically
distinct vectors -- including ones that are orthogonal or even nearly
anti-aligned with one another -- fall into the same behavioral equivalence
class, so behavioral testing alone cannot recover a unique "true" direction.

**Why it matters here:** it is the central negative result of
[[2602.06801--non-identifiability-steering-vectors-large-language-models]]:
steering vectors are widely interpreted as revealing meaningful internal
representations, but this interpretation assumes identifiability that the
paper shows does not hold, undercutting behavior-only evidence for the
[[linear-representation-hypothesis]] in steering studies.

**Lineage:** established empirically via the
[[orthogonal-perturbation-test]] and via SVD-based null-space estimation of
the activation-to-logit map.
