---
aliases:
- Concept Ablation Fine-Tuning
- CAFT
- Training-time concept ablation
tags:
- kg/method
- concept
- method
kg:
  id: method:concept-ablation-finetuning
  type: method
  status: canonical
area: methods
related:
- '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
- '[[directional-ablation]]'
- '[[sparse-autoencoder]]'
- '[[low-rank-adaptation]]'
relationships:
- type: proposed_by
  target: '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
  target_id: paper:2507.16795
  confidence: high
- type: derived_from
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
- type: uses
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: medium
---

Concept Ablation Fine-Tuning projects residual-stream activations onto the
orthogonal complement of selected concept directions during every training
forward pass. Gradients pass through the projection, so the model must learn
the training task without using the ablated subspace. The projection is removed
at inference time.

The directions can come from principal components of base-versus-fine-tuned
activation differences or from sparse-autoencoder latents. Human or automated
interpretation selects directions associated with an undesired generalization.

**Why it matters here:** CAFT is a weights-level route for internalizing a
fixed representation-space constraint during fine-tuning. It does not make a
generation-time policy consult a changing latent readout.
