---
aliases:
- routing-content dependence shift
- operational routing-content handoff
tags:
- kg/term
- concept
- term
kg:
  id: term:routing-content-handoff
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[parameter-retrieval-routing]]'
- '[[activation-intervention]]'
- '[[decodability-steerability-gap]]'
relationships:
- type: proposed_by
  target: '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
  target_id: paper:2609.11859
  confidence: high
- type: related_to
  target: '[[parameter-retrieval-routing]]'
  target_id: term:parameter-retrieval-routing
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
- type: related_to
  target: '[[decodability-steerability-gap]]'
  target_id: term:decodability-steerability-gap
  confidence: medium
---

A routing-content handoff is an operational depth profile in which answers become less sensitive to deleting a fitted request-routing component while remaining sensitive to deleting fitted answer-supporting content. In arXiv:2609.11859, the result applies to the paper's global first-versus-second request direction and does not generalize to every request representation.

**Why it matters here:** The term forces a claimed handoff to name the direction, center, intervention norm, model, task, and layer sets that define it.

**Lineage:** It combines causal [[activation-intervention]] evidence on [[parameter-retrieval-routing]] and fitted content rather than inferring a stage boundary from readability alone.
