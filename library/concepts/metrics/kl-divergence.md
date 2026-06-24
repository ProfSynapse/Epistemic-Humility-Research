---
aliases:
- Kullback-Leibler divergence
- KL divergence
- KL(final || layer)
- KL(input || layer)
- relative entropy
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:kl-divergence
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[logit-lens]]'
- '[[residual-stream]]'
- '[[kl-divergence-penalty]]'
relationships:
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
---

Kullback-Leibler divergence is a non-symmetric, non-negative information-theoretic
measure of how much one probability distribution P differs from a reference
distribution Q, defined as the sum over outcomes of P(x) log(P(x)/Q(x)). A value
of zero means the two distributions are identical; larger values indicate greater
divergence. In the [[logit-lens]] context it is computed in two directions: KL from
each layer's decoded distribution to the final output distribution (measuring how
quickly the [[residual-stream]] converges to the model's ultimate prediction) and
KL from the input embedding distribution to each layer's decoded distribution
(measuring how quickly the input token identity is discarded).

**Why it matters here:** Tracking KL convergence across layers provides a
mechanistic account of where and when a model commits to a prediction, which bears
directly on questions of epistemic humility: a model that converges early and
sharply may be less open to late-layer revision of uncertain predictions.

**Lineage:** used as the convergence diagnostic in [[logit-lens]]; appears as a
regularization term in reinforcement learning as [[kl-divergence-penalty]], which
constrains policy drift during fine-tuning and is directly relevant to RLHF-based
calibration interventions.
