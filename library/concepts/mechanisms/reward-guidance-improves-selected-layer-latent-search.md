---
aliases:
- reward-derived gradients improve over random selected-layer latent exploration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:reward-guidance-improves-selected-layer-latent-search
  type: mechanism
  status: canonical
cause: "A binary self-verifier's reward is backpropagated through continuation-token log-probabilities instead of using random latent directions."
effect: "Selected-layer latent search reaches higher final-answer accuracy across the evaluated reasoning settings."
polarity: increases
related:
- '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
- '[[gradcuit]]'
- '[[policy-gradient]]'
relationships:
- type: supported_by
  target: '[[2608.02585--gradcuit-credit-assigned-gradient-flow-enables-robust]]'
  target_id: paper:2608.02585
  confidence: high
- type: related_to
  target: '[[gradcuit]]'
  target_id: method:gradcuit
  confidence: high
- type: related_to
  target: '[[policy-gradient]]'
  target_id: term:policy-gradient
  confidence: high
---

Table 3 reports that reward-derived gradients improve average Boxed accuracy
by 2.4 points over random directions across 15 backbone-benchmark settings,
with 14 wins and one tie. The result isolates a benefit from credit guidance
on top of the benefit already supplied by direct latent exploration.
