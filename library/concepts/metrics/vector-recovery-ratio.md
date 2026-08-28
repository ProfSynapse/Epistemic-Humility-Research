---
aliases:
- Vector recovery ratio
- Steering vector recovery ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:vector-recovery-ratio
  type: metric
  status: canonical
area: metrics
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
- '[[steering-vector]]'
relationships:
- type: used_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Vector recovery ratio measures how much projection onto an embedded steering
direction returns after fine-tuning. Zero indicates that the edit remains
intact, while one indicates recovery to the original pre-edit projection.

**Why it matters here:** The metric tests whether behavioral recovery reflects
literal reversal of the weights-level intervention.

**Lineage:** It compares original, steered, and steered-then-fine-tuned output
weight projections along the selected direction.
