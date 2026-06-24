---
aliases:
- GPQA
- Graduate-Level Google-Proof Q&A
- GPQA Diamond
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:gpqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.18183--reasoning-models-dont-know]]'
- '[[mmlu]]'
- '[[strategyqa]]'
- '[[simpleqa]]'
- '[[arc-challenge]]'
- '[[overconfidence]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2506.18183--reasoning-models-dont-know]]'
  target_id: paper:2506.18183
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[strategyqa]]'
  target_id: dataset:strategyqa
  confidence: medium
- type: related_to
  target: '[[simpleqa]]'
  target_id: dataset:simpleqa
  confidence: medium
- type: related_to
  target: '[[arc-challenge]]'
  target_id: dataset:arc-challenge
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A multiple-choice QA benchmark of questions determined to be challenging even for PhD-level domain experts, designed to resist lookup via search engines. Questions span biology, chemistry, and physics at graduate research level.

**Why it matters here:** One of the primary challenging benchmarks used to evaluate reasoning model calibration; models that achieve high accuracy on MMLU often exhibit severe overconfidence on GPQA, making it a useful probe of calibration in the presence of genuine domain difficulty.

**Lineage:** Introduced by Rein et al. (2023), arXiv:2311.12022. Used in arXiv:2506.18183 to document inference-time scaling effects on calibration.
