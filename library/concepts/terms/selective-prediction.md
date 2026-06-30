---
aliases:
- Selective Prediction
- prediction with a reject option
- reject option
- selective classification
tags:
- kg/term
- concept
- term
kg:
  id: term:selective-prediction
  type: term
  status: canonical
area: terms
related:
- '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
- '[[selectivenet]]'
- '[[selective-risk]]'
- '[[abstention]]'
- '[[selective-classification-auc]]'
relationships:
- type: proposed_by
  target: '[[1901.09192--selectivenet-deep-neural-network-integrated-reject-option]]'
  target_id: paper:1901.09192
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: high
- type: related_to
  target: '[[selective-risk]]'
  target_id: metric:selective-risk
  confidence: high
---

Selective prediction is the setting in which a model may abstain ("reject") on
some inputs and is scored only on the subset it chooses to answer (its coverage).
The objective is a risk-coverage tradeoff: minimize error on the covered subset
while maintaining a desired coverage level. Abstention is the discrete decision; a
reject option is the mechanism that produces it.

**Why it matters here:** It is the formal framing of the answer/abstain action
channel in the epistemic-humility experiment: deciding when to answer versus
defer is exactly a learned reject option, and the calibration of the gate is what
the confidence head is meant to drive.

**Lineage:** El-Yaniv and Wiener 2010; instantiated for deep networks by
[[selectivenet]] and measured by [[selective-risk]] and
[[selective-classification-auc]].
