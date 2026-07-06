---
aliases:
- Task Difficulty Reduces Performative CoT
- Task Difficulty Relative to Model Enables CoT Faithfulness
- task difficulty enables cot faithfulness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:task-difficulty-reduces-performativity
  type: mechanism
  status: canonical
cause: Task difficulty relative to model capability (easy recall-based versus hard multi-hop reasoning)
effect: "Degree of performative [[chain-of-thought-faithfulness|chain-of-thought]] (gap between probe or forced-answer accuracy and CoT monitor accuracy)"
polarity: decreases
related:
- '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
- '[[performative-chain-of-thought]]'
- '[[chain-of-thought-faithfulness]]'
- '[[chain-of-thought-prompting]]'
relationships:
- type: supported_by
  target: '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
  target_id: paper:2603.05488
  confidence: high
- type: supported_by
  target: '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
  target_id: paper:2307.13702
  confidence: high
- type: related_to
  target: '[[performative-chain-of-thought]]'
  target_id: term:performative-chain-of-thought
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
- type: related_to
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
---

When a task is sufficiently hard relative to the model's parametric knowledge, the model cannot internally resolve the answer before generating its reasoning trace, so the written chain-of-thought does real computational work and faithfully tracks the probe-detected decision trajectory. Conversely, on easy recall tasks the answer is settled internally before the first reasoning token, producing performative CoT that rationalises a foregone conclusion. Turpin et al. (2307.13702) and arXiv:2603.05488 each show that the probe-accuracy vs CoT-monitor accuracy gap collapses as task difficulty increases, confirming task difficulty as the primary moderator of CoT faithfulness.
