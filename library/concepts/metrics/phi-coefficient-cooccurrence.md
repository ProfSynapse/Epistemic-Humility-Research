---
aliases:
- mean |phi|
- phi coefficient
- SAE latent co-activation metric
- Phi Coefficient Co-occurrence (|phi|)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:phi-coefficient-cooccurrence
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[decomposability-penalty]]'
- '[[metasae]]'
relationships:
- type: related_to
  target: '[[decomposability-penalty]]'
  target_id: method:decomposability-penalty
- type: related_to
  target: '[[metasae]]'
  target_id: method:metasae
---

The phi (phi) coefficient measures co-occurrence of two binary SAE latent firing
indicators above chance: phi(i,j) = (N_11 * n - N_1i * N_1j) /
sqrt(N_1i * (n - N_1i) * N_1j * (n - N_1j)). Mean |phi| averaged over all
feature pairs in the dictionary serves as the primary atomicity metric for sparse
autoencoders. It is normalized by marginal firing rates so that changes in
individual feature firing frequency do not confound the measurement, and lower
mean |phi| indicates more statistically independent (more atomic) feature
co-activations.

**Why it matters here:** This metric provides a quantitative handle on how much
SAE features co-activate, which is a proxy for polysemanticity; reducing it is
the stated optimization target of [[decomposability-penalty]] and the primary
measure of improvement for [[metasae]].

**Lineage:** standalone measurement grounded in classical correlation statistics;
used as the primary evaluation target in the [[metasae]] paper.
