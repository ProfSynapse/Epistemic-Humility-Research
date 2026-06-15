---
aliases:
- AUD
- Answer Uncertainty Disparity (AUD)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:answer-uncertainty-disparity
  type: metric
  status: canonical
area: metrics
related:
- '[[2305.13712--kuq-knowledge-of-knowledge]]'
- '[[self-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2305.13712--kuq-knowledge-of-knowledge]]'
  target_id: paper:2305.13712
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
---

Answer Uncertainty Disparity (AUD) is a semantic metric that quantifies how differently a model expresses uncertainty when responding to known versus unknown questions. It is computed as the normalized average difference across three linguistic features: subjectivity score, hedge-phrase frequency, and text-uncertainty vocabulary density. A higher AUD indicates that the model uses more hedged, uncertain language on questions it gets wrong than on questions it gets right, which is the desired calibration behaviour.

**Why it matters here:** AUD operationalizes the intuition that a well-calibrated model should sound different when it is out of its depth. It provides a surface-level signal for the epistemic-humility study that complements accuracy-based metrics, catching cases where a model hedges appropriately even if it does not formally abstain.

**Lineage:** proposed by [[2305.13712--kuq-knowledge-of-knowledge]] as the primary evaluation metric for the [[known-unknown-questions]] benchmark.
