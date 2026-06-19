---
aliases:
- CAA steers alignment behaviors
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:contrastive-activation-addition-steers-alignment-behaviors
  type: mechanism
  status: canonical
cause: "A [[contrastive-activation-addition]] vector is computed from contrasting behavior examples."
effect: "Alignment-relevant behaviors shift during evaluation or generation."
polarity: enables
related:
- '[[2312.06681--steering-llama-2-via-contrastive-activation-addition]]'
- '[[contrastive-activation-addition]]'
- '[[activation-addition]]'
- '[[sycophancy]]'
relationships:
- type: supported_by
  target: '[[2312.06681--steering-llama-2-via-contrastive-activation-addition]]'
  target_id: paper:2312.06681
  confidence: high
- type: related_to
  target: '[[contrastive-activation-addition]]'
  target_id: method:contrastive-activation-addition
  confidence: high
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
---

Contrastive activation addition uses contrast pairs to build steering vectors
for alignment-relevant behaviors, including behaviors such as sycophancy.
