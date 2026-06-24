---
aliases:
- CQA
- CarnaticQA
- Carnatic Music QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:carnatic-qa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.16221--abstainqa]]'
- '[[abstain-qa-dataset]]'
- '[[abstention]]'
- '[[unanswerable-questions]]'
- '[[knowledge-boundary]]'
- '[[over-abstention]]'
relationships:
- type: proposed_by
  target: '[[2407.16221--abstainqa]]'
  target_id: paper:2407.16221
  confidence: high
- type: related_to
  target: '[[abstain-qa-dataset]]'
  target_id: dataset:abstain-qa-dataset
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
- type: related_to
  target: '[[unanswerable-questions]]'
  target_id: term:unanswerable-questions
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[over-abstention]]'
  target_id: term:over-abstention
  confidence: medium
---

A 900-question expert-validated MCQA dataset for the under-represented domain of Carnatic classical music, constructed from a web-scraped list of 930 ragas reduced to 272 by two expert annotators. Nine task templates (e.g., raga recognition, property identification) each generate 100 questions; data quality was verified by three Carnatic musician volunteers via majority voting.

**Why it matters here:** Serves as the primary under-represented domain test in Abstain-QA, where models lack pre-training coverage and show extreme abstention failures under Base prompting. Its use demonstrates that domain familiarity is a first-order determinant of abstention ability, independent of prompting strategy.

**Lineage:** Created as part of 2407.16221; grounded in theoretical Carnatic music knowledge; expert annotation from full-time workers compensated at local wages.
