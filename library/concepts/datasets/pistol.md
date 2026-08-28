---
aliases:
- PISTOL
- PISTOL synthetic contractual knowledge dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:pistol
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[tofu]]'
relationships:
- type: used_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[tofu]]'
  target_id: dataset:tofu
  confidence: medium
---

PISTOL is a synthetic knowledge-adaptation dataset built from generated
contractual relationships. The SEAT experiments use Sample Dataset 1, with 20
relationships and 20 question-answer pairs per relationship.

**Why it matters here:** Its fictitious entities provide disjoint known and
unknown sets for testing whether a knowledge update erodes abstention.
