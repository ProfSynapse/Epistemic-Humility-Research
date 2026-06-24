---
aliases:
- Cosmos QA
- cosmos-qa
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:cosmosqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2401.12794--llm-uncertainty-bench-conformal]]'
- '[[conformal-prediction-for-llm-uncertainty]]'
- '[[hallucination]]'
- '[[mmlu]]'
relationships:
- type: proposed_by
  target: '[[2401.12794--llm-uncertainty-bench-conformal]]'
  target_id: paper:2401.12794
  confidence: high
- type: related_to
  target: '[[conformal-prediction-for-llm-uncertainty]]'
  target_id: method:conformal-prediction-for-llm-uncertainty
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
---

A reading comprehension dataset of approximately 35,000 examples focused on everyday narrative texts that require reasoning beyond the literal text span. Used in 2401.12794 as the RC task, with 10,000 instances sampled from train/dev sets and reformatted as 6-option multiple-choice questions.

**Why it matters here:** Benchmarks narrative commonsense reasoning; used as one of five tasks in the conformal prediction LLM uncertainty benchmark.

**Lineage:** Huang et al. (2019); used in 2401.12794.
