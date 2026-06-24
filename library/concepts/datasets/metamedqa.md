---
aliases:
- Meta Med QA
- Medical Metacognition QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:metamedqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2510.05126--metacognition-uncertainty-communication]]'
- '[[truthfulqa]]'
- '[[legalbench]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[knowledge-boundary]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2510.05126--metacognition-uncertainty-communication]]'
  target_id: paper:2510.05126
  confidence: high
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[legalbench]]'
  target_id: dataset:legalbench
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A medical reasoning benchmark of 1,373 multiple-choice clinical vignette questions with six response options per item: four plausible medical diagnoses or interventions, a 'don't know' option, and a 'none of the above' option, where some questions have no correct answer among the first four, requiring models to recognize knowledge limits.

**Why it matters here:** Explicitly tests whether LLMs can recognize their own uncertainty in high-stakes clinical contexts; prior work using MetaMedQA argued that LLMs lack reliable metacognitive abilities for medical reasoning, making it a critical out-of-domain test for any calibration or abstention intervention.

**Lineage:** Introduced as a metacognitive medical reasoning dataset to probe whether LLMs can express appropriate uncertainty in clinical decision-making.
