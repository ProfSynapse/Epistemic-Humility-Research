---
aliases:
- rogue dimensions
- covariance drift across layers
tags:
- kg/term
- concept
- term
kg:
  id: term:representational-drift
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[tuned-lens]]'
- '[[logit-lens]]'
relationships:
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
---

Representational drift refers to the phenomenon in transformer hidden states
where the statistical structure of activations (covariance, outlier dimensions)
changes substantially across layers. A small number of high-variance "rogue
dimensions" are distributed unevenly across the depth of the network, and the
covariance at the final layer often shifts sharply relative to prior layers.
This mismatch causes the logit lens to misinterpret earlier representations as
if they were already in the final layer's coordinate frame, producing
unreliable intermediate predictions.

**Why it matters here:** Representational drift is a confound for any method
that reads epistemic state (uncertainty, confidence, known-unknown direction)
from intermediate layers: raw logit-lens projections can be misleading precisely
at the layers where the drift is largest, so calibration probes must account
for it (e.g., via the affine correction in the tuned lens).

**Lineage:** motivates the design of [[tuned-lens]] as a corrective over
[[logit-lens]]; related to the broader [[superposition-hypothesis]] literature
on non-trivial geometric structure in residual streams.
