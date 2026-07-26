---
aliases:
- Qwen2.5-7B-Instruct
- Qwen 2.5 7B Instruct
- Qwen2.5-7B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-7b-instruct
  type: model
  status: canonical
area: models
related:
- '[[qwen3]]'
relationships:
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
---

Qwen2.5-7B-Instruct is Alibaba's instruction-tuned 7-billion-parameter checkpoint from the Qwen2.5 release family, commonly used as a smaller open cross-architecture comparison point to Llama-family models in mechanistic and behavioral studies.

**Why it matters here:** [[2605.05715--decodable-but-not-corrected-fixed-residual-stream]] uses Qwen2.5-7B-Instruct as the cross-architecture replication target for its Overthinking probing and linear-steering null-result findings, showing the classification-correction gap is not an artifact of a single model family.

**Lineage:** an earlier generation in the same Qwen model line as [[qwen3]].
