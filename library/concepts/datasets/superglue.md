---
aliases:
- SuperGLUE
- SuperGLUE benchmark
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:superglue
  type: dataset
  status: canonical
area: datasets
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[mmlu]]'
- '[[arc-challenge]]'
relationships:
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[arc-challenge]]'
  target_id: dataset:arc-challenge
  confidence: medium
---

SuperGLUE is a natural-language-understanding benchmark suite covering tasks such as textual entailment, commonsense reasoning, and question answering. In this paper it is one of the 10 held-out evaluation datasets used to test faithful-calibration generalization.

**Why it matters here:** Broad NLU suites help detect whether calibration or uncertainty-expression methods transfer beyond the open-domain QA datasets often used for abstention work.

**Lineage:** A successor benchmark suite to GLUE and a complement to broad multitask evaluation datasets such as [[mmlu]].
