---
aliases:
- Orthogonality alone does not imply representational independence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:orthogonality-does-not-imply-independence
  type: mechanism
  status: canonical
cause: "Ablating one [[refusal-direction]] from [[residual-stream]] activations, which then propagates through non-linear transformer layers downstream"
effect: "The cosine similarity of a geometrically orthogonal refusal direction with model activations changes in later layers, violating causal independence despite zero inner product at the ablation site"
polarity: enables
related:
- '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
- '[[representational-independence]]'
- '[[refusal-direction]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2502.17420--geometry-refusal-large-language-models-concept-cones]]'
  target_id: paper:2502.17420
  confidence: high
- type: related_to
  target: '[[representational-independence]]'
  target_id: term:representational-independence
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

Two directions in a model's activation space can be geometrically orthogonal (zero inner product) yet causally entangled: ablating one direction alters the downstream representation of the other because non-linear transformer operations mix them in subsequent layers. The refusal concept-cones paper (arXiv:2502.17420) demonstrates this empirically by ablating one refusal direction and showing that cosine similarities of nominally orthogonal directions with later-layer activations shift significantly. This finding motivates the stricter criterion of [[representational-independence]] (causal non-interference) rather than geometric orthogonality alone when designing multi-direction refusal interventions.
