---
aliases:
- ActAdd
- activation additions
tags:
- kg/method
- concept
- method
kg:
  id: method:activation-addition
  type: method
  status: canonical
area: methods
related:
- '[[2308.10248--steering-language-models-with-activation-engineering]]'
- '[[activation-engineering]]'
- '[[steering-vector]]'
- '[[residual-stream-activation]]'
relationships:
- type: proposed_by
  target: '[[2308.10248--steering-language-models-with-activation-engineering]]'
  target_id: paper:2308.10248
  confidence: high
- type: related_to
  target: '[[activation-engineering]]'
  target_id: term:activation-engineering
  confidence: high
- type: uses
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: applied_to
  target: '[[residual-stream-activation]]'
  target_id: term:residual-stream-activation
  confidence: medium
---

Activation addition is an activation-engineering method that adds a vector
computed from contrastive prompts or examples to model activations during
generation.

