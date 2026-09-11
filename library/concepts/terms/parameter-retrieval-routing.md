---
aliases:
- parameter routing
- parameter-retrieval-routing candidate
- request-to-parameter routing
tags:
- kg/term
- concept
- term
kg:
  id: term:parameter-retrieval-routing
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[activation-intervention]]'
- '[[factual-association-recall-mechanism]]'
- '[[object-selection-routing]]'
- '[[routing-content-handoff]]'
relationships:
- type: proposed_by
  target: '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
  target_id: paper:2609.11859
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
  confidence: high
- type: related_to
  target: '[[object-selection-routing]]'
  target_id: term:object-selection-routing
  confidence: high
- type: related_to
  target: '[[routing-content-handoff]]'
  target_id: term:routing-content-handoff
  confidence: high
---

Parameter-retrieval routing is hidden-state information that specifies which fact subsequent computation should retrieve from model parameters. Wei et al. operationalize it with request-related directions whose fitted content and supplied-record selection components have been removed, then test the remaining direction through deletion and reversal interventions.

**Why it matters here:** It separates a query feature that is merely readable from a component that causally steers later factual content or the answer.

**Lineage:** It is one part of the broader [[factual-association-recall-mechanism]] and is functionally distinct from [[object-selection-routing]], which selects among contents already available in a hidden state.
