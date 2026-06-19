---
aliases:
- activation addition steers generated behavior
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-addition-steers-generation
  type: mechanism
  status: canonical
cause: "Adding a [[steering-vector]] to intermediate activations during generation."
effect: "Model generations shift toward the behavior represented by the vector."
polarity: enables
related:
- '[[2308.10248--steering-language-models-with-activation-engineering]]'
- '[[activation-addition]]'
- '[[steering-vector]]'
relationships:
- type: supported_by
  target: '[[2308.10248--steering-language-models-with-activation-engineering]]'
  target_id: paper:2308.10248
  confidence: high
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Activation addition can steer generated text by adding behavior-associated
activation vectors during inference.
