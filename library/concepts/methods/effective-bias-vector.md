---
aliases:
- effective bias vector
- judge bias direction
- bias-direction estimator
tags:
- kg/method
- concept
- method
kg:
  id: method:effective-bias-vector
  type: method
  status: canonical
area: methods
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[activation-steering]]'
- '[[steering-vector]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
---

An effective bias vector is a unit-normalized direction estimated from paired hidden-state differences for inputs whose surface cue changes an LLM judge's score by a prespecified amount. Xu et al. fit directional summaries and discriminative boundaries, then use the resulting directions for geometry analysis, activation steering, and outcome prediction.

**Why it matters here:** Restricting direction fitting to observed paired failures separates samples that exhibit the target scoring failure from null-shift observations and yields a direct causal intervention target.

**Lineage:** A judge-specific application of [[steering-vector]] estimation that combines contrastive activation differences with [[linear-probe]] style discriminative directions and is tested through [[activation-steering]].
