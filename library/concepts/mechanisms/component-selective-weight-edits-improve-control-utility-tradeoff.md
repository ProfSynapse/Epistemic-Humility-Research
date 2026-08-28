---
aliases:
- Selective rank-1 edits improve behavioral control while preserving utility
- Steering-guided component editing outperforms global activation injection at matched utility
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:component-selective-weight-edits-improve-control-utility-tradeoff
  type: mechanism
  status: canonical
cause: "Steering-vector alignment scores and Elastic-Net sparsity select rank-1 edits for behaviorally relevant attention heads and MLP neurons."
effect: "The edited model improves the controlled attribute at matched downstream utility relative to global inference-time activation steering."
polarity: increases
related:
- '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
- '[[steer2edit]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
  target_id: paper:2602.09870
  confidence: high
- type: related_to
  target: '[[steer2edit]]'
  target_id: method:steer2edit
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

Across safety, truthfulness, and efficient-reasoning evaluations, Steer2Edit configurations reached more favorable attribute and utility trade-offs than direct activation injection. The paper reports gains at matched downstream performance and validates that dense or unnormalized edit variants can sharply damage utility.
