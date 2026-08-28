---
aliases:
- Student rollouts and reverse KL internalize context
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:on-policy-reverse-kl-internalizes-context
  type: mechanism
  status: canonical
cause: "A context-free student samples its own trajectories and minimizes reverse KL to a teacher conditioned on the target context."
effect: "The student's weights reproduce useful context-conditioned behavior without the context at inference time."
polarity: enables
related:
- '[[2602.12275--policy-context-distillation-language-models]]'
- '[[on-policy-context-distillation]]'
- '[[context-distillation]]'
- '[[on-policy-distillation]]'
relationships:
- type: supported_by
  target: '[[2602.12275--policy-context-distillation-language-models]]'
  target_id: paper:2602.12275
  confidence: high
- type: related_to
  target: '[[on-policy-context-distillation]]'
  target_id: method:on-policy-context-distillation
  confidence: high
- type: related_to
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: high
- type: related_to
  target: '[[on-policy-distillation]]'
  target_id: method:on-policy-distillation
  confidence: high
---

Across math, text games, medical question answering, and safety classification,
OPCD usually exceeded the off-policy context-distillation baseline. The student
generated without the target context, while the teacher scored the same
trajectory with that context present.
