---
aliases:
- Gemini-2.5-Pro
- Gemini 2.5 Pro
tags:
- kg/model
- concept
- model
kg:
  id: model:gemini-2-5-pro
  type: model
  status: canonical
area: models
related:
- '[[2603.09906--thinking-recall-how-reasoning-unlocks-parametric-knowledge]]'
- '[[gemini-2-5-flash]]'
relationships:
- type: related_to
  target: '[[gemini-2-5-flash]]'
  target_id: model:gemini-2-5-flash
  confidence: high
---

A hybrid reasoning model from the Gemini 2.5 family (Comanici et al., 2025) whose reasoning can be toggled ON or OFF. It is the most capable model evaluated in this paper for the parametric-recall boundary experiments.

**Why it matters here:** As the strongest model in the sweep it shows the smallest reasoning-effectiveness (Omega), supporting the finding that more capable models already recall parametric knowledge well and so benefit less from reasoning. On the complex-question subset its reasoning benefit is not even guaranteed (95% CI crosses zero).

**Lineage:** A member of the Gemini 2.5 family alongside [[gemini-2-5-flash]] (Comanici et al., 2025).
