---
aliases:
- Causal Abstraction
- causal abstraction relationship
tags:
- kg/term
- concept
- term
kg:
  id: term:causal-abstraction
  type: term
  status: canonical
area: terms
related:
- '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
- '[[causal-intervention]]'
relationships:
- type: proposed_by
  target: '[[2112.00826--inducing-causal-structure-interpretable-neural-networks]]'
  target_id: paper:2112.00826
  confidence: medium
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
  confidence: high
---

A causal abstraction is a mapping under which aligned interventions in a low-level model and a high-level model have corresponding effects. It permits the high-level model to serve as a faithful description of the low-level model's causal organization.

**Why it matters here:** An answerability representation must affect downstream behavior in the intended way if it is to support a causal rather than merely correlational account.

**Lineage:** This paper applies constructive causal-abstraction theory to neural representations and training.
