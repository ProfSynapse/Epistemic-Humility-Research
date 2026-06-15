---
aliases:
- BS
- BS-t
- Brier
- MSE calibration
- mean squared error calibration
- Brier Score (MSE)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:brier-score
  type: metric
  status: canonical
area: metrics
related:
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[calibration]]'
relationships:
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

The Brier Score is the mean squared error between a model's assigned probability
and the binary outcome of whether its answer was correct, referred to as MSE in
several calibration papers. It combines calibration error (are probabilities
accurate on average?) with sharpness (are probabilities spread out, not bunched
near 0.5?), so a model can reduce its Brier Score either by improving accuracy
or by expressing sharper, better-placed confidence.

**Why it matters here:** The Brier Score provides a joint view of calibration
and sharpness in the abstention study, complementing [[expected-calibration-error]]
(which isolates mean deviation) and [[auroc]] (which isolates ranking) when
assessing whether preference training yields genuinely better self-knowledge.

**Lineage:** related to [[expected-calibration-error]], which isolates the
calibration component via mean absolute deviation; related to [[auroc]], which
measures only ranking quality and is insensitive to absolute probability values.
