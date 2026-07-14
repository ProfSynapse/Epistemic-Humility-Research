---
aliases:
- Bidirectional bias-direction steering controls judge scores
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:bias-direction-steering-bidirectionally-controls-judge-scores
  type: mechanism
  status: canonical
cause: "A fitted judge-bias direction is added to clean hidden states or subtracted from biased hidden states at a selected layer."
effect: "Judge scores move toward biased behavior in the forward direction and toward baseline behavior in the reverse direction."
polarity: enables
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[effective-bias-vector]]'
- '[[activation-steering]]'
- '[[wasserstein-distance]]'
relationships:
- type: supported_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[effective-bias-vector]]'
  target_id: method:effective-bias-vector
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[wasserstein-distance]]'
  target_id: metric:wasserstein-distance
  confidence: high
---

Forward and reverse steering along the same fitted direction reproduce and reduce scoring bias while maintaining output validity above 0.93. Matched-norm random controls are at least an order of magnitude weaker, supporting direction-specific interventional sufficiency without establishing that the direction is the judge's unique natural causal pathway.
