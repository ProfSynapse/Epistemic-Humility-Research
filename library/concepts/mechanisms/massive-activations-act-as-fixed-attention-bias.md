---
aliases:
- massive activations act as fixed bias terms and cause attention sinks
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:massive-activations-act-as-fixed-attention-bias
  type: mechanism
  status: canonical
cause: "a few fixed residual-stream coordinates hold enormous, input-agnostic values at special token positions."
effect: "attention concentrates on those tokens, injecting a constant implicit bias; zeroing them collapses the model while setting them to their mean does not."
polarity: enables
related:
- '[[2402.17762--massive-activations-large-language-models]]'
- '[[massive-activations]]'
- '[[attention-sink]]'
- '[[implicit-attention-bias]]'
relationships:
- type: supported_by
  target: '[[2402.17762--massive-activations-large-language-models]]'
  target_id: paper:2402.17762
  confidence: high
- type: related_to
  target: '[[massive-activations]]'
  target_id: term:massive-activations
  confidence: high
- type: related_to
  target: '[[attention-sink]]'
  target_id: term:attention-sink
  confidence: high
- type: related_to
  target: '[[implicit-attention-bias]]'
  target_id: term:implicit-attention-bias
  confidence: high
---

Sun et al. find that a couple of fixed feature dimensions carry near-constant
values thousands of times the median at the start token and first delimiter,
functioning as implicit bias terms: attention concentrates on those tokens
(attention sinks), setting the values to their mean is harmless, and zeroing them
collapses the model, showing they are input-agnostic yet functionally essential.
