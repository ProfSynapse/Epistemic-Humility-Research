---
aliases:
- Token consistency outperforms activation consistency on jailbreaks
- BCT reduces jailbreaks more than ACT
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:token-consistency-outperforms-activation-consistency-on-jailbreaks
  type: mechanism
  status: canonical
cause: "BCT directly trains clean-prompt refusal tokens on wrapped unsafe prompts, while ACT only aligns prompt activations at matching suffix positions."
effect: "BCT produces a larger reduction in jailbreak attack success, while ACT generally preserves benign answering better."
polarity: trades_off
related:
- '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
- '[[bias-augmented-consistency-training]]'
- '[[activation-consistency-training]]'
relationships:
- type: supported_by
  target: '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
  target_id: paper:2510.27062
  confidence: high
- type: related_to
  target: '[[bias-augmented-consistency-training]]'
  target_id: method:bias-augmented-consistency-training
  confidence: high
- type: related_to
  target: '[[activation-consistency-training]]'
  target_id: method:activation-consistency-training
  confidence: high
---

The direction is consistent across the reported model panel. The authors note that ACT's shared-suffix restriction cannot directly align wrapper tokens inserted at the prompt end.
