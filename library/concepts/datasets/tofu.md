---
aliases:
- TOFU
- TOFU fictitious author dataset
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:tofu
  type: dataset
  status: canonical
area: datasets
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[pistol]]'
relationships:
- type: used_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: high
- type: related_to
  target: '[[pistol]]'
  target_id: dataset:pistol
  confidence: medium
---

TOFU is a synthetic dataset of 200 fictitious author profiles, each with 20
question-answer pairs generated from predefined attributes. The SEAT paper uses
it for fine-tuning and cross-dataset unknown-query evaluation.

**Why it matters here:** It supplies artificial facts that should be absent
from base-model pretraining and supports held-out abstention tests.
