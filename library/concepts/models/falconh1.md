---
aliases:
- Falcon-H1
- FalconH1
tags:
- kg/model
- concept
- model
kg:
  id: model:falconh1
  type: model
  status: canonical
area: models
related:
- '[[falcon3-7b-instruct]]'
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
relationships:
- type: related_to
  target: '[[falcon3-7b-instruct]]'
  target_id: model:falcon3-7b-instruct
  confidence: medium
- type: used_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: medium
---

FalconH1 is TII's hybrid attention/state-space-model instruction-tuned checkpoint family, included alongside pure-transformer Llama3.1, Qwen2.5, and Falcon3 checkpoints in cross-family activation-steering safety evaluations.

**Why it matters here:** [[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]] includes FalconH1 in its random-direction steering experiments, showing that the harmful-compliance vulnerability from steering is not confined to pure-transformer architectures.

**Lineage:** TII's hybrid architecture line, distinct from the pure-transformer [[falcon3-7b-instruct]] release.
