---
aliases:
- Model Size Increases Performative CoT
- Model Scale Reduces CoT Faithfulness
- model scale reduces cot faithfulness
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:model-size-increases-performativity
  type: mechanism
  status: canonical
cause: Model size and capability (larger models store more in-weights knowledge)
effect: "Rate of performative [[chain-of-thought-faithfulness|chain-of-thought]] on the same task (how early the final answer is internally settled before reasoning begins)"
polarity: increases
related:
- '[[2603.05488--reasoning-theater-disentangling-model-beliefs-chain-thought]]'
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
- '[[performative-chain-of-thought]]'
- '[[chain-of-thought-faithfulness]]'
- '[[task-difficulty-reduces-performativity]]'
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
  target: '[[task-difficulty-reduces-performativity]]'
  target_id: mechanism:task-difficulty-reduces-performativity
---

Larger models have richer parametric recall, so a given task is effectively easier for them; the model internally commits to the answer before composing its reasoning trace, making the written CoT performative rather than generative. arXiv:2603.05488 shows that on identical tasks, bigger models exhibit a larger gap between probe-detected answer commitment and CoT monitor accuracy, measured via [[attention-probing]] classifiers. This effect runs opposite to [[task-difficulty-reduces-performativity]]: holding difficulty fixed, scaling up the model raises performativity; holding model fixed, raising difficulty lowers it.
