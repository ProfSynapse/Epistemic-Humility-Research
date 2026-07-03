---
aliases:
- DoM extraction
- contrastive mean activation extraction
- Difference-of-Means Persona Extraction
tags:
- kg/method
- concept
- method
kg:
  id: method:difference-of-means-persona-extraction
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[persona-vectors]]'
relationships:
- type: derived_from
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
---

Difference-of-Means Persona Extraction elicits a persona vector by generating paired continuations (persona-aligned vs. persona-opposing), filtering by a judge model for trait expression and coherence, recording mean residual-stream activations per condition, and computing the difference: v = h_plus_bar minus h_minus_bar. The method adapts the standard contrastive mean-extraction procedure from instruction-tuned to base-model settings via third-person character descriptions, so no preference labels are required.

**Why it matters here:** The method provides a geometry-first handle on persona-like attributes in base models, which is relevant to understanding how epistemic traits such as hedging or calibrated confidence are encoded prior to any alignment training.

**Lineage:** variant of [[persona-vectors]].
