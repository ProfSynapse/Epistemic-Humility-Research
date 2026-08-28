---
aliases:
- Steering behavioural preservation
- Steering behavioral preservation
- Steering preservation ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:steering-behavioral-preservation
  type: metric
  status: canonical
area: metrics
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
relationships:
- type: used_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: high
---

Steering behavioral preservation measures the fraction of an embedded
steering effect that remains after fine-tuning. A value of one denotes full
behavioral preservation, while zero denotes reversion to the unsteered
baseline.

**Why it matters here:** It separates deployment behavior from the physical
persistence of a weight edit.

**Lineage:** The paper defines separate forms for refusal-rate ablation and
response-length amplification.
