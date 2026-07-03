---
aliases:
- Explicit composition token prevents order-variance collapse
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:explicit-composition-token-prevents-order-collapse
  type: mechanism
  status: canonical
cause: "Training a dedicated composition token that learns behavior-independent composition rather than relying on simple concatenation of [[compositional-steering-tokens]]"
effect: "Lower order variance (reduced sensitivity to token ordering) and higher accuracy on unseen 3-behavior compositions"
polarity: decreases
related:
- '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
- '[[compositional-steering-tokens]]'
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
  target: '[[compositional-generalization]]'
  target_id: term:compositional-generalization
---

When behavior tokens are simply concatenated, their order in the sequence can arbitrarily bias which behavior dominates, because the model has no operator that enforces symmetric composition. Inserting a dedicated composition token trained with orthogonality regularisation provides an explicit operator that treats all behavior tokens symmetrically, reducing sensitivity to ordering (arXiv:2601.05062). Empirically this lowers order variance and raises accuracy on 3-behavior unseen compositions, confirming that the token has learned a genuinely order-invariant composition function rather than absorbing the semantics of a dominant behavior.
