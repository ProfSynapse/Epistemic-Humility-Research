---
aliases:
- TinyMMLU
- Tiny MMLU
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:tiny-mmlu
  type: dataset
  status: canonical
area: datasets
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[mmlu]]'
relationships:
- type: related_to
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: derived_from
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: high
---

TinyMMLU is a compact multiple-choice benchmark designed to approximate MMLU performance with fewer examples. The paper uses chain-of-thought TinyMMLU accuracy as a narrow general-capability check while steering Qwen2.5-7B-Instruct toward evil answers.

**Why it matters here:** It tests whether behavioral control occurs before a visible loss of general benchmark performance.

**Lineage:** Introduced by Polo et al. (2024) as a reduced evaluation derived from [[mmlu]].
