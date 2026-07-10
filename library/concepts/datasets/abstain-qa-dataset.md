---
aliases:
- Abstain QA benchmark
- AbstainQA evaluation dataset
- 2407.16221 Abstain-QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:abstain-qa-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2407.16221--abstainqa]]'
- '[[popqa]]'
- '[[mmlu]]'
- '[[carnatic-qa]]'
- '[[abstention]]'
- '[[unanswerable-questions]]'
- '[[answerable-unanswerable-confusion-matrix]]'
relationships:
- type: proposed_by
  target: '[[2407.16221--abstainqa]]'
  target_id: paper:2407.16221
  confidence: high
- type: related_to
  target: '[[popqa]]'
  target_id: dataset:popqa
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[carnatic-qa]]'
  target_id: dataset:carnatic-qa
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
  target: '[[answerable-unanswerable-confusion-matrix]]'
  target_id: metric:answerable-unanswerable-confusion-matrix
  confidence: medium
---

A 2900-sample zero-shot MCQA evaluation benchmark for LLM abstention ability, combining Pop-QA (1000 questions), MMLU (1000 questions), and Carnatic-QA (900 questions) with an equal answerable/unanswerable split. Unanswerable items are created by replacing the correct option with a plausible distractor; every question carries an explicit IDK/None-of-the-Above option. Evaluated under three abstain-clause types and three task-prompt regimes.

**Why it matters here:** Provides the empirical substrate for the AUCM-based evaluation of abstention ability, covering well-represented factoid (PopQA), multi-domain reasoning (MMLU), and under-represented expert-knowledge (CQA) question types, which maps directly onto the coverage requirements for locked training-regimen experiment evaluation.

**Lineage:** Proposed in 2407.16221; combines PopQA (Mallen et al. 2023), MMLU (Hendrycks et al. 2020), and the newly created Carnatic-QA; distinct from the AbstainQA task formulation (term:abstain-qa) defined in 2402.00367.
