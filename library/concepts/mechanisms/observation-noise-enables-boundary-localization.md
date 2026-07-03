---
aliases:
- Observation noise enables latent-boundary distance learning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:observation-noise-enables-boundary-localization
  type: mechanism
  status: canonical
cause: "Non-zero observation noise (sigma > 0) in the [[evidence-accumulation-task|multi-task evidence accumulation]] setting, creating graded classification difficulty that depends on the distance from each decision boundary"
effect: "The model learns to encode distances from classification boundaries, enabling accurate localisation of latent variables and emergence of the 2D [[continuous-attractor]] encoding [[disentangled-representation|disentangled representations]]"
polarity: enables
related:
- '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
- '[[continuous-attractor]]'
- '[[evidence-accumulation-task]]'
- '[[disentangled-representation]]'
relationships:
- type: supported_by
  target: '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
  target_id: paper:2407.11249
  confidence: high
- type: related_to
  target: '[[continuous-attractor]]'
  target_id: term:continuous-attractor
- type: related_to
  target: '[[evidence-accumulation-task]]'
  target_id: term:evidence-accumulation-task
- type: related_to
  target: '[[disentangled-representation]]'
  target_id: term:disentangled-representation
---

Without observation noise, each task presents a deterministic binary label that provides no information about how far the latent state is from the decision boundary, so the model need only encode which side of each boundary the state lies on. With noise, the optimal Bayesian strategy requires encoding continuous distances from boundaries because error probability is a smooth function of boundary distance, and the gradient of this loss propagates information about fine-grained latent position. The disentangling paper (arXiv:2407.11249) shows that this graded pressure is necessary for the emergence of the continuous 2D attractor encoding the latent factors; in the noiseless limit the attractor collapses to a discrete grid.
