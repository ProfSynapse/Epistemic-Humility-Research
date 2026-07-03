---
aliases:
- Semantic subspace mismatch degrades activation steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:semantic-subspace-mismatch-degrades-steering
  type: mechanism
  status: canonical
cause: "Applying a domain-mismatched [[semantic-prior-subspace]] (e.g., safety concept vectors) to steer a different target domain (e.g., reasoning tasks) via [[activation-steering]]"
effect: "Substantial performance degradation and elevated variance across all target-domain tasks compared to a domain-matched subspace"
polarity: decreases
related:
- '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
- '[[semantic-prior-subspace]]'
- '[[activation-steering]]'
- '[[steer2adapt]]'
relationships:
- type: supported_by
  target: '[[2602.07276--steer2adapt-dynamically-composing-steering-vectors-elicits-efficient]]'
  target_id: paper:2602.07276
  confidence: high
- type: related_to
  target: '[[semantic-prior-subspace]]'
  target_id: term:semantic-prior-subspace
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
- type: related_to
  target: '[[steer2adapt]]'
  target_id: method:steer2adapt
---

Activation steering by projecting interventions onto a semantic subspace borrowed from an unrelated domain fails because the subspace does not span the directions relevant to the target domain, causing the intervention to perturb uninformative directions or introduce noise. The Steer2Adapt paper (arXiv:2602.07276) demonstrates this by applying safety-domain concept vectors to reasoning tasks and observing significant accuracy drops and variance spikes relative to using a domain-matched subspace. The finding motivates constructing task-specific subspaces via Bayesian optimisation over a small held-out set rather than recycling subspaces across domains.
