---
aliases:
- SycophancyEval
- sycophancy-eval dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:sycophancy-eval
  type: dataset
  status: canonical
area: datasets
related:
- '[[2310.13548--towards-understanding-sycophancy]]'
- '[[sycophancy]]'
- '[[truthfulqa]]'
- '[[triviaqa]]'
- '[[mmlu]]'
- '[[math-benchmark]]'
- '[[reinforcement-learning-from-human-feedback]]'
relationships:
- type: proposed_by
  target: '[[2310.13548--towards-understanding-sycophancy]]'
  target_id: paper:2310.13548
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[truthfulqa]]'
  target_id: dataset:truthfulqa
  confidence: medium
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: medium
- type: related_to
  target: '[[mmlu]]'
  target_id: dataset:mmlu
  confidence: medium
- type: related_to
  target: '[[math-benchmark]]'
  target_id: dataset:math-benchmark
  confidence: medium
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: medium
---

An evaluation suite introduced by Sharma et al. (2023) to measure sycophancy in AI assistants across three types: feedback sycophancy (three domains: math solutions, arguments, poems), Are-you-sure sycophancy (five QA datasets: MMLU, MATH, AQuA, TruthfulQA, TriviaQA), and mimicry sycophancy (poem misattribution). All tasks use open-ended free-form generation rather than multiple-choice.

**Why it matters here:** The first broad open-ended benchmark for sycophancy covering feedback, answer retraction, and mimicry, enabling comparisons across five production AI assistants and across training interventions. locked training-regimen evaluation can use it to track sycophancy type before and after each training arm.

**Lineage:** Extends Perez et al. (2022) and Wei et al. (2023b) beyond multiple-choice to free-form generation. Code and datasets released at https://github.com/meg-tong/sycophancy-eval.
