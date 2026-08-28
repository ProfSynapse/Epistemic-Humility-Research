---
aliases:
- Vicuna-7B
tags:
- kg/model
- concept
- model
kg:
  id: model:vicuna-7b
  type: model
  status: canonical
area: language-models
related:
- '[[llama-7b]]'
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
relationships:
- type: variation_of
  target: '[[llama-7b]]'
  target_id: model:llama-7b
  confidence: high
- type: used_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
---

Vicuna-7B is a LLaMA-7B descendant fine-tuned on user-shared conversations. The paper evaluates whether the base entity-tracking circuit and its functions persist in this model.
