---
aliases:
- Instruction tuning on held-out set hurts cross-domain abstention generalization
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-hurts-abstention-generalization
  type: mechanism
  status: canonical
cause: Training [[abstention]] via [[instruction-tuning]] on a held-out set from one dataset or LLM
effect: Performance drops of up to 33.8% in [[abstain-accuracy]] when transferred to different knowledge domains or LLMs
polarity: decreases
related:
- '[[2402.00367--dont-hallucinate-abstain]]'
- '[[abstention]]'
- '[[instruction-tuning]]'
- '[[abstain-accuracy]]'
relationships:
- type: supported_by
  target: '[[2402.00367--dont-hallucinate-abstain]]'
  target_id: paper:2402.00367
  confidence: high
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[abstain-accuracy]]'
  target_id: metric:abstain-accuracy
---

Instruction-tuned abstention is fragile because it ties the model's abstention behavior to the specific surface features and knowledge distribution of the training set. When evaluated on a different domain or when the trained abstention model is applied to a different base LLM, the abstention accuracy drops dramatically. The dont-hallucinate-abstain paper (arXiv:2402.00367) shows up to 33.8% drops in abstain accuracy under cross-domain and cross-model transfer, motivating dataset diversity and LLM-agnostic abstention strategies.
