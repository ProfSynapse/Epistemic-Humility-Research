---
aliases:
- PubMedQA
- PubMed question answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:pubmedqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[gpqa]]'
relationships:
- type: evaluation_set_for
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[gpqa]]'
  target_id: dataset:gpqa
  confidence: medium
---

PubMedQA is a biomedical question-answering benchmark built from PubMed abstracts. It tests whether a system can reason over scientific evidence to answer research questions.

**Why it matters here:** Xu et al. sample 500 PubMedQA questions as one of nine domains used to test whether LLM judge bias depends on subject matter.

**Lineage:** A biomedical evaluation domain complementary to the broader scientific reasoning questions in [[gpqa]].
