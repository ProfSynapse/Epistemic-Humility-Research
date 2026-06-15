---
aliases:
- Abstention instruction tuning fails to generalize across domains
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:abstention-generalization-failure
  type: mechanism
  status: canonical
cause: '[[instruction-tuning]] for [[abstention]] on a narrow, homogeneous set of refusal expressions and task formats'
effect: Abstention ability does not generalize to new domains or LLMs
polarity: prevents
related:
- '[[2407.18418--know-your-limits-abstention-survey]]'
- '[[instruction-tuning]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[2407.18418--know-your-limits-abstention-survey]]'
  target_id: paper:2407.18418
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
---

When abstention training data covers only a limited range of question types and refusal formats, the model learns surface patterns (specific phrasing, topic cues) rather than a general policy of abstaining when uncertain. The abstention survey (arXiv:2407.18418) synthesizes evidence across multiple papers showing that models trained on narrow abstention datasets consistently fail when evaluated on new domains or when the trained behavior is transferred to a different base model. Diversity of abstention training data, in both domain and refusal format, appears necessary for generalization.
