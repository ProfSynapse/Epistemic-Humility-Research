---
aliases:
- Joint-Orth
- Orthogonal joint adaptation
tags:
- kg/method
- concept
- method
kg:
  id: method:orthogonality-constrained-joint-adaptation
  type: method
  status: canonical
area: methods
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[post-block-activation-steering]]'
- '[[low-rank-adaptation]]'
- '[[weight-orthogonalization]]'
relationships:
- type: proposed_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[post-block-activation-steering]]'
  target_id: method:post-block-activation-steering
  confidence: high
- type: derived_from
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[weight-orthogonalization]]'
  target_id: method:weight-orthogonalization
  confidence: medium
---

Orthogonality-constrained joint adaptation trains a LoRA weight update and a
post-block activation adapter together. During training, it projects the
activation adapter's output matrix onto the complement of the LoRA output
subspace.

**Why it matters here:** The method tests whether weight-space and
activation-space adaptation can contribute distinct functions instead of
learning redundant directions.

**Lineage:** It combines [[low-rank-adaptation]] with
[[post-block-activation-steering]] and adds an explicit subspace constraint.
