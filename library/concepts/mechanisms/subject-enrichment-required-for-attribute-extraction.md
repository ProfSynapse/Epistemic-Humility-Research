---
aliases:
- Subject enrichment is prerequisite for accurate attribute extraction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:subject-enrichment-required-for-attribute-extraction
  type: mechanism
  status: canonical
cause: Patching (replacing) early subject representations before they are enriched
effect: Attribute extraction rate decreases by up to 50%, demonstrating that the enrichment process is causally necessary for downstream attribute recall
polarity: decreases
related:
- '[[2304.14767--dissecting-recall-factual-associations]]'
- '[[subject-enrichment]]'
- '[[early-mlp-drives-subject-enrichment]]'
- '[[upper-mhsa-extracts-factual-attributes]]'
- '[[activation-patching]]'
relationships:
- type: supported_by
  target: '[[2304.14767--dissecting-recall-factual-associations]]'
  target_id: paper:2304.14767
  confidence: high
- type: related_to
  target: '[[subject-enrichment]]'
  target_id: term:subject-enrichment
- type: related_to
  target: '[[early-mlp-drives-subject-enrichment]]'
  target_id: mechanism:early-mlp-drives-subject-enrichment
- type: related_to
  target: '[[upper-mhsa-extracts-factual-attributes]]'
  target_id: mechanism:upper-mhsa-extracts-factual-attributes
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
---

[[activation-patching]] experiments that replace early subject-token hidden states with states from a corrupted (non-subject-enriched) run cause attribute extraction rates in upper MHSA sublayers to fall by up to 50%, establishing that [[subject-enrichment]] is causally upstream of attribute extraction (arXiv:2304.14767). The degradation is graded with the layer at which the patch is applied: earlier patches that intercept more of the enrichment process cause larger extraction failures. This causal dependency means that interventions targeting the enrichment stage (e.g., via model editing or probing) will have cascading effects on downstream factual recall.
