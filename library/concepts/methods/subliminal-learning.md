---
aliases:
- Subliminal Learning
tags:
- kg/method
- concept
- method
kg:
  id: method:subliminal-learning
  type: method
  status: canonical
area: methods
related:
- '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
- '[[steering-vector-distillation]]'
- '[[context-distillation]]'
relationships:
- type: proposed_by
  target: '[[2606.00995--subliminal-learning-steering-vector-distillation]]'
  target_id: paper:2606.00995
  confidence: medium
- type: related_to
  target: '[[steering-vector-distillation]]'
  target_id: method:steering-vector-distillation
  confidence: high
- type: related_to
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: medium
---

Subliminal learning is the transfer of a teacher model's behavioral trait to a
student that is fine-tuned on teacher outputs with no explicit semantic
reference to that trait. The effect is evaluated by testing the student on
held-out prompts that directly elicit the trait.

**Why it matters here:** Subliminal learning is an example of behavior encoded
into trainable weights through statistics in generated data that are not
captured by surface semantics.

**Lineage:** The phenomenon is related to distillation and unintended
generalization. This paper explains its language-model form as a special case
of [[steering-vector-distillation]].
