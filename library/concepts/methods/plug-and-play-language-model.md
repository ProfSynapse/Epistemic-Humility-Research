---
aliases:
- Plug and Play Language Model
- PPLM
tags:
- kg/method
- concept
- method
kg:
  id: method:plug-and-play-language-model
  type: method
  status: canonical
area: methods
related:
- '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
relationships:
- type: used_by
  target: '[[2401.01967--mechanistic-understanding-alignment-algorithms-case-study-dpo]]'
  target_id: paper:2401.01967
  confidence: high
---

Plug and Play Language Model generation uses gradients from an attribute classifier to shift generation toward a selected attribute without retraining the base model. This paper uses PPLM with a toxicity probe to construct rejected continuations for DPO preference pairs.
