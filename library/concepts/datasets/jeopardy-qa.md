---
aliases:
- Jeopardy
- Jeopardy dataset
- Jeopardy Kaggle
- jeopardy question-answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:jeopardy-qa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2404.00474--linguistic-calibration-long-form]]'
- '[[triviaqa]]'
- '[[linguistic-calibration-lc]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2404.00474--linguistic-calibration-long-form]]'
  target_id: paper:2404.00474
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[linguistic-calibration-lc]]'
  target_id: method:linguistic-calibration-lc
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

A Kaggle-hosted dataset of Jeopardy! clue-answer pairs used in Band et al. (2024) as an out-of-distribution QA evaluation for models trained on TriviaQA. Questions are in the distinctive Jeopardy answer-first format, making it a distribution shift from standard trivia-style questions.

**Why it matters here:** Serves as an OOD generalization probe for calibration transfer: a model trained on TriviaQA is tested without fine-tuning on Jeopardy-format questions. Strong forecast ECE on this dataset supports the claim that the LC training objective generalizes across question-answering distribution shifts.

**Lineage:** Kaggle (2020); used as OOD evaluation in Band et al. (2024) LC framework
