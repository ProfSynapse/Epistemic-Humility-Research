---
aliases:
- Steering Vector Distillation
- SVDistillation
tags:
- kg/method
- concept
- method
kg:
  id: method:steering-vector-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
- '[[steering-vector]]'
- '[[low-rank-adaptation]]'
- '[[subliminal-learning]]'
relationships:
- type: proposed_by
  target: '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
  target_id: paper:2606.00995
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[subliminal-learning]]'
  target_id: method:subliminal-learning
  confidence: high
---

Steering vector distillation trains a student on outputs from a copy of the
same model with an activation steering vector applied. The student learns a
weight change whose residual-stream shift aligns with the teacher vector,
including for random vectors without semantic meaning.

**Why it matters here:** The method directly tests whether an inference-time
activation intervention can be internalized by fine-tuning the student's
weights.

**Lineage:** It is a distillation method built from [[steering-vector]]
interventions and is presented as the general process underlying
[[subliminal-learning]].
