---
aliases:
- Safety and truthfulness edits concentrate in attention while reasoning-efficiency edits concentrate in MLPs
- Behavioral target determines the component class selected for weight editing
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:behavior-dependent-component-edits-separate-attention-and-mlp-control
  type: mechanism
  status: canonical
cause: "Steer2Edit applies behavior-specific component scoring and sparsity budgets to attention heads and MLP neurons."
effect: "Safety and truthfulness control concentrates in sparse attention-head edits, while reasoning-efficiency control uses distributed MLP-neuron edits."
polarity: redistributes
related:
- '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
- '[[steer2edit]]'
relationships:
- type: supported_by
  target: '[[2602.09870--steer2edit-activation-steering-component-level-editing]]'
  target_id: paper:2602.09870
  confidence: high
- type: related_to
  target: '[[steer2edit]]'
  target_id: method:steer2edit
  confidence: high
---

The component maps and budget-isolation experiments associate safety and truthfulness gains with a small set of attention heads. The reasoning-efficiency setting instead uses broad MLP updates, and attention-only budget changes provide little efficiency gain.
