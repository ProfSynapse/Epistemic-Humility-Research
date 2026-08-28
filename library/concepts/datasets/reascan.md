---
aliases:
- ReaSCAN
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:reascan
  type: dataset
  status: canonical
area: datasets
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
relationships:
- type: proposed_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: medium
---

ReaSCAN is a grounded-language benchmark in which a model maps a natural-language command and a grid world to an action sequence. Its splits test systematic generalization to novel attribute and action compositions.

**Why it matters here:** ReaSCAN tests whether causal-structure training transfers beyond the combinations seen during training.

**Lineage:** The benchmark builds on SCAN and gSCAN.
