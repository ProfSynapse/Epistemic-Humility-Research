---
aliases:
- GPT-2 Medium
- GPT2-medium
- GPT2 Medium
tags:
- kg/model
- concept
- model
kg:
  id: model:gpt-2-medium
  type: model
  status: canonical
area: language-models
related:
- '[[gpt-2]]'
- '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
relationships:
- type: variation_of
  target: '[[gpt-2]]'
  target_id: model:gpt-2
  confidence: high
- type: used_by
  target: '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
  target_id: paper:2401.01967
  confidence: high
---

GPT-2 Medium is the 355-million-parameter GPT-2 variant with 24 transformer layers, hidden width 1,024, and MLP width 4,096. The paper applies DPO and mechanistic toxicity interventions to this model.
