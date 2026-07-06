---
aliases:
- representation manifold
- feature manifold
- on-manifold distance
- geodesic distance in representation space
tags:
- kg/term
- concept
- term
kg:
  id: term:representation-manifold
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2505.18235--origins-representation-manifolds-large-language-models]]'
- '[[multi-dimensional-feature]]'
- '[[linear-representation-hypothesis]]'
- '[[intrinsic-dimension]]'
relationships:
- type: proposed_by
  target: '[[2505.18235--origins-representation-manifolds-large-language-models]]'
  target_id: paper:2505.18235
  confidence: high
- type: related_to
  target: '[[multi-dimensional-feature]]'
  target_id: term:multi-dimensional-feature
  confidence: high
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
  confidence: medium
- type: related_to
  target: '[[intrinsic-dimension]]'
  target_id: metric:intrinsic-dimension
  confidence: medium
---

A representation manifold is the low-dimensional curved submanifold of the unit
hypersphere on which a feature's representation directions live, topologically
homeomorphic to the feature's own metric space so its shape (a curve, loop, or
tree) mirrors the concept's structure rather than collapsing to a single
direction. Modell et al. prove that under a continuous-correspondence assumption
this map is a homeomorphism, and that cosine similarity locally decreases with
squared feature distance, so on-manifold shortest-path (geodesic) distance
recovers intrinsic feature geometry up to a scale constant. They argue manifolds
arise because bending a feature into a higher-dimensional subspace makes a richer
class of functions of its value linearly readable by the next layer.

**Why it matters here:** the representation-manifold view supplies the positive
diagnostic for the interesting slice of the census. A smoothly curved,
connected, low-intrinsic-dimensional shape whose geodesic distances vary
monotonically with an underlying quantity is genuine structure, distinguishable
from both a rank-1 linear feature and a diffuse noise ball.

**Lineage:** the curved-space generalization of the
[[multi-dimensional-feature]]; a refinement of the
[[linear-representation-hypothesis]]; characterized by its
[[intrinsic-dimension]] and geodesic geometry.
