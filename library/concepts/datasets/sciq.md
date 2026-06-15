---
aliases:
- science QA
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:sciq
  type: dataset
  status: canonical
area: datasets
related:
- '[[triviaqa]]'
- '[[mmlu]]'
relationships:
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
---

SciQ is a crowdsourced dataset of approximately 14,000 multiple-choice
science-exam questions (biology, chemistry, physics, earth science) each paired
with a correct answer and three distractors. Questions were crowd-sourced from
science textbooks and exams, then validated by additional annotators.

**Why it matters here:** SciQ serves as a factual QA benchmark for calibration
evaluation, testing whether a model's verbalized confidence tracks accuracy
on domain-specific factual recall rather than general world knowledge alone.

**Lineage:** related to [[triviaqa]] and [[mmlu]] as factual QA calibration
benchmarks, but narrower in scope (school-level science) and multiple-choice in
format.
