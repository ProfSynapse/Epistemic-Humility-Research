---
aliases:
- Qwen3
- Qwen3-1.7B
- Qwen3-4B
- Qwen3-8B
- Qwen-3-8B
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen3
  type: model
  status: canonical
area: models
related:
- '[[2606.32032--reinforcement-learning-metacognitive-feedback-elicits-faithful-uncertainty]]'
- '[[qwen3-32b]]'
relationships:
- type: related_to
  target: '[[qwen3-32b]]'
  target_id: model:qwen3-32b
  confidence: medium
---

Qwen3 is Alibaba's third-generation open model family. This paper evaluates instruction-tuned Qwen3 variants at 1.7B, 4B, and 8B scale for faithful calibration, and also uses a larger Qwen3-32B variant as an auxiliary judge in parts of the pipeline.

**Why it matters here:** The Qwen3 results provide an open-model comparison point against Llama-3.1-8B-Instruct and show that RLMF's faithful-calibration gains are not confined to one architecture family.

**Lineage:** Related to the existing [[qwen3-32b]] model atom used elsewhere in the vault.
