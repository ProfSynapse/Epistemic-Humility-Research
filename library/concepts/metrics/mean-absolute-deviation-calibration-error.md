---
aliases:
- MAD calibration error
- MAD
- Mean Absolute Deviation Calibration Error (MAD)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:mean-absolute-deviation-calibration-error
  type: metric
  status: canonical
area: metrics
related:
- '[[brier-score]]'
- '[[expected-calibration-error]]'
relationships:
- type: related_to
  target: '[[brier-score]]'
  target_id: metric:brier-score
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
---

Mean Absolute Deviation Calibration Error (MAD) estimates miscalibration by
binning model predictions by stated confidence, then averaging the absolute
difference between mean confidence and mean empirical accuracy within each bin.
Unlike squared-error variants (MSE, Brier score), MAD weighs all bins equally
in absolute terms, making it less sensitive to a few very miscalibrated bins and
easier to interpret as an average percentage-point deviation.

**Why it matters here:** Used alongside [[brier-score]] and
[[expected-calibration-error]] to evaluate whether verbalized probabilities are
well-calibrated in the finetuning-for-uncertainty paradigm, providing a
complementary view of calibration quality that is robust to outlier bins.

**Lineage:** related to [[brier-score]] (a squared-error calibration metric) and
[[expected-calibration-error]] (a standard binned calibration metric); all three
measure alignment between stated confidence and observed accuracy from different
loss perspectives.
