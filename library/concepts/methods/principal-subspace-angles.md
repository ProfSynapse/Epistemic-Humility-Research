---
aliases:
- SSA
- principal subspace angles
- Grassmann distance
tags:
- kg/method
- concept
- method
kg:
  id: method:principal-subspace-angles
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2310.16484--subspace-chronicles-how-linguistic-information-emerges-shifts]]'
- '[[pretraining-checkpoint-tracing]]'
- '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
relationships:
- type: related_to
  target: '[[2310.16484--subspace-chronicles-how-linguistic-information-emerges-shifts]]'
  target_id: paper:2310.16484
  confidence: high
- type: related_to
  target: '[[pretraining-checkpoint-tracing]]'
  target_id: method:pretraining-checkpoint-tracing
  confidence: medium
- type: related_to
  target: '[[subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance]]'
  target_id: mechanism:subspace-identity-rotates-across-seeds-and-checkpoints-despite-stable-probe-performance
  confidence: high
---

Principal Subspace Angles (SSA) compare two linear subspaces theta_A in R^(d x p) and theta_B in R^(d x q) without requiring matched inputs or labels: orthonormalize each to Q_A, Q_B, take the transformation magnitudes M = Q_A^T Q_B, run an SVD on M, and convert the resulting singular values to angles via arccos. The result is a set of angles between 0 degrees (identical subspaces) and 90 degrees (orthogonal, maximally dissimilar), closely related to Grassmann distance. Unlike SVCCA or PWCCA, SSA needs only the probe weight matrices, so it can compare subspaces fit on different datasets, tasks, or checkpoints directly.

**Why it matters here:** SSA is precedent for exactly the operation a correctness-subspace-overlap estimator needs, comparing two fitted subspaces (e.g., across training stages or seeds) purely from their bases, and its reported behavior (large angles between same-timestep, different-seed probes; slowly narrowing angles across checkpoints even after task performance plateaus) is a second independent instrument reaching the same qualitative conclusion as the correctness-direction-rotation cell's cosine-based finding: a stable readout does not imply a stable direction.

**Lineage:** builds on Knyazev and Argentati's (2002) Grassmann-distance formulation, not yet ingested into this vault; operationalized for cross-checkpoint LM probing in [[2310.16484--subspace-chronicles-how-linguistic-information-emerges-shifts]]; sibling to [[pretraining-checkpoint-tracing]], which tracks a single mean-difference direction across checkpoints rather than a full probe subspace.
