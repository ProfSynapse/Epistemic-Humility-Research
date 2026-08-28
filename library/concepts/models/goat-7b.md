---
aliases:
- Goat-7B
tags:
- kg/model
- concept
- model
kg:
  id: model:goat-7b
  type: model
  status: canonical
area: language-models
related:
- '[[llama-7b]]'
- '[[low-rank-adaptation]]'
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
relationships:
- type: variation_of
  target: '[[llama-7b]]'
  target_id: model:llama-7b
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
- type: used_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
---

Goat-7B is a LLaMA-7B descendant adapted with LoRA on synthetic arithmetic expressions. It reaches 0.82 accuracy on the paper's entity-tracking task.
