---
aliases:
- Orthogonality prevents redundant joint updates
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:orthogonality-prevents-joint-adaptation-redundancy
  type: mechanism
  status: canonical
cause: "[[orthogonality-constrained-joint-adaptation]] projects the activation adapter output away from the LoRA output subspace."
effect: "The weight and activation modules are discouraged from learning aligned and redundant update directions."
polarity: prevents
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[orthogonality-constrained-joint-adaptation]]'
- '[[weight-orthogonalization]]'
relationships:
- type: supported_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[orthogonality-constrained-joint-adaptation]]'
  target_id: method:orthogonality-constrained-joint-adaptation
  confidence: high
- type: related_to
  target: '[[weight-orthogonalization]]'
  target_id: method:weight-orthogonalization
  confidence: medium
---

Naive joint training produced aligned LoRA and activation-adapter subspaces and
often underperformed the individual methods. The projection constraint reduced
that overlap, and Joint-Orth often matched or exceeded the strongest baseline.
