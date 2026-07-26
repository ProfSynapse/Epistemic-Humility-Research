---
aliases:
- Falcon3-7B-Instruct
- Falcon3 7B
tags:
- kg/model
- concept
- model
kg:
  id: model:falcon3-7b-instruct
  type: model
  status: canonical
area: models
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
relationships:
- type: used_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
---

Falcon3-7B-Instruct is TII's instruction-tuned 7-billion-parameter checkpoint from the Falcon3 release family, used alongside Llama3.1 and Qwen2.5 checkpoints as a cross-family comparison point in activation-steering safety studies.

**Why it matters here:** [[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]] uses Falcon3-7B-Instruct in its random-direction and universal-attack experiments; the universal steering vector improves its harmful compliance nearly 10-fold (5.7% to 63.4%), making it the model family most vulnerable to the aggregated-vector attack.

**Lineage:** part of TII's Falcon3 release family, alongside [[falconh1]].
