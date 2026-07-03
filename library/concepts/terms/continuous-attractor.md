---
aliases:
- CAN
- continuous attractor dynamics
- Continuous Attractor Network
tags:
- kg/term
- concept
- term
kg:
  id: term:continuous-attractor
  type: term
  status: canonical
area: neuroscience
related:
- '[[disentangled-representation]]'
relationships:
- type: related_to
  target: '[[disentangled-representation]]'
  target_id: term:disentangled-representation
---

A continuous attractor network (CAN) is a dynamical system whose set of stable fixed
points forms a continuous low-dimensional manifold rather than a discrete set of isolated
attractors. Perturbations within the manifold produce slow drift along it rather than
return to a single fixed point, while perturbations off the manifold decay back to it.
RNNs trained on the [[evidence-accumulation-task|multi-task evidence-accumulation]]
paradigm spontaneously develop a 2D continuous attractor whose manifold encodes a
product-space joint estimate of the underlying latent factors, enabling zero-shot
out-of-distribution generalization because any novel factor combination corresponds to a
point already on the manifold.

**Why it matters here:** If a language model's hidden state during generation traces a
low-dimensional continuous manifold indexed by epistemic state (confident-correct,
uncertain, abstaining), then activation-steering interventions can navigate that manifold
to adjust expressed confidence without destabilizing other behaviors, making the geometry
directly actionable for epistemic-humility control.

**Lineage:** related to [[disentangled-representation]]; the CAN geometry is the
dynamical-systems realization of the disentangled product structure that [[multi-task-learning]]
provably induces.
