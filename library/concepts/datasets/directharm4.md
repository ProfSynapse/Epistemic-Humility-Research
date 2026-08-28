---
aliases:
- DirectHarm4
- Direct Harm 4
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:directharm4
  type: dataset
  status: canonical
area: safety
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[gsm-danger]]'
relationships:
- type: related_to
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: related_to
  target: '[[gsm-danger]]'
  target_id: dataset:gsm-danger
  confidence: high
---

DirectHarm4 is a safety evaluation set of direct imperative requests for harmful assistance. The paper measures whether refusal behavior eroded by GSM8K fine-tuning can be restored on these requests.

**Why it matters here:** It tests behavioral repair after task-specific fine-tuning on an explicit harmful-request distribution.

**Lineage:** Reused from Lyu et al. (2024) alongside [[gsm-danger]].
