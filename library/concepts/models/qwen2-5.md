---
aliases:
- Qwen2.5
- Qwen 2.5
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5
  type: model
  status: canonical
area: models
related:
- '[[qwen2-5-7b-instruct]]'
- '[[qwen3]]'
- '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
relationships:
- type: related_to
  target: '[[qwen2-5-7b-instruct]]'
  target_id: model:qwen2-5-7b-instruct
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: medium
- type: used_by
  target: '[[2603.05498--spike-sparse-sink-anatomy-massive-activations-attention]]'
  target_id: paper:2603.05498
  confidence: high
---

Qwen2.5 is Alibaba's second-generation-plus open model family, released in
instruction-tuned and base variants across a range of parameter counts. It uses
pre-norm RMSNorm and SwiGLU feed-forward blocks in the same architectural
lineage as Llama-family and Qwen3 models, making it a standard cross-family
comparison point for studies of massive activations and attention sinks.

**Why it matters here:** Sun et al. include Qwen2.5 checkpoints among the seven
Llama/Qwen models used to characterize the step-up/plateau/step-down massive-
activation life cycle, showing the pattern is not specific to one model family.

**Lineage:** predecessor generation to [[qwen3]] in the Qwen line; the specific
7B instruction-tuned checkpoint used elsewhere in this vault is
[[qwen2-5-7b-instruct]].
