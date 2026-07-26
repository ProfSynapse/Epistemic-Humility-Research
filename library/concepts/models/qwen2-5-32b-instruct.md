---
aliases:
- Qwen2.5-32B-Instruct
- Qwen 2.5 32B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-32b-instruct
  type: model
  status: canonical
area: models
related:
- '[[qwen2-5-7b-instruct]]'
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
relationships:
- type: related_to
  target: '[[qwen2-5-7b-instruct]]'
  target_id: model:qwen2-5-7b-instruct
  confidence: high
- type: used_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: medium
---

Qwen2.5-32B-Instruct is Alibaba's instruction-tuned 32-billion-parameter checkpoint from the Qwen2.5 release family, used as a mid-to-large-scale cross-family comparison point in activation-steering safety evaluations.

**Why it matters here:** [[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]] uses Qwen2.5-32B-Instruct in its universal-attack generalization experiments, where it is the notable exception: the aggregated universal steering vector's effectiveness is reduced on this model relative to the other families tested, showing the attack's model-dependence.

**Lineage:** a larger checkpoint in the same Qwen2.5 release family as [[qwen2-5-7b-instruct]].
