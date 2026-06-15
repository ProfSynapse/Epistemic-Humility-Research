---
aliases:
- TruthfulQA benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:truthfulqa
  type: dataset
  status: canonical
area: datasets
---

TruthfulQA is an 817-question benchmark designed to test whether language models produce truthful answers or instead mimic common human falsehoods and misconceptions. Each question targets a category where plausible-sounding wrong answers exist, so a model that has memorized human writing patterns tends to fail even when a correct answer is available.

**Why it matters here:** InstructGPT evaluations use TruthfulQA to surface calibration differences between RLHF-tuned models and base models, and the dataset appears in the alignment-tax analysis as a domain where instruction-tuned models can improve on truthfulness at the cost of other benchmark performance.

**Lineage:** no formal lineage edges; stands alone as an evaluation benchmark.
