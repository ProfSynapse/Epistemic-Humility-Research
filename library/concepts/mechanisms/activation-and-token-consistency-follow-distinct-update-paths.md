---
aliases:
- Activation and token consistency follow distinct update paths
- ACT is not BCT in disguise
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:activation-and-token-consistency-follow-distinct-update-paths
  type: mechanism
  status: canonical
cause: "ACT directly minimizes clean-versus-wrapped activation distance, whereas BCT minimizes response-token cross-entropy."
effect: "BCT can increase activation distance and ACT need not reduce the BCT token loss, despite similar sycophancy behavior."
polarity: decouples
related:
- '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
- '[[activation-consistency-training]]'
- '[[bias-augmented-consistency-training]]'
relationships:
- type: supported_by
  target: '[[2510.27062--consistency-training-helps-stop-sycophancy-jailbreaks]]'
  target_id: paper:2510.27062
  confidence: high
- type: related_to
  target: '[[activation-consistency-training]]'
  target_id: method:activation-consistency-training
  confidence: high
- type: related_to
  target: '[[bias-augmented-consistency-training]]'
  target_id: method:bias-augmented-consistency-training
  confidence: high
---

The Gemma 3 4B training traces show that optimizing one consistency objective does not automatically optimize the other. This establishes distinct update behavior, not a complete mechanistic explanation of either trained model.
