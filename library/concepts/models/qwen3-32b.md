---
aliases:
- Qwen3-32B
- Qwen3 32B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen3-32b
  type: model
  status: canonical
area: models
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[knowledge-boundary]]'
relationships:
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A 32B-parameter hybrid reasoning model from the Qwen3 family (Qwen Team, 2025) whose reasoning can be toggled ON or OFF.

**Why it matters here:** As the least capable model in the sweep it shows the largest reasoning-effectiveness (Omega), and its pass@k nearly doubles with reasoning on SimpleQA-Verified. This is the clearest case that weaker models hold more hidden knowledge that reasoning unlocks.

**Lineage:** A member of the Qwen3 model family (Qwen Team, 2025).
