---
aliases:
- GSM-Danger
- GSM Danger
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:gsm-danger
  type: dataset
  status: canonical
area: safety
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[gsm8k]]'
- '[[directharm4]]'
relationships:
- type: related_to
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: variation_of
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: high
- type: related_to
  target: '[[directharm4]]'
  target_id: dataset:directharm4
  confidence: high
---

GSM-Danger formats harmful requests to resemble GSM8K math problems and appends an unsafe request. The paper uses it to test whether math fine-tuning erodes refusal behavior and whether weight steering restores that behavior.

**Why it matters here:** It probes safety behavior under a distribution that resembles the capability-training data.

**Lineage:** Introduced by Lyu et al. (2024) as a safety-oriented variation of [[gsm8k]].
