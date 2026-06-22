---
aliases:
- CoT monitorability
- chain-of-thought monitorability
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:monitorability
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2606.20560--how-transparent-is-diffusiongemma]]'
- '[[reasoning-transparency]]'
relationships:
- type: measured_by
  target: '[[2606.20560--how-transparent-is-diffusiongemma]]'
  target_id: paper:2606.20560
  confidence: high
- type: related_to
  target: '[[reasoning-transparency]]'
  target_id: term:reasoning-transparency
---

Monitorability measures whether a model's outputs or reasoning traces contain
enough information for a downstream monitor to infer task-relevant properties
of the model's reasoning, behavior, or environment.

**Why it matters here:** Monitorability is a practical transparency test. A
model can be accurate while still hiding the reasoning signals needed to detect
misuse, misalignment, hallucination, or knowledge-boundary failure.
