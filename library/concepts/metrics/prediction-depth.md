---
aliases:
- token prediction depth
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:prediction-depth
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[tuned-lens]]'
relationships:
- type: proposed_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
---

Prediction depth is the number of transformer layers required before a model's
top-1 next-token prediction for a given input stabilizes and stops changing, as
read out by the tuned lens at each layer. It serves as a proxy for example
difficulty in pretrained models without requiring task-specific finetuning, and
it correlates with the training iteration at which the model first answers an
example correctly (Spearman rho up to 0.577 on Pythia 12B, Table 2 of the
tuned-lens paper).

**Why it matters here:** Prediction depth is a model-internal signal that
reflects how confidently and early a model resolves a query. High depth (late
stabilization) may indicate uncertainty or knowledge-boundary proximity, making
it a candidate signal for calibration-aware abstention systems.

**Lineage:** defined in [[2303.08112--tuned-lens-eliciting-latent-predictions]];
depends on [[tuned-lens]] to elicit per-layer predictions; conceptually related
to [[prediction-trajectory]] which tracks the sequence of intermediate
predictions rather than the convergence depth.
