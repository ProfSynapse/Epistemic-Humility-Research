---
aliases:
- Social IQa
- Social Interaction QA
- Social Interaction Question Answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:siqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2311.09410--llm-sycophantic-behaviour]]'
- '[[sycophancy]]'
- '[[openbookqa]]'
- '[[piqa]]'
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
  target: '[[piqa]]'
  target_id: dataset:piqa
  confidence: medium
---

A multiple-choice commonsense reasoning benchmark (Sap et al. 2019) focused on reasoning about people's actions and social implications, covering a range of social situations with plausible and implausible answer candidates.

**Why it matters here:** One of four QA benchmarks used in Ranaldi and Pucci 2023 to probe self-confidence sycophancy under human-influenced hint prompts.

**Lineage:** Sap et al. 2019; used in Ranaldi and Pucci 2023 (arXiv:2311.09410).
