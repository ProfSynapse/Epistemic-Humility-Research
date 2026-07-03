---
aliases:
- abstract representation
- disentanglement
- factored representation
tags:
- kg/term
- concept
- term
kg:
  id: term:disentangled-representation
  type: term
  status: canonical
area: representation-learning
related: []
relationships: []
---

A disentangled representation encodes distinct latent factors of variation along
approximately orthogonal directions in activation space, such that each factor is
linearly decodable by a simple probe and can be manipulated without disrupting others.
This is weaker than strict axis-alignment: mixed selectivity (units responding to
combinations of factors) is compatible with disentanglement as long as the factors
collectively span distinct subspaces. Disentangled representations enable zero-shot
generalization by allowing novel factor combinations to be expressed as compositions of
already-learned directions.

**Why it matters here:** If epistemic states such as "knows," "doesn't know," and
"uncertain" correspond to disentangled directions in hidden-state space, they can be read
out and causally steered independently, providing the geometric foundation for reliable
abstention, calibration, and [[activation-steering]] without cross-contamination.

**Lineage:** no upstream lineage; realized in practice by [[multi-task-learning]] under
sufficient task diversity, and measured by [[zero-shot-compositional-generalization]] and
[[ood-coefficient-of-determination]].
