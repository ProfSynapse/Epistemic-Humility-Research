---
aliases:
- hidden-state routing
- object selection
- selection among available factual contents
tags:
- kg/term
- concept
- term
kg:
  id: term:object-selection-routing
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[linear-probe]]'
- '[[activation-intervention]]'
- '[[parameter-retrieval-routing]]'
relationships:
- type: proposed_by
  target: '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
  target_id: paper:2609.11859
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
- type: related_to
  target: '[[parameter-retrieval-routing]]'
  target_id: term:parameter-retrieval-routing
  confidence: high
---

Object-selection routing is the function of choosing which of multiple candidate contents already represented in a hidden state controls the answer. The paper also calls this hidden-state routing and tests it with supplied-marker calibration, transferred selection directions, and direct selection readouts.

**Why it matters here:** It prevents an answer-changing internal edit from being misread as evidence that two candidate facts were both present and independently usable.

**Lineage:** It is distinct from [[parameter-retrieval-routing]], which guides later computation toward knowledge stored in model parameters rather than selecting among already formed contents.
