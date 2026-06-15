---
aliases:
- area under the ROC curve
- AUC-ROC
- Area Under the ROC Curve
- failure prediction AUROC
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:auroc
  type: metric
  status: canonical
area: metrics
related:
- '[[expected-calibration-error]]'
- '[[brier-score]]'
- '[[calibration]]'
relationships:
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

AUROC (Area Under the Receiver Operating Characteristic Curve) measures how
well a confidence score ranks correctly answered questions above incorrectly
answered ones, irrespective of the absolute probability values. It equals the
probability that a randomly chosen correct answer receives a higher score than a
randomly chosen incorrect one; chance performance is 0.5 and a perfect
discriminator scores 1.0.

**Why it matters here:** AUROC isolates the ranking quality of self-knowledge
signals such as [[p-ik]] and [[p-true]], showing whether a model that is
miscalibrated in absolute terms can still reliably identify which questions it
does or does not know, a key property for abstention.

**Lineage:** related to [[expected-calibration-error]] and [[brier-score]];
while ECE captures absolute probability accuracy and Brier Score combines both,
AUROC captures only discriminative ordering.
