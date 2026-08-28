---
aliases:
- Dual-pass routing adds compute for adapter selection
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dual-pass-routing-adds-compute-for-adapter-selection
  type: mechanism
  status: canonical
cause: "X-LoRA first runs the base model to obtain hidden states for its scaling head, then runs the model again with the predicted adapter coefficients."
effect: "Adapter selection can depend on the input, but inference requires two forward passes and separate cache handling."
polarity: trades_off
related:
- '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
- '[[x-lora]]'
- '[[x-lora-scaling-head]]'
relationships:
- type: supported_by
  target: '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
  target_id: paper:2402.07148
  confidence: high
- type: related_to
  target: '[[x-lora]]'
  target_id: method:x-lora
  confidence: high
- type: related_to
  target: '[[x-lora-scaling-head]]'
  target_id: term:x-lora-scaling-head
  confidence: high
---

The scaling pass uses constant adapter weights and feeds its hidden states to the scaling head. The forward pass then applies the resulting coefficient tensor, and reusing one key-value cache across both passes can corrupt the scaling-head input.
