---
aliases:
- relation heads
- mixture head
tags:
- kg/term
- concept
- term
kg:
  id: term:relation-head
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[mover-head]]'
- '[[factual-association-recall-mechanism]]'
- '[[upper-mhsa-extracts-factual-attributes]]'
- '[[residual-stream]]'
relationships:
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[upper-mhsa-extracts-factual-attributes]]'
  target_id: mechanism:upper-mhsa-extracts-factual-attributes
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

A relation head is an attention head in a transformer that attends to relation
tokens in the prompt and injects relational signal into the residual stream,
contributing the "what kind of fact are we looking for?" information that guides
the downstream MLP to map subject to object. Relation heads typically operate in
middle-to-upper layers, working in concert with subject-enriched representations
to enable the model to distinguish, for example, "capital city of X" from
"language spoken in X" even when X is the same entity.

**Why it matters here:** Relation heads are a key component in the factual-recall
pipeline; understanding their contribution clarifies why models sometimes confuse
different facts about the same subject, a failure mode tied to knowledge boundary
errors and overconfident wrong answers.

**Lineage:** pairs with [[mover-head]] (which routes enriched subject information
to the prediction position) within the [[factual-association-recall-mechanism]];
the mechanism [[upper-mhsa-extracts-factual-attributes]] characterizes the
combined role of both head types.
