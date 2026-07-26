---
aliases:
- Qwen2.5-3B-Instruct
- Qwen 2.5 3B Instruct
- Qwen2.5-3B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-3b-instruct
  type: model
  status: canonical
area: models
related:
- '[[qwen2-5-7b-instruct]]'
- '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
relationships:
- type: related_to
  target: '[[qwen2-5-7b-instruct]]'
  target_id: model:qwen2-5-7b-instruct
  confidence: high
- type: evaluation_set_for
  target: '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
  target_id: paper:2602.06801
  confidence: high
---

Qwen2.5-3B-Instruct is Alibaba's instruction-tuned 3-billion-parameter
checkpoint from the Qwen2.5 release family, a smaller sibling of
[[qwen2-5-7b-instruct]] used as a lightweight cross-architecture and
cross-scale comparison point to Llama-family models in steering and
mechanistic studies.

**Why it matters here:**
[[2602.06801--non-identifiability-steering-vectors-large-language-models]]
uses Qwen2.5-3B-Instruct alongside Llama-3.1-8B-Instruct to show that
steering-vector non-identifiability holds across models of different scale
and family, not just within a single checkpoint.

**Lineage:** an earlier and smaller checkpoint in the same Qwen2.5 line as
[[qwen2-5-7b-instruct]].
