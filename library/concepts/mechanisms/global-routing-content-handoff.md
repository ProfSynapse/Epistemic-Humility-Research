---
aliases:
- Global request dependence decreases while fitted-content dependence persists
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:global-routing-content-handoff
  type: mechanism
  status: canonical
cause: "Moving from prespecified earlier to later layer sets while deleting the fitted global first-versus-second request direction in paired country-continent questions."
effect: "Answer sensitivity to global-route deletion decreases while sensitivity to fitted-content deletion remains larger in Qwen, Gemma, and Llama."
polarity: redistributes
related:
- '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
- '[[routing-content-handoff]]'
- '[[parameter-retrieval-routing]]'
- '[[activation-intervention]]'
relationships:
- type: supported_by
  target: '[[2609.11859--parameters-answers-how-llms-retrieve-use-their]]'
  target_id: paper:2609.11859
  confidence: high
- type: related_to
  target: '[[routing-content-handoff]]'
  target_id: term:routing-content-handoff
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

On 24 held-out country pairs, the earlier-minus-later global-route contrast is positive in all three instruction models, and later content deletion exceeds later global-route deletion in all three (arXiv:2609.11859, Section 6.2; Appendix C.1, Table 5). The result concerns fitted global request directions and does not establish a universal processing stage.
