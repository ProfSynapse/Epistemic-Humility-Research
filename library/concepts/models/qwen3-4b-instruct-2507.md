---
aliases:
- Qwen3-4B-Instruct-2507
- Qwen3 4B Instruct 2507
- Qwen3-4B-Instruct
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen3-4b-instruct-2507
  type: model
  status: canonical
area: models
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[qwen3]]'
relationships:
- type: studied_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: high
---

Qwen3-4B-Instruct-2507 is a 4-billion-parameter instruction-tuned checkpoint in
the Qwen3 family. In GradCuit it receives a 4,096-token continuation budget and
uses the midpoint of its 36 decoder blocks as the main latent-optimization
site.

**Why it matters here:** It is a small open checkpoint on which a
selected-layer latent write can be compared with existing Qwen-family readout
and intervention tools without updating model weights.

**Lineage:** Instruction-tuned member of the [[qwen3]] model family.
