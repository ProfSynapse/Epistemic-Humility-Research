---
aliases:
- Model-specific vector effects restrict subliminal transfer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-specific-steering-effects-limit-cross-model-subliminal-transfer
  type: mechanism
  status: canonical
cause: "A semantic [[steering-vector]] also changes non-semantic output statistics in a model-specific way."
effect: "A student from another model family cannot reliably use those traces to reconstruct the teacher's semantic direction."
polarity: limits
related:
- '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
- '[[steering-vector-distillation]]'
- '[[subliminal-learning]]'
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
  target: '[[subliminal-learning]]'
  target_id: method:subliminal-learning
  confidence: high
---

Directions from one model reduced loss on that model's filtered and semantic
completions more reliably than directions from another family. Cross-variant
transfer within the OLMo-3 family remained positive, supporting a
model-specific rather than purely semantic transmission channel.
