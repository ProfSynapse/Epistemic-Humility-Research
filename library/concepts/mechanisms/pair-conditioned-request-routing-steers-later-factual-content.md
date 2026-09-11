---
aliases:
- Pair-conditioned request reversal steers later fitted knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pair-conditioned-request-routing-steers-later-factual-content
  type: mechanism
  status: canonical
cause: "Reversing a fitted pair-conditioned request component at Qwen layer 32 in natural country-continent questions."
effect: "The answer margin and the layer-36 fitted continent-knowledge score shift toward the paired country's answer, beyond eight equal-length random controls."
polarity: modulates
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[parameter-retrieval-routing]]'
- '[[activation-intervention]]'
relationships:
- type: supported_by
  target: '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
  target_id: paper:2609.11859
  confidence: high
- type: related_to
  target: '[[parameter-retrieval-routing]]'
  target_id: term:parameter-retrieval-routing
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
---

At the fixed Qwen layer-32-to-36 comparison, reversal changes the answer margin by 7.200 [5.422, 8.634] and the fitted knowledge score by 6270.843 [3408.236, 8771.132] (arXiv:2609.11859, Section 3.5, Table 1). Deletion changes the answer margin but its later-knowledge interval crosses zero, so this mechanism records directional steering rather than necessity.
