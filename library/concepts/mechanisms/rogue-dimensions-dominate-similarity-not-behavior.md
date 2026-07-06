---
aliases:
- a few rogue dimensions dominate similarity while being irrelevant to behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rogue-dimensions-dominate-similarity-not-behavior
  type: mechanism
  status: canonical
cause: "one to five embedding dimensions with far-from-origin means and outsized variance."
effect: "dominate cosine and Euclidean similarity (driving anisotropy) despite being nearly irrelevant to model behavior; per-dimension standardization neutralizes them."
polarity: enables
related:
- '[[2109.04404--all-bark-no-bite-rogue-dimensions-transformer]]'
- '[[rogue-dimensions]]'
relationships:
- type: supported_by
  target: '[[2109.04404--all-bark-no-bite-rogue-dimensions-transformer]]'
  target_id: paper:2109.04404
  confidence: high
- type: related_to
  target: '[[rogue-dimensions]]'
  target_id: term:rogue-dimensions
  confidence: high
---

Timkey and van Schijndel show that a handful of rogue dimensions can supply over
99% of expected cosine similarity, that removing the top one to five collapses
the explained variance of the similarity measure, and that ablating them barely
changes model behavior, so a similarity metric on raw embeddings can be
degenerate; per-dimension standardization removes the effect and restores
representational quality.
