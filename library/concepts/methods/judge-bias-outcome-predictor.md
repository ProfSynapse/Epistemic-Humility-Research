---
aliases:
- judge-degradation predictor
- judge bias failure predictor
- activation-based judge failure detector
tags:
- kg/method
- concept
- method
kg:
  id: method:judge-bias-outcome-predictor
  type: method
  status: canonical
area: methods
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[effective-bias-vector]]'
- '[[linear-probe]]'
- '[[auroc]]'
relationships:
- type: proposed_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: derived_from
  target: '[[effective-bias-vector]]'
  target_id: method:effective-bias-vector
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

The judge-bias outcome predictor classifies whether a surface-perturbed answer will receive a score at least one integer point below its paired baseline. Its compact version uses logistic regression over per-layer projections onto fitted LDA and classifier bias directions, rather than attempting only to recognize whether a surface cue is present.

**Why it matters here:** The method turns an internal bias representation into a prospective judge-reliability signal and tests whether that signal transfers to domains excluded from direction fitting.

**Lineage:** Derived from the [[effective-bias-vector]] and operationalized as a [[linear-probe]] whose held-out performance is reported with [[auroc]].
