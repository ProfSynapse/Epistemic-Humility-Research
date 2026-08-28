---
aliases:
- MNIST Pointer-Value Retrieval
- MNIST-PVR
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mnist-pvr
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

MNIST-PVR is a visual reasoning benchmark with four handwritten digits arranged in a grid. The upper-left digit points to one of the other positions, and the model must return the selected digit under a systematic train-test split.

**Why it matters here:** The benchmark provides a clear high-level causal structure for testing whether internal representations implement a designated computation.

**Lineage:** It is built from MNIST images and a pointer-value retrieval task.
