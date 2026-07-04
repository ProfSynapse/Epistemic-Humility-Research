---
aliases:
- TPR-GAP
- true positive rate gap
- GAP_TPR
- TPR-Gap
- GAP^TPR
- TPR-Gap Bias Metric
- TPR-GAP (True Positive Rate Gap)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:tpr-gap
  type: metric
  status: canonical
area: fairness
related:
- '[[bias-in-bios]]'
relationships:
- type: related_to
  target: '[[bias-in-bios]]'
  target_id: dataset:bias-in-bios
---

TPR-GAP (De-Arteaga et al. 2019) measures the disparity in true positive rates for a downstream classifier across protected groups such as gender. For a given profession y and protected group z, GAP^TPR_{y,z} is the difference between group-conditional true positive rates; the summary statistic GAP^TPR_RMS is the root-mean-square over all professions, capturing aggregate bias. Lower values indicate more equitable classifier performance across groups.

**Why it matters here:** TPR-GAP is the primary extrinsic bias metric used to evaluate whether concept-erasure methods actually reduce downstream discriminatory behaviour, complementing intrinsic probing-accuracy measures.

**Lineage:** used alongside [[weat]] to benchmark [[inlp]], [[rlace]], and [[leace]] on the [[bias-in-bios]] dataset.
