---
aliases:
- Request-direction construction changes late deletion effects
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:request-direction-construction-modulates-causal-effect
  type: mechanism
  status: canonical
cause: "Replacing a global request direction with a pair-conditioned direction while holding the paired Qwen task, late layers, weights, precision, state position, and evaluation pairs fixed."
effect: "Late deletion changes from less damaging than the strongest random control to strongly consequential, with direction orientation and intervention length changing together."
polarity: modulates
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[parameter-retrieval-routing]]'
- '[[routing-content-handoff]]'
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
  target: '[[routing-content-handoff]]'
  target_id: term:routing-content-handoff
  confidence: high
- type: related_to
  target: '[[activation-intervention]]'
  target_id: method:activation-intervention
  confidence: high
---

With the fit center, global late deletion has effect -0.195 [-0.251, -0.160], whereas pair-conditioned deletion has effect 3.092 [2.464, 3.624] (arXiv:2609.11859, Section 6.4, Table 3). Mean write lengths are 16.38 and 80.47, respectively, so the evidence identifies dependence on the deletion definition but does not isolate direction orientation from intervention magnitude (Appendix F.2).
