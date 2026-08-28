---
aliases:
- X-LoRA
- Mixture of Low-Rank Adapter Experts
tags:
- kg/method
- concept
- method
kg:
  id: method:x-lora
  type: method
  status: canonical
area: methods
related:
- '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
- '[[low-rank-adaptation]]'
- '[[x-lora-scaling-head]]'
relationships:
- type: proposed_by
  target: '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
  target_id: paper:2402.07148
  confidence: high
- type: derived_from
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: related_to
  target: '[[x-lora-scaling-head]]'
  target_id: term:x-lora-scaling-head
  confidence: high
---

X-LoRA combines several pretrained LoRA adapters with coefficients predicted from the base model's hidden states. The routing coefficients vary by token, model layer, and adapter expert.

**Why it matters here:** X-LoRA demonstrates a trainable internal sensor that routes adapter-level writes using the model's own hidden state.

**Lineage:** It extends low-rank adaptation with a hidden-state-driven mixture-of-experts scaling head.
