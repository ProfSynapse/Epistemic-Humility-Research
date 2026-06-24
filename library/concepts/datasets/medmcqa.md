---
aliases:
- MedMCQA dataset
- Medical MCQA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:medmcqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2601.20126--rewarding-intellectual-humility]]'
- '[[math-benchmark]]'
- '[[abstention]]'
- '[[hallucination]]'
- '[[ternary-reward-design]]'
relationships:
- type: proposed_by
  target: '[[2601.20126--rewarding-intellectual-humility]]'
  target_id: paper:2601.20126
  confidence: high
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[ternary-reward-design]]'
  target_id: method:ternary-reward-design
  confidence: medium
---

A large-scale multiple-choice question-answering dataset derived from real-world Indian medical entrance exams (AIIMS and NEET-PG), covering 21 medical subjects with four answer options per question and verified ground-truth labels. It is used to benchmark both answer accuracy and abstention behavior in high-stakes domain QA.

**Why it matters here:** MedMCQA is one of the two evaluation benchmarks in this paper and provides the primary MCQ abstention sweep results. Because it has verified ground truths and a structured option format, the IDK option can be added as a fifth choice and abstention can be scored automatically, making it well-suited for ternary-reward RLVR experiments.

**Lineage:** Introduced by Pal et al. (2022); used here by appending an explicit IDK option to the standard four-choice format to enable abstention evaluation.
