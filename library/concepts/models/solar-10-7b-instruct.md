---
aliases:
- SOLAR-10.7B-Instruct
- SOLAR 10.7B Instruct
tags:
- kg/model
- concept
- model
kg:
  id: model:solar-10-7b-instruct
  type: model
  status: canonical
area: models
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[qwen3-14b]]'
relationships:
- type: studied_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[qwen3-14b]]'
  target_id: model:qwen3-14b
  confidence: low
---

SOLAR-10.7B-Instruct is an instruction-tuned 10.7-billion-parameter language
model. The paper includes it in the cross-family steering-persistence study.

**Why it matters here:** Its brevity edit returned nearly to baseline after
SFT, showing that behavioral durability varies across model and target.

**Lineage:** It is studied alongside [[qwen3-14b]] and three Llama models.
