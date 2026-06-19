---
aliases:
- CAA
- contrastive activation additions
tags:
- kg/method
- concept
- method
kg:
  id: method:contrastive-activation-addition
  type: method
  status: canonical
area: methods
related:
- '[[2312.06681--steering-llama-2-via-contrastive-activation-addition]]'
- '[[activation-addition]]'
- '[[steering-vector]]'
relationships:
- type: proposed_by
  target: '[[2312.06681--steering-llama-2-via-contrastive-activation-addition]]'
  target_id: paper:2312.06681
  confidence: high
- type: derived_from
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: high
- type: uses
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
---

Contrastive activation addition is a steering method that forms activation
directions from paired positive and negative examples, then applies those
directions during model generation or evaluation.

