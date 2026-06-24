---
aliases:
- OpenBookQA
- OBQA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:openbookqa
  type: dataset
  status: canonical
area: datasets
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[mmlu]]'
- '[[hellaswag]]'
- '[[truthfulqa]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[pretrained-distribution-temperature-scaling]]'
relationships:
- type: proposed_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[hellaswag]]'
  target_id: dataset:hellaswag
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
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
  target: '[[pretrained-distribution-temperature-scaling]]'
  target_id: method:pretrained-distribution-temperature-scaling
  confidence: medium
---

A multiple-choice question-answering dataset (Mihaylov et al. 2018) requiring the application of core science facts in combination with broad common knowledge. Each question has four answer choices and a corresponding open-book core science fact.

**Why it matters here:** One of the seven MCQ benchmarks used for calibration evaluation in He et al. 2023; specifically highlighted as a case where standard TS and KDE both perform worse than out-of-the-box calibration, making it a hard case for few-shot post-hoc calibration.

**Lineage:** Mihaylov et al. 2018; used in He et al. 2023 (arXiv:2310.11732) for post-hoc calibration evaluation.
