---
aliases:
- distractor prompting
- multiple-choice distractor format
- structured distractor prompt
- D-setting prompting
tags:
- kg/method
- concept
- method
kg:
  id: method:distractor-augmented-prompting
  type: method
  status: canonical
area: methods
related:
- '[[2502.11028--mind-the-confidence-gap]]'
- '[[simpleqa]]'
- '[[expected-calibration-error]]'
- '[[verbalized-confidence]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[llm-as-judge]]'
relationships:
- type: proposed_by
  target: '[[2502.11028--mind-the-confidence-gap]]'
  target_id: paper:2502.11028
  confidence: high
- type: related_to
  target: '[[simpleqa]]'
  target_id: dataset:simpleqa
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[llm-as-judge]]'
  target_id: method:llm-as-judge
  confidence: medium
---

A prompting strategy in which, alongside the question, the model is presented with the correct answer and a fixed number (typically three) of plausible but factually incorrect distractors in shuffled multiple-choice format. The model must select among options and provide a confidence score. Distractors are generated to match the answer type and remain distinct but similarly specific to the correct answer.

**Why it matters here:** Converts free-generation into a structured selection task, which substantially reduces ECE and increases accuracy across model families. The format reveals a calibration paradox: larger models benefit more in absolute calibration terms but are also more susceptible to distractor-induced errors, while smaller models gain more in accuracy but remain miscalibrated.

**Lineage:** Used by Chhikara (2025, arXiv 2502.11028) as the D-setting in a systematic calibration study of six LLMs on SimpleQA. Related to multiple-choice evaluation conventions in the broader QA literature.
