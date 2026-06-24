---
aliases:
- shallow-to-semantic layer gradient
- lower-upper layer pattern specialization
- Layer-Depth Pattern Hierarchy in Transformers
tags:
- kg/term
- concept
- term
kg:
  id: term:layer-depth-pattern-hierarchy
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[transformer-feed-forward-layer]]'
- '[[wikitext-103]]'
relationships:
- type: proposed_by
  target: '[[2012.14913--transformer-ff-layers-key-value-memories]]'
  target_id: paper:2012.14913
  confidence: high
- type: related_to
  target: '[[transformer-feed-forward-layer]]'
  target_id: term:transformer-feed-forward-layer
- type: related_to
  target: '[[wikitext-103]]'
  target_id: dataset:wikitext-103
---

The empirical regularity in transformer language models that lower-layer feed-forward memory keys predominantly fire on shallow surface patterns (recurring n-grams, specific punctuation or formatting tokens) while upper-layer keys fire on semantically coherent patterns (recurring topics or discourse contexts that share no surface form). This hierarchy was established in a 16-layer transformer trained on WikiText-103 via human expert annotation of the top-25 trigger examples for each key.

**Why it matters here:** The depth-hierarchy implies that factual knowledge and abstract self-assessment (relevant to epistemic humility) are more likely localized to upper layers, guiding where probing or editing interventions should be targeted.

**Lineage:** discovered in [[2012.14913--transformer-ff-layers-key-value-memories]] using [[wikitext-103]] as the training corpus; a precursor observation to the factual-recall localization literature.
