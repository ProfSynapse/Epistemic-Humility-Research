---
aliases:
- Causal separability enables faithful concept editing
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:causal-separability-enables-faithful-editing
  type: mechanism
  status: canonical
cause: "Two concepts satisfying [[causal-separability]] (intervening on one does not affect the marginal distribution of the other in the score representation)"
effect: "Projecting and replacing the target concept's subspace component in the [[score-representation]] changes only that concept while leaving all other concept dimensions unchanged"
polarity: enables
related:
- '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
- '[[causal-separability]]'
- '[[score-representation]]'
- '[[concept-algebra]]'
relationships:
- type: supported_by
  target: '[[2302.03693--concept-algebra-score-based-text-controlled-generative]]'
  target_id: paper:2302.03693
  confidence: high
- type: related_to
  target: '[[causal-separability]]'
  target_id: term:causal-separability
- type: related_to
  target: '[[score-representation]]'
  target_id: method:score-representation
- type: related_to
  target: '[[concept-algebra]]'
  target_id: method:concept-algebra
---

When two concepts are causally separable, the score-representation subspace for each concept is orthogonal to the other's, so intervening on one subspace leaves the other's marginal unchanged. This independence property is the foundation of concept algebra editing in score-based generative models: projecting away one concept's subspace component and replacing it with another concept's component does not leak into unintended dimensions of the representation (arXiv:2302.03693). Empirically the method supports faithful concept transfer in [[stable-diffusion]] without spurious co-changes in unedited attributes.
