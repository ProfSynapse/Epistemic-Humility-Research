---
aliases:
- A linear steering operator can be absorbed into output weights
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:linear-steering-operator-can-be-embedded-in-output-weights
  type: mechanism
  status: canonical
cause: "A linear activation projection or amplification is algebraically composed with residual-stream output matrices."
effect: "[[embedded-activation-steering]] produces the same linear transformation without an inference-time hook."
polarity: enables
related:
- '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
- '[[embedded-activation-steering]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2608.24988--does-fine-tuning-undo-activation-steering-behavioural]]'
  target_id: paper:2608.24988
  confidence: high
- type: related_to
  target: '[[embedded-activation-steering]]'
  target_id: method:embedded-activation-steering
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

The paper writes projection and amplification operators directly into
attention-output and MLP-down-projection matrices. Constant activation offsets
cannot be absorbed in the same way because they do not depend linearly on the
incoming activation.
