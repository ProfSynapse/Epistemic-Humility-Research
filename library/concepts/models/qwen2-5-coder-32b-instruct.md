---
aliases:
- Qwen2.5-Coder-32B-Instruct
- Qwen 2.5 Coder 32B Instruct
tags:
- kg/model
- concept
- model
kg:
  id: model:qwen2-5-coder-32b-instruct
  type: model
  status: canonical
area: models
related:
- '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
- '[[qwen2-5-32b-instruct]]'
relationships:
- type: studied_by
  target: '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
  target_id: paper:2507.16795
  confidence: high
- type: related_to
  target: '[[qwen2-5-32b-instruct]]'
  target_id: model:qwen2-5-32b-instruct
  confidence: high
---

Qwen2.5-Coder-32B-Instruct is a 32-billion-parameter instruction-tuned coding
model in the Qwen2.5 family. Casademunt et al. use it for insecure-code
fine-tuning and emergent-misalignment evaluation.

**Why it matters here:** It is one of the two large models on which Concept
Ablation Fine-Tuning reduced broad misalignment while retaining most
in-distribution insecure-code behavior.
