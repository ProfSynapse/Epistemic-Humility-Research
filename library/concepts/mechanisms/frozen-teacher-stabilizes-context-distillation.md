---
aliases:
- Frozen teacher improves OPCD stability
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:frozen-teacher-stabilizes-context-distillation
  type: mechanism
  status: canonical
cause: "The context-conditioned teacher remains frozen while the student is updated."
effect: "[[on-policy-context-distillation]] has a more stable target and higher task accuracy than simultaneous self-distillation."
polarity: enables
related:
- '[[2602.12275--policy-context-distillation-language-models]]'
- '[[on-policy-context-distillation]]'
relationships:
- type: supported_by
  target: '[[2602.12275--policy-context-distillation-language-models]]'
  target_id: paper:2602.12275
  confidence: high
- type: related_to
  target: '[[on-policy-context-distillation]]'
  target_id: method:on-policy-context-distillation
  confidence: high
---

The frozen teacher-student configuration scored 53.9 versus 18.8 for
self-distillation on Sokoban and 56.8 versus 50.0 on the medical task. The
authors attribute self-distillation failures to the variance from a teacher
whose weights change during training.
