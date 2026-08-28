---
aliases:
- Representation Tuning
- representation fine-tuning
- activation-vector tuning
- activation similarity tuning
- weights-level behavior control without inference hooks
tags:
- kg/method
- concept
- method
kg:
  id: method:representation-tuning
  type: method
  status: canonical
area: methods
related:
- '[[2409.06927--representation-tuning]]'
- '[[activation-steering]]'
- '[[difference-in-means]]'
- '[[supervised-finetuning]]'
relationships:
- type: proposed_by
  target: '[[2409.06927--representation-tuning]]'
  target_id: paper:2409.06927
  confidence: high
- type: derived_from
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: derived_from
  target: '[[difference-in-means]]'
  target_id: method:difference-in-means
  confidence: high
- type: variation_of
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

Representation tuning fine-tunes model parameters with a joint objective that aligns selected residual-stream activations to a target behavioral vector while retaining a lower-weight token cross-entropy loss. The target vector is obtained from contrastive activation differences, and tuning can focus on selected layers and modules.

**Why it matters here:** It is an explicit weights-level route for making generation express a previously identified internal behavioral direction without an inference-time hook.

**Lineage:** It internalizes directions derived by [[activation-steering]] and [[difference-in-means]] through a modified [[supervised-finetuning]] objective.
