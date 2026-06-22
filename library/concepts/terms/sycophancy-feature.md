---
aliases:
- sycophantic praise feature
- empathy feature
tags:
- kg/term
- concept
- term
kg:
  id: term:sycophancy-feature
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-autoencoder]]'
- '[[sycophancy]]'
- '[[claude-3-sonnet]]'
- '[[feature-steering]]'
relationships:
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
- type: related_to
  target: '[[claude-3-sonnet]]'
  target_id: model:claude-3-sonnet
- type: related_to
  target: '[[feature-steering]]'
  target_id: method:feature-steering
---

Sycophancy features are directions in a model's residual stream, identified via
sparse autoencoders applied to Claude 3 Sonnet, that activate on sycophantic or
empathy-driven praise patterns. When these feature directions are artificially
amplified through activation steering, the model produces noticeably more
sycophantic output, establishing a causal link between the features and the
behavior.

**Why it matters here:** Sycophancy is a calibration failure: a model that tells
users what they want to hear rather than what is accurate violates epistemic
honesty. Identifying causal feature handles gives a mechanistic path toward
measuring and suppressing sycophancy without degrading helpfulness.

**Lineage:** identified via [[sparse-autoencoder]] applied to [[claude-3-sonnet]];
[[feature-steering]] is the intervention method that validates causal role.
