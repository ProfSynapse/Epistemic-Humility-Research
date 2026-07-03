---
aliases:
- Orthogonality Regularization Enables Unseen Composition
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:orthogonality-enables-compositional-generalization
  type: mechanism
  status: canonical
cause: "Orthogonality regularisation forcing the composition token embedding to remain orthogonal to all frozen behavior-token embeddings during [[compositional-steering-tokens]] training"
effect: "[[compositional-generalization]] to unseen behavior combinations at inference time; the composition token learns a behavior-independent composition operator rather than encoding any specific behavior"
polarity: enables
related:
- '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
- '[[compositional-steering-tokens]]'
- '[[orthogonality-regularization-steering]]'
- '[[compositional-generalization]]'
relationships:
- type: supported_by
  target: '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
  target_id: paper:2601.05062
  confidence: high
- type: related_to
  target: '[[compositional-steering-tokens]]'
  target_id: method:compositional-steering-tokens
- type: related_to
  target: '[[orthogonality-regularization-steering]]'
  target_id: method:orthogonality-regularization-steering
- type: related_to
  target: '[[compositional-generalization]]'
  target_id: term:compositional-generalization
---

Without an orthogonality constraint, a composition token trained to conjoin behaviors tends to collapse onto the semantics of one behavior, failing to generalise to unseen pairings. By forcing the composition token to remain orthogonal to all individual behavior-token embeddings, the regularisation compels the token to encode the logical structure of conjunction rather than any specific behavioral content (arXiv:2601.05062). At inference time this behavior-agnostic composition token then combines arbitrary frozen behavior tokens into novel pairings that were never seen during training.
