---
aliases:
- Jacobian null space makes steering vectors non-identifiable
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:jacobian-null-space-makes-steering-vectors-non-identifiable
  type: mechanism
  status: canonical
cause: The activation-to-logit map's Jacobian has a large, depth-stable null space -- SVD of the activation covariance matrix shows ~86-94% of directions are behaviorally inert across the models studied.
effect: Perturbations to a steering vector that fall within that null space, such as orthogonal or even near-anti-aligned directions, leave model behavior statistically unchanged, so the steering vector's direction cannot be uniquely recovered from behavioral evidence alone.
polarity: enables
related:
- '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
- '[[steering-vector]]'
- '[[non-identifiability]]'
- '[[orthogonal-perturbation-test]]'
relationships:
- type: supported_by
  target: '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
  target_id: paper:2602.06801
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[non-identifiability]]'
  target_id: term:non-identifiability
  confidence: high
- type: related_to
  target: '[[orthogonal-perturbation-test]]'
  target_id: method:orthogonal-perturbation-test
  confidence: high
---

A large null space in the activation-to-logit Jacobian means most directions
in activation space have no measurable effect on model output, so a wide,
high-dimensional equivalence class of steering vectors produces
behaviorally indistinguishable interventions.
