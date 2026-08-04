---
aliases:
- orthogonal perturbation test
- orthogonal perturbation
tags:
- kg/method
- concept
- method
kg:
  id: method:orthogonal-perturbation-test
  type: method
  status: canonical
area: methods
related:
- '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
- '[[steering-vector]]'
- '[[non-identifiability]]'
- '[[cohens-d]]'
relationships:
- type: proposed_by
  target: '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
  target_id: paper:2602.06801
  confidence: high
- type: uses
  target: '[[cohens-d]]'
  target_id: metric:cohens-d
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[non-identifiability]]'
  target_id: term:non-identifiability
  confidence: high
---

The orthogonal perturbation test evaluates whether a [[steering-vector]]'s
behavioral effect is specific to its direction by adding a randomly sampled
unit vector orthogonal to the original steering vector and comparing the
resulting behavioral shift, measured with [[cohens-d]], against the original
vector's effect. If the orthogonal perturbation produces a statistically
indistinguishable (negligible-effect-size) shift, the steering vector's
direction is not behaviorally identifiable from that intervention alone.

**Why it matters here:** it is the primary experimental instrument of
[[2602.06801--non-identifiability-steering-vectors-large-language-models]]
for demonstrating [[non-identifiability]] -- run across five semantic traits
and two models, and repeated across prompt environments and the operational
steering range to rule out artifact explanations.
