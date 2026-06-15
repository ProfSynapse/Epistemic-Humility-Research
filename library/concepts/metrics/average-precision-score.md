---
aliases:
- AP score
- Average Precision
- Average Precision (AP) Score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:average-precision-score
  type: metric
  status: canonical
area: metrics
---

Average Precision (AP) ranks a model's predictions by confidence from highest to
lowest and computes the area under the resulting precision-recall curve. A model
scores high only when it simultaneously places correct answers at high confidence
and incorrect or unknown answers at low confidence, capturing the full
precision-recall tradeoff in a single scalar.

**Why it matters here:** In R-Tuning and related abstention studies, AP measures
how well a model orders its willingness to answer relative to its actual
correctness, making it more informative than a single operating-point metric like
raw abstention rate or accuracy alone.

**Lineage:** a standard retrieval-derived metric applied to the selective-answer
setting; no direct lineage to other atoms in this vault.
