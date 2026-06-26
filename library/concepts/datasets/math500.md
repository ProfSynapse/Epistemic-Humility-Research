---
aliases:
- MATH500 benchmark
- MATH 500
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:math500
  type: dataset
  status: canonical
area: datasets
related: []
relationships: []
---

A 500-problem subset of the MATH competition benchmark spanning seven mathematical domains (algebra, counting and probability, geometry, intermediate algebra, number theory, pre-algebra, and precalculus). Problems are drawn from the full MATH dataset and are widely used for evaluating inference-time scaling and mathematical reasoning in large language models. In the sequence-probability correctness study (2606.27359), MATH500 is the only benchmark where within-sample log-probability and correctness correlations average positive across evaluated methods, suggesting domain structure interacts with how sequence probability tracks correctness.

**Why it matters here:** The anomalous positive within-sample correlation on MATH500 compared to other benchmarks provides a calibration-relevant signal: math problems may have distributional properties that make internal probability a more reliable confidence indicator than in open-ended or knowledge-recall tasks.

**Lineage:** no direct predecessors encoded in this graph.
