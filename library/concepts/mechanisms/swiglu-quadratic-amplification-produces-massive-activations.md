---
aliases:
- SwiGLU quadratic amplification produces massive activations
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:swiglu-quadratic-amplification-produces-massive-activations
  type: mechanism
  status: canonical
cause: "SwiGLU's elementwise gating multiplication quadratically amplifies a growing residual-stream signal in one or two early feed-forward blocks."
effect: "extreme outlier values are injected into a handful of channels via the residual connection, producing the step-up onset of the massive-activation life cycle."
polarity: causes
related:
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
- '[[massive-activations]]'
- '[[swiglu]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[swiglu]]'
  target_id: method:swiglu
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Sun et al. trace the step-up onset of the massive-activation life cycle to
SwiGLU's elementwise gating multiplication: a growing residual-stream signal
gets quadratically amplified within one or two early feed-forward blocks,
injecting extreme values into a handful of channels via the residual
connection. Downstream blocks then passively propagate the resulting outliers
before late blocks neutralize them with opposite-sign contributions, confining
massive activations to intermediate layers across all seven evaluated
Llama/Qwen models (Figure 1; Table 1).
