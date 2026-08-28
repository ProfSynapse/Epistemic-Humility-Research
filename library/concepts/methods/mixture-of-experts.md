---
aliases:
- Mixture of Experts
- MoE
- mixture-of-experts network
tags:
- kg/method
- concept
- method
kg:
  id: method:mixture-of-experts
  type: method
  status: canonical
area: architectures
related:
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
relationships:
- type: used_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
---

A mixture-of-experts network combines outputs from several expert modules using a gating network. The paper routes supervised terminal-state updates to designated Diamond and Ghost experts.
