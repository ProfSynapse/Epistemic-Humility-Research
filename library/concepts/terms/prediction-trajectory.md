---
aliases:
- latent prediction trajectory
- layer-wise prediction sequence
tags:
- kg/term
- concept
- term
kg:
  id: term:prediction-trajectory
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[tuned-lens]]'
- '[[logit-lens]]'
- '[[residual-stream]]'
relationships:
- type: proposed_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

A prediction trajectory is the sequence of per-layer vocabulary distributions
obtained by applying a lens (logit lens or tuned lens) to the residual stream
at every layer of a transformer forward pass. Empirically, trajectories exhibit
a strong tendency to converge smoothly toward the final output distribution,
with each successive layer typically achieving lower cross-entropy against the
model's final prediction. Deviations from smooth convergence, such as abrupt
reversals or persistent disagreement at mid-layers, can signal prompt injection
or other out-of-distribution processing.

**Why it matters here:** Monitoring how a model's predicted token distribution
evolves layer by layer can reveal when and where uncertainty signals are formed
or suppressed, making prediction trajectories a tool for mechanistic probing of
self-knowledge and calibration in language models.

**Lineage:** introduced alongside [[tuned-lens]] in
[[2303.08112--tuned-lens-eliciting-latent-predictions]]; read from the
[[residual-stream]] via [[logit-lens]] or [[tuned-lens]].
