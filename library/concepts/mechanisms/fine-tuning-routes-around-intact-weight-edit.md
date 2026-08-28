---
aliases:
- Fine-tuning routes around an intact steering edit
- Behavioral recovery occurs without weight-edit reversal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fine-tuning-routes-around-intact-weight-edit
  type: mechanism
  status: canonical
cause: "Fine-tuning updates the steering direction mostly orthogonally to the original [[embedded-activation-steering]] weight pattern."
effect: "Behavior can revert through alternative pathways without linearly cancelling the installed weight edit."
polarity: explains
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
- '[[vector-recovery-ratio]]'
- '[[weight-edit-reversal-fraction]]'
relationships:
- type: supported_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: high
- type: related_to
  target: '[[vector-recovery-ratio]]'
  target_id: metric:vector-recovery-ratio
  confidence: high
- type: related_to
  target: '[[weight-edit-reversal-fraction]]'
  target_id: metric:weight-edit-reversal-fraction
  confidence: high
---

Across 20 runs, fine-tuning reversed at most 0.79 percent of the embedded edit.
Its update along the steering direction was nearly orthogonal to the pre-edit
weight pattern, while behavioral and vector recovery were not significantly
correlated.
