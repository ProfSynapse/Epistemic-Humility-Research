---
aliases:
- three-perspective abstention framework
- abstention-aware workflow
- Abstention Framework (Query / Model / Human Values)
tags:
- kg/method
- concept
- method
kg:
  id: method:abstention-framework-query-model-values
  type: method
  status: canonical
area: methods
related:
- '[[2407.18418--know-your-limits-abstention-survey]]'
- '[[abstention]]'
relationships:
- type: proposed_by
  target: '[[2407.18418--know-your-limits-abstention-survey]]'
  target_id: paper:2407.18418
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

This formal framework decomposes the decision to abstain into three orthogonal conditions: query answerability a(x), model confidence c(x,y), and human value alignment h(x,y). A system abstains when any one of these conditions falls below a designer-specified threshold, making it possible to attribute abstention failures to their precise source (unanswerable query, uncertain model, or value mismatch) rather than treating abstention as a monolithic output behavior.

**Why it matters here:** The framework supplies a principled vocabulary for diagnosing over-abstention and under-abstention separately by condition, which is directly relevant to comparing SFT, DPO, and KTO training regimes that may produce different failure modes across the three conditions.

**Lineage:** related to [[abstention]]; proposed in the abstention survey (2407.18418).
