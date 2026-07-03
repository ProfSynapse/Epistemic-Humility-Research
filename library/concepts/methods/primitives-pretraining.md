---
aliases:
- 1-rule pretraining
- primitive pretraining
- primitives pretrain
tags:
- kg/method
- concept
- method
kg:
  id: method:primitives-pretraining
  type: method
  status: canonical
area: neuroscience
related:
- '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
- '[[compositional-generalization]]'
relationships:
- type: proposed_by
  target: '[[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]'
  target_id: paper:2209.07431
  confidence: high
- type: required_by
  target: '[[compositional-generalization]]'
  target_id: term:compositional-generalization
---

Primitives pretraining is a curriculum strategy for artificial neural networks in which the three compositional rule domains of the [[c-pro-task]] are taught in isolation before the network encounters the full multi-rule task: a sensory discrimination subtask (distinguishing stimulus features), a motor response subtask (mapping responses), and a logical decision subtask (learning boolean relations). The rationale is that embedding abstract rule knowledge through these isolated 1-rule exposures gives the network a head start that promotes [[abstract-representations]] rather than context-specific memorization. Combined with a 2-rule intermediate stage it forms the "Combined" pretraining condition, which achieves the highest [[parallelism-score]] and best zero-shot compositional generalization on held-out [[c-pro-task]] contexts.

**Why it matters here:** Primitives pretraining demonstrates that the structure of training data, not just model capacity, determines whether internal representations generalize compositionally. This parallels arguments in epistemic-humility research that training regime shapes whether a model's uncertainty representations are flexible or brittle.

**Lineage:** proposed in [[2209.07431--compositional-generalization-through-abstract-representations-human-artificial]]; a prerequisite intervention for [[compositional-generalization]] in the C-PRO setting; motivates curriculum design choices in multi-task learning.
