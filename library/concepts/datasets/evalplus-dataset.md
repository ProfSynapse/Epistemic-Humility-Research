---
aliases:
- EvalPlus benchmark
- EvalPlus code generation
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:evalplus-dataset
  type: dataset
  status: canonical
area: datasets
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[valid-reasoning-rate]]'
- '[[gsm8k]]'
relationships:
- type: proposed_by
  target: '[[2605.21127--silent-reasoning-trace-suppression]]'
  target_id: paper:2605.21127
  confidence: high
- type: related_to
  target: '[[reasoning-trace-collapse]]'
  target_id: term:reasoning-trace-collapse
  confidence: medium
- type: related_to
  target: '[[valid-reasoning-rate]]'
  target_id: metric:valid-reasoning-rate
  confidence: medium
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
---

A code generation benchmark providing rigorous evaluation of LLMs for code correctness, extending HumanEval with additional test cases to reduce false positives. Used in Twist et al. 2026 as the out-of-domain code generation evaluation track alongside GSM8K (math).

**Why it matters here:** Provides an out-of-domain structural reasoning reliability measurement (VR on code tasks) separate from the in-domain Chemistry fine-tuning task, revealing whether reasoning-trace collapse generalizes beyond the training domain.

**Lineage:** Liu et al. 2023, NeurIPS. Used in Twist et al. 2026 (arXiv:2605.21127), Section 5.1.
