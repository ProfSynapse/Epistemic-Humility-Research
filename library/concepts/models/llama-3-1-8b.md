---
aliases:
- Llama-3.1-8B
- Llama 3.1 8B
tags:
- kg/model
- concept
- model
kg:
  id: model:llama-3-1-8b
  type: model
  status: canonical
area: models
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[llama-3-1-8b-instruct]]'
relationships:
- type: studied_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[llama-3-1-8b-instruct]]'
  target_id: model:llama-3-1-8b-instruct
  confidence: high
---

Llama 3.1 8B is an eight-billion-parameter member of Meta's Llama 3.1 family.
The paper uses it in its supervised adaptation comparison.

**Why it matters here:** It tests whether the proposed activation intervention
remains competitive at a larger model scale.

**Lineage:** It is the base-model counterpart of
[[llama-3-1-8b-instruct]].
