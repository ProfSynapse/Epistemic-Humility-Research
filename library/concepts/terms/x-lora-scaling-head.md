---
aliases:
- X-LoRA scaling head
- adapter scaling head
tags:
- kg/term
- concept
- term
kg:
  id: term:x-lora-scaling-head
  type: term
  status: canonical
area: terms
related:
- '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
- '[[x-lora]]'
relationships:
- type: proposed_by
  target: '[[2402.07148--x-lora-mixture-low-rank-adapter-experts]]'
  target_id: paper:2402.07148
  confidence: high
- type: related_to
  target: '[[x-lora]]'
  target_id: method:x-lora
  confidence: high
---

The X-LoRA scaling head is a feed-forward network that maps hidden states to softmax-normalized adapter coefficients. It is the only trainable component in the paper's default X-LoRA setup.

**Why it matters here:** It is a concrete weights-level routing module that reads hidden states and controls downstream adapter contributions.

**Lineage:** It serves as the routing network in X-LoRA's adapter mixture.
