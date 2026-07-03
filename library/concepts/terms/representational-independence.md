---
aliases:
- RepInd
- representationally independent directions
tags:
- kg/term
- concept
- term
kg:
  id: term:representational-independence
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[directional-ablation]]'
relationships:
- type: proposed_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: derived_from
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
---

Representational independence is a stricter criterion for independence between
activation-space directions than geometric orthogonality. Two directions are
representationally independent if ablating one does not change the cosine
similarity of the other with the model's residual-stream activations at any
layer. This criterion captures both linear and non-linear interactions
propagated through the network's non-linearities, closing the gap that
geometric orthogonality alone leaves open. In practice, refusal concept cones
are constructed from directions that are not only orthogonal but also
representationally independent, ensuring that steering one concept does not
inadvertently perturb another.

**Why it matters here:** If doubt and caution occupy representationally
independent directions, they can in principle be steered separately, which is
the precondition for the compound-caution decomposition hypothesis: one can
boost or suppress epistemic caution without touching the underlying doubt
signal.

**Lineage:** extends [[directional-ablation]], which provides the ablation
mechanism used to test independence.
