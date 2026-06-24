---
aliases:
- Natural Questions dataset
- NQ
- Google Natural Questions
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:natural-questions
  type: dataset
  status: canonical
area: datasets
related:
- '[[2410.06913--craft]]'
- '[[triviaqa]]'
- '[[refusal-aware-instruction-tuning]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2410.06913--craft]]'
  target_id: paper:2410.06913
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[refusal-aware-instruction-tuning]]'
  target_id: method:refusal-aware-instruction-tuning
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A large-scale open-domain question-answering dataset introduced by Kwiatkowski et al. (2019) consisting of naturally occurring Google search queries paired with Wikipedia-sourced answers. It tests factual recall over a broad range of topics and difficulty levels.

**Why it matters here:** Natural Questions is used in the CRaFT paper as the secondary OEQA evaluation dataset alongside TriviaQA; the Cor-RAIT accuracy drop from 24.65% to 15.93% motivates the over-refusal problem. It is a standard factoid QA testbed for abstention studies.

**Lineage:** Kwiatkowski et al. 2019; used alongside triviaqa in refusal-aware and abstention studies
