---
aliases:
- Embedded steering
- Weight-embedded activation steering
- Activation steering embedded in weights
tags:
- kg/method
- concept
- method
kg:
  id: method:embedded-activation-steering
  type: method
  status: canonical
area: methods
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[activation-steering]]'
- '[[weight-orthogonalization]]'
relationships:
- type: related_to
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[weight-orthogonalization]]'
  target_id: method:weight-orthogonalization
  confidence: high
---

Embedded activation steering absorbs a linear projection or amplification
operator into residual-stream output weights. The modified model then applies
the steering transformation without an inference-time activation hook.

**Why it matters here:** The method gives a weights-level route for installing
a representation-space intervention before deployment.

**Lineage:** It implements a linear [[activation-steering]] operator through a
structured weight edit, including refusal-direction orthogonalization.
