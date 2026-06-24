---
aliases:
- OEQ dataset
- open-ended advice queries
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:oeq-advice-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2505.13995--elephant-social-sycophancy]]'
- '[[elephant-benchmark]]'
- '[[sycophancy]]'
- '[[social-sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2505.13995--elephant-social-sycophancy]]'
  target_id: paper:2505.13995
  confidence: high
- type: related_to
  target: '[[elephant-benchmark]]'
  target_id: method:elephant-benchmark
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[social-sycophancy]]'
  target_id: term:social-sycophancy
  confidence: medium
---

A dataset of 3,027 prompt-answer pairs of open-ended personal advice queries paired with human responses, covering five topic clusters: romantic relationships, emotional fatigue, social disconnections, existential dilemmas, and identity and growth. Constructed by aggregating data from multiple human-vs-LLM advice studies, embedding with Sentence-BERT, and clustering with BERTopic.

**Why it matters here:** Enables comparison of LLM vs. human face-preserving behaviors in naturalistic advice contexts without requiring a verifiable ground truth, filling a gap left by propositional sycophancy benchmarks.

**Lineage:** Introduced in Cheng et al. (2505.13995) as part of the ELEPHANT framework; source advice queries drawn from Howe et al. (2023), Kuosmanen (2024), Hou et al. (2024), and AdvisorQA.
