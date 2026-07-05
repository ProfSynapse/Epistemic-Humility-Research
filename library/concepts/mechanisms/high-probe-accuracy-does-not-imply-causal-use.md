---
aliases:
- High Probe Accuracy Does Not Imply Causal Use
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:high-probe-accuracy-does-not-imply-causal-use
  type: mechanism
  status: canonical
cause: A property being linearly decodable from a neural representation (high [[linear-probe]] accuracy)
effect: No guarantee that the property is causally used by the model for its primary task; phrase-boundary features show ~85% probe accuracy yet amnesic removal has zero LM accuracy impact
polarity: prevents
related:
- '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
- '[[amnesic-probing]]'
- '[[linear-probe]]'
- '[[probing-accuracy-task-importance-disconnect]]'
relationships:
- type: supported_by
  target: '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
  target_id: paper:2006.00995
  confidence: high
- type: related_to
  target: '[[amnesic-probing]]'
  target_id: method:amnesic-probing
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[probing-accuracy-task-importance-disconnect]]'
  target_id: term:probing-accuracy-task-importance-disconnect
contradicted-by: []
---

[[amnesic-probing]] in arXiv:2006.00995 reveals a fundamental dissociation: phrase-boundary features are linearly decodable from BERT representations with ~85% accuracy, yet removing them via INLP nullspace projection has zero effect on the model's language-modeling accuracy. This shows that high probing accuracy reflects encoding, not causal use, and that standard [[linear-probe]] experiments cannot by themselves establish that a property is task-relevant. Causal use must be verified through intervention, not correlation.
