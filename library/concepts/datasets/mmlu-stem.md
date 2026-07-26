---
aliases:
- MMLU-STEM
- MMLU STEM subset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:mmlu-stem
  type: dataset
  status: canonical
area: datasets
related:
- '[[mmlu]]'
relationships:
- type: variation_of
  target: '[[mmlu]]'
  target_id: dataset:mmlu
---

MMLU-STEM is the science/technology/engineering/mathematics subset of the MMLU benchmark, isolating quantitative and technical-reasoning questions from the full 57-subject suite.

**Why it matters here:** [[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] uses MMLU-STEM (n=300) as a cross-domain replication set for its Overthinking steering null result, showing the classification-correction gap generalizes beyond medical QA.

**Lineage:** a topical subset of [[mmlu]].
