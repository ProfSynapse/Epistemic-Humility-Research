---
aliases:
- OPCD preserves out-of-distribution behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:on-policy-context-distillation-mitigates-forgetting
  type: mechanism
  status: canonical
cause: "[[on-policy-context-distillation]] trains on trajectories sampled from the student's current distribution."
effect: "Out-of-distribution instruction-following performance is preserved better than with off-policy context distillation."
polarity: prevents
related:
- '[[2602.12275--policy-context-distillation-language-models]]'
- '[[on-policy-context-distillation]]'
- '[[context-distillation]]'
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
---

On Frozen Lake, OPCD retained an IF-Eval score near the base model and about
two points above the off-policy baseline. In cross-size safety distillation,
OPCD preserved medical accuracy and exceeded the off-policy baseline by about
four points.
