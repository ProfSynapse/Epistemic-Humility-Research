---
aliases:
- Physical Intuition QA
- Physical Interaction Question Answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:piqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2311.09410--llm-sycophantic-behaviour]]'
- '[[sycophancy]]'
- '[[openbookqa]]'
- '[[non-contradiction-benchmark]]'
relationships:
- type: proposed_by
  target: '[[2311.09410--llm-sycophantic-behaviour]]'
  target_id: paper:2311.09410
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[openbookqa]]'
  target_id: dataset:openbookqa
  confidence: medium
- type: related_to
  target: '[[non-contradiction-benchmark]]'
  target_id: dataset:non-contradiction-benchmark
  confidence: medium
---

A multiple-choice question-answering benchmark (Bisk et al. 2019) consisting of everyday physical situations paired with a typical and an atypical solution. Tests physical commonsense reasoning.

**Why it matters here:** One of four QA benchmarks used in Ranaldi and Pucci 2023 to probe self-confidence sycophancy under human-influenced hint prompts.

**Lineage:** Bisk et al. 2019; used in Ranaldi and Pucci 2023 (arXiv:2311.09410).
