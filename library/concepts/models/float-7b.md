---
aliases:
- FLoat-7B
- Fine-tuned Llama on arithmetic tasks
tags:
- kg/model
- concept
- model
kg:
  id: model:float-7b
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

FLoat-7B is a fully fine-tuned LLaMA-7B model trained on the same arithmetic data as Goat-7B. It reaches 0.82 accuracy on the paper's entity-tracking task.
