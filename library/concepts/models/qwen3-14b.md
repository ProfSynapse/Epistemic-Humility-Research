---
aliases:
- Qwen3-14B
- Qwen 3 14B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen3-14b
  type: model
  status: canonical
area: models
related:
- '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
- '[[qwen3]]'
relationships:
- type: studied_by
  target: '[[2607.11871--inside-unfair-judge-mechanistic-interpretability-account-llm]]'
  target_id: paper:2607.11871
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: high
---

Qwen3-14B is a 14-billion-parameter member of the Qwen3 model family. Xu et al. use it as one of three white-box LLM judges for activation geometry and cross-architecture replication.

**Why it matters here:** It tests whether the recovered judge-bias subspace is specific to the primary Llama model or also appears in another architecture and parameter scale.

**Lineage:** A mid-scale checkpoint in the [[qwen3]] family.
