---
aliases:
- Upper MHSA attention heads extract factual attributes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:upper-mhsa-extracts-factual-attributes
  type: mechanism
  status: canonical
cause: Upper multi-head self-attention sublayers attending to both the enriched subject representation and the prediction position, guided by the relation
effect: The correct factual attribute is promoted to the prediction position, with approximately 68% of predictions showing explicit MHSA extraction events and approximately 70% overall involving attention-head-encoded subject-attribute mappings
polarity: enables
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[subject-enrichment]]'
- '[[mover-head]]'
- '[[early-mlp-drives-subject-enrichment]]'
relationships:
- type: supported_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: related_to
  target: '[[subject-enrichment]]'
  target_id: term:subject-enrichment
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
- type: related_to
  target: '[[early-mlp-drives-subject-enrichment]]'
  target_id: mechanism:early-mlp-drives-subject-enrichment
---

After [[early-mlp-drives-subject-enrichment]] loads attribute information into the subject-token residual stream, upper multi-head self-attention (MHSA) sublayers extract the relation-appropriate attribute and write it to the prediction position (arXiv:2304.14767). Approximately 68% of successful factual predictions exhibit a detectable MHSA extraction event, and roughly 70% of predictions overall involve attention heads encoding subject-to-attribute mappings. This two-stage pipeline -- MLP-driven enrichment followed by attention-driven extraction -- constitutes the core mechanism of factual-attribute recall in GPT-style transformers.
