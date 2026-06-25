---
aliases:
- Gemini-2.5-Flash
- Gemini 2.5 Flash
tags:
- kg/model
- concept
- model
kg:
  id: model:gemini-2-5-flash
  type: model
  status: canonical
area: models
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[gemini-2-5-pro]]'
relationships:
- type: related_to
  target: '[[gemini-2-5-pro]]'
  target_id: model:gemini-2-5-pro
  confidence: high
---

A hybrid reasoning model from the Gemini 2.5 family (Comanici et al., 2025) whose reasoning can be toggled ON or OFF. It is the primary model for this paper's compute-heavy controlled experiments because of its latency-quality tradeoff, and it also serves as the search-enabled autorater and fact verifier.

**Why it matters here:** Its toggleable reasoning makes it the workhorse for isolating reasoning's effect on parametric recall while holding parametric knowledge fixed. As a verifier with search it underpins the large-scale hallucination audit (estimated verification accuracy near 100% on human-checked items).

**Lineage:** A member of the Gemini 2.5 family alongside [[gemini-2-5-pro]] (Comanici et al., 2025).
