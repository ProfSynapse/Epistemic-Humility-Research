---
aliases:
- Multi-task pressure induces disentangled representations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:multitask-pressure-induces-disentanglement
  type: mechanism
  status: canonical
cause: "Optimal simultaneous solution of N_task >= D noisy [[evidence-accumulation-task|evidence-accumulation classification tasks]] whose decision-boundary normals span the input space"
effect: "Guaranteed emergence of abstract, [[disentangled-representation|disentangled representations]] of the underlying ground-truth latent factors in the model's internal state"
polarity: enables
related:
- '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
- '[[disentangled-representation]]'
- '[[multi-task-learning]]'
- '[[continuous-attractor]]'
- '[[evidence-accumulation-task]]'
relationships:
- type: supported_by
  target: '[[2407.11249--disentangling-representations-through-multi-task-learning]]'
  target_id: paper:2407.11249
  confidence: high
- type: related_to
  target: '[[disentangled-representation]]'
  target_id: term:disentangled-representation
- type: related_to
  target: '[[multi-task-learning]]'
  target_id: method:multi-task-learning
- type: related_to
  target: '[[continuous-attractor]]'
  target_id: term:continuous-attractor
---

When a model must simultaneously optimise for at least D classification tasks whose decision-boundary normals span the D-dimensional latent factor space, the optimal solution encodes each latent factor in a separate dimension of the model's internal representation. The disentangling paper (arXiv:2407.11249) proves this geometrically and confirms it empirically: as N_task reaches D, representations transition abruptly from entangled to disentangled, with the disentangled state manifesting as a 2D continuous attractor whose axes correspond to the ground-truth latent factors. The guarantee requires that boundary normals span the space, so task diversity is the key design constraint.
