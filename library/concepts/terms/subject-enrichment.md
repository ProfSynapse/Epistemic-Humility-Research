---
aliases:
- attribute-rich subject representation
- subject representation enrichment
tags:
- kg/term
- concept
- term
kg:
  id: term:subject-enrichment
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[factual-association-recall-mechanism]]'
- '[[factual-recall-localization]]'
- '[[mover-head]]'
relationships:
- type: proposed_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: related_to
  target: '[[factual-association-recall-mechanism]]'
  target_id: term:factual-association-recall-mechanism
- type: related_to
  target: '[[factual-recall-localization]]'
  target_id: term:factual-recall-localization
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
---

Subject enrichment is a process identified in transformer language models whereby the hidden representation at the last-subject-token position accumulates a wealth of subject-related attributes across early-to-middle layers, driven primarily by early MLP sublayers. The attribute-recall rate at this position reaches roughly 50% in intermediate-upper layers, substantially higher than at other sequence positions. Upper attention heads subsequently query this enriched representation to extract the specific factual attribute relevant to the relation being completed.

**Why it matters here:** Understanding how models build up subject knowledge internally connects to questions of knowledge localization and knowledge boundaries: if a model's subject representation is sparse or corrupted, factual recall fails and the model may hallucinate or over-confidently assert wrong facts rather than abstaining.

**Lineage:** introduced in [[2304.14767--dissecting-recall-factual-associations]] as step 1 of the [[factual-association-recall-mechanism]]; underpins findings in [[early-mlp-drives-subject-enrichment]] and [[subject-enrichment-required-for-attribute-extraction]].
