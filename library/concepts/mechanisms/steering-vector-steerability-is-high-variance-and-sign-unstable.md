---
aliases:
- steering vectors are unreliable and per-input sign-unstable
- many inputs are anti-steerable under CAA
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:steering-vector-steerability-is-high-variance-and-sign-unstable
  type: mechanism
  status: canonical
cause: "Applying a contrastive-activation-addition steering vector across the inputs of a behavior dataset."
effect: "Per-input steerability varies widely within and across concepts; for several datasets roughly half of inputs are anti-steerable (the same direction moves behavior the opposite way), some behaviors are un-steerable, and spurious dataset factors dominate effectiveness."
polarity: prevents
related:
- '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
- '[[steerability]]'
- '[[steering-vector]]'
- '[[contrastive-activation-addition]]'
relationships:
- type: supported_by
  target: '[[2407.12404--analyzing-generalization-reliability-steering-vectors]]'
  target_id: paper:2407.12404
  confidence: high
- type: related_to
  target: '[[steerability]]'
  target_id: metric:steerability
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: medium
---

Tan et al. find CAA steering vectors are substantially unreliable in-distribution:
per-input steerability varies widely within and across the Model-Written
Evaluations concepts, several datasets produce the opposite behavior for almost
50% of inputs (anti-steerable), some behaviors are effectively un-steerable, and
spurious dataset factors strongly affect how well steering works. This documents
that a direction which separates a behavior on average can have an unstable,
per-input-dependent causal sign, the prior-art grounding for a probe direction
whose causal steering sign does not match its projection.
