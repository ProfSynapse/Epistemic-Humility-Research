---
aliases:
- Qwen2.5-14B-Instruct
- Qwen 2.5 14B Instruct
- Qwen2.5-14B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-14b-instruct
  type: model
  status: canonical
area: models
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[qwen2-5]]'
relationships:
- type: studied_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: related_to
  target: '[[qwen2-5]]'
  target_id: model:qwen2-5
  confidence: high
---

Qwen2.5-14B-Instruct is an instruction-tuned 14-billion-parameter checkpoint in
the Qwen2.5 family. GradCuit evaluates it as one of five backbones for
test-time intermediate-latent optimization on three reasoning benchmarks.

**Why it matters here:** It supplies a larger open Qwen checkpoint for checking
whether an inference-time epistemic write interface persists across scale.

**Lineage:** Instruction-tuned member of the [[qwen2-5]] model family.
