---
aliases:
- Mistral-Small-24B-Instruct-2501
- Mistral Small 24B Instruct 2501
tags:
- kg/model
- concept
- model
kg:
  id: model:mistral-small-24b-instruct-2501
  type: model
  status: canonical
area: models
related:
- '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
- '[[mistral-7b]]'
relationships:
- type: studied_by
  target: '[[2507.16795--steering-out-distribution-generalization-concept-ablation-fine]]'
  target_id: paper:2507.16795
  confidence: high
- type: related_to
  target: '[[mistral-7b]]'
  target_id: model:mistral-7b
  confidence: medium
---

Mistral-Small-24B-Instruct-2501 is a 24-billion-parameter instruction-tuned
Mistral model. Casademunt et al. use it for insecure-code fine-tuning and
emergent-misalignment evaluation.

**Why it matters here:** It supplies the second model family for the paper's
test of whether training-time concept ablation changes unintended
generalization.
