---
aliases:
- SciKnowEval Chemistry L-3
- Chemistry L-3 subset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:sciknoweval
  type: dataset
  status: canonical
area: datasets
related:
- '[[2605.21127--silent-reasoning-trace-suppression]]'
- '[[reasoning-trace-collapse]]'
- '[[gsm8k]]'
- '[[evalplus-dataset]]'
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
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: medium
- type: related_to
  target: '[[evalplus-dataset]]'
  target_id: dataset:evalplus-dataset
  confidence: medium
---

A comprehensive dataset for evaluating scientific knowledge of large language models, spanning multiple scientific domains and difficulty levels. The Chemistry L-3 subset is used as a fine-tuning and in-domain evaluation task in Twist et al. 2026: training responses contain explanations but no explicit reasoning delimiters.

**Why it matters here:** Provides a realistic non-math/non-code domain for studying reasoning-trace collapse during fine-tuning, enabling evaluation of domain transfer alongside structural reasoning reliability.

**Lineage:** Feng et al. 2025, NeurIPS AI for Science Workshop. Used in Twist et al. 2026 (arXiv:2605.21127), Section 5.1.
