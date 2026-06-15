---
aliases:
- ECE
- mean absolute deviation calibration error
- calibration error
- Expected Calibration Error (ECE)
- ECE-t
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:expected-calibration-error
  type: metric
  status: canonical
area: metrics
related:
- '[[calibration]]'
- '[[brier-score]]'
- '[[auroc]]'
relationships:
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
---

Expected Calibration Error (ECE) is the mean absolute difference between a
model's predicted confidence and the empirical accuracy of its predictions,
computed by grouping predictions into equal-frequency bins (typically 10) and
averaging the bin-level gaps. It is a scalar summary of miscalibration: a
perfectly calibrated model scores 0, and larger values indicate systematic over-
or under-confidence.

**Why it matters here:** ECE is one of the primary calibration diagnostics used
to evaluate whether SFT, DPO, or KTO training changes how well a model's
expressed confidence tracks its actual correctness on abstention-relevant questions.

**Lineage:** related to [[calibration]] as its dominant scalar estimator; compare
[[brier-score]], which adds a sharpness component, and [[auroc]], which measures
discriminative power without penalising calibration directly.
