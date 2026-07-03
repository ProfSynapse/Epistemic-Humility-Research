---
aliases:
- DIM
- mean-difference refusal direction
- Difference-in-Means (DIM)
tags:
- kg/method
- concept
- method
kg:
  id: method:difference-in-means
  type: method
  status: canonical
area: mechanistic-interpretability
related: []
relationships: []
---

Difference-in-Means (DIM) extracts a single direction in residual-stream
activation space by computing the difference between mean hidden-state
activations elicited by harmful prompts and mean activations elicited by
harmless prompts at a chosen layer. The resulting vector approximates the
linear axis most predictive of whether a prompt will be refused, and can be
used for both probing and [[directional-ablation]]. DIM is computationally
cheap (no training beyond a single mean subtraction) and serves as the primary
baseline against which more expressive multi-direction methods are compared in
refusal geometry work.

**Why it matters here:** DIM produces the canonical single-axis view of
refusal that subsequent research challenges: if refusal is governed by more
than one direction, DIM understimates the geometry and a [[safety-residual-space]]
decomposition is needed instead.

**Lineage:** foundational baseline method in activation-space interpretability;
the [[dominant-refusal-direction]] framework uses DIM as its comparison point.
