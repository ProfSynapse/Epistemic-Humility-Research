---
aliases:
- Clustering-derived calibration targets
- cluster-accuracy calibration targets
tags:
- kg/method
- concept
- method
kg:
  id: method:clustering-derived-calibration-target
  type: method
  status: canonical
area: methods
related:
- '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
- '[[apricot]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2403.05973--calibrating-large-language-models-using-their-generations]]'
  target_id: paper:2403.05973
  confidence: high
- type: related_to
  target: '[[apricot]]'
  target_id: method:apricot
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A procedure for setting confidence/calibration targets without access to LLM
likelihoods or internals: embed questions with a lightweight sentence model,
normalize along the feature dimension, cluster with HDBSCAN into topically
similar sets, and define each input's target as the target LLM's observed
accuracy over its cluster. It mirrors ECE's group-then-measure-group-accuracy
logic but groups by embedding similarity rather than by confidence bins, yielding
graded rather than binary targets.

**Why it matters here:** It is the insight that makes a purely black-box auxiliary
calibrator trainable — it manufactures graded calibration targets from
generations alone — and the ablation that fine-grained cluster targets beat
binary correct/incorrect targets is directly relevant to choosing a regression
target for a confidence head.

**Lineage:** Ulmer et al. 2024; grounded in ECE binning (Naeini et al. 2015; Guo
et al. 2017) and Holtgen and Williamson 2023; the target-generation half of
[[apricot]].
