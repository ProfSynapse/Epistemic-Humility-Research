---
aliases:
- INLP Erasure Reveals Property Causal Utility
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:inlp-erasure-reveals-property-causal-utility
  type: mechanism
  status: canonical
cause: "Removing a linguistic property via [[inlp]] nullspace projection from BERT representations"
effect: "Catastrophic LM accuracy drops for causally used properties (dependency labels: -87 pts, fine-grained POS: -81.8 pts) vs. negligible drops for unused properties (phrase markers: ~0 pts), separating encoded-but-unused from genuinely task-driving information"
polarity: enables
related:
- '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
- '[[amnesic-probing]]'
- '[[inlp]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2006.00995--amnesic-probing-behavioral-explanation-amnesic-counterfactuals]]'
  target_id: paper:2006.00995
  confidence: high
- type: related_to
  target: '[[amnesic-probing]]'
  target_id: method:amnesic-probing
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
contradicted-by: []
---

[[amnesic-probing]] uses [[inlp]] erasure as an intervention to test causal utility: when dependency labels are removed from BERT representations, LM accuracy collapses by 87 points; when phrase-boundary markers are removed, accuracy is unchanged. This differential response reveals which properties are load-bearing for the model's computation versus merely correlated with the input. The method is introduced and validated in arXiv:2006.00995, establishing amnesic probing as a diagnostic that goes beyond standard probing accuracy.
