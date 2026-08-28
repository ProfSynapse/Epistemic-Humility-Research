---
aliases:
- Sparse updates limit off-target activation drift
- Masked fine-tuning preserves unknown-query representations
- Parameter sparsity anchors abstention behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sparse-updates-limit-off-target-activation-drift
  type: mechanism
  status: canonical
cause: "A binary parameter mask restricts each fine-tuning update to a subset of model coordinates."
effect: "Residual representations for off-target unknown queries move less, which helps preserve prior abstention behavior while target examples remain learnable."
polarity: limits
related:
- '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
- '[[sparse-entity-aware-tuning]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2506.14387--seat-sparse-entity-aware-tuning-knowledge-adaptation]]'
  target_id: paper:2506.14387
  confidence: medium
- type: related_to
  target: '[[sparse-entity-aware-tuning]]'
  target_id: method:sparse-entity-aware-tuning
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
---

Increasing parameter sparsity generally reduced activation drift on unseen
queries and improved human-judged abstention. Target-data activations still
moved substantially. Sparse tuning alone reached 0.806 IDK human assessment,
below SEAT's 0.954, so sparsity did not explain the full effect.

The paper proves only that masked updates give a no-looser worst-case bound on
activation displacement. It does not formally prove the behavioral mechanism.
