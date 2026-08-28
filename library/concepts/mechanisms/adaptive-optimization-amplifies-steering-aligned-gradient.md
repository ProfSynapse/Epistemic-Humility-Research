---
aliases:
- Adaptive optimization exposes weak steering-aligned gradients
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:adaptive-optimization-amplifies-steering-aligned-gradient
  type: mechanism
  status: canonical
cause: "An adaptive optimizer rescales LoRA parameters and prevents a small set of outlier gradients from dominating updates."
effect: "A weak gradient component aligned with the teacher's [[steering-vector]] can install the corresponding direction in the student."
polarity: enables
related:
- '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
- '[[steering-vector-distillation]]'
- '[[low-rank-adaptation]]'
relationships:
- type: supported_by
  target: '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
  target_id: paper:2606.00995
  confidence: high
- type: related_to
  target: '[[steering-vector-distillation]]'
  target_id: method:steering-vector-distillation
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

The paper reports that Adam and RMSProp enabled subliminal learning in its
language-model setting, while plain SGD and momentum SGD did not. Loss-matched
controls and frozen scaling-map experiments support the role of per-parameter
adaptive scaling, though the authors call the explanation preliminary.
