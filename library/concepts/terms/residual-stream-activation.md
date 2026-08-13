---
aliases:
- residual stream activation
- residual-stream activations
tags:
- kg/term
- concept
- term
kg:
  id: term:residual-stream-activation
  type: term
  status: canonical
area: terms
related:
- '[[residual-stream]]'
- '[[activation-addition]]'
- '[[activation-patching]]'
- '[[refusal-direction]]'
relationships:
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: medium
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
- type: part_of
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
  note: "The intermediate activations read from and written to the residual stream; kept distinct because interventions target the activations, not the architecture concept."
---

Residual-stream activations are intermediate transformer states commonly used
for activation steering, patching, and direction-ablation interventions.

