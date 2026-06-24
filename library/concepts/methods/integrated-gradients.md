---
aliases:
- IG attribution
- integrated gradient attribution
tags:
- kg/method
- concept
- method
kg:
  id: method:integrated-gradients
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[knowledge-attribution]]'
relationships:
- type: related_to
  target: '[[knowledge-attribution]]'
  target_id: method:knowledge-attribution
---

Integrated Gradients (Sundararajan et al., 2017) attributes a neural network's prediction to individual input features or internal neurons by integrating the gradients of the output with respect to the feature along a straight-line interpolation from a baseline (typically zero) to the actual input or activation value. The integral approximation satisfies axiomatic properties such as sensitivity and implementation invariance that simpler gradient methods violate. It can be applied to any differentiable model without architectural modification.

**Why it matters here:** As a theoretically grounded attribution method, integrated gradients underpins [[knowledge-attribution]], which localizes factual knowledge to specific neurons, providing a principled bridge between model internals and observable epistemic behavior.

**Lineage:** foundational attribution technique that [[knowledge-attribution]] applies to FFN intermediate activations for fact localization.
