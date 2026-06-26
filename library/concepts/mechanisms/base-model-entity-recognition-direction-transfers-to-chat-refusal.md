---
aliases:
- base-model SAE entity directions steer chat refusal
- chat finetuning repurposes pretrained knowledge-awareness mechanism
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:base-model-entity-recognition-direction-transfers-to-chat-refusal
  type: mechanism
  status: canonical
cause: "Steering the chat model with entity-recognition directions extracted from sparse autoencoders trained only on the base model."
effect: "The chat model's refusal behavior changes accordingly, indicating chat finetuning reused the pretrained entity-recognition mechanism rather than building a new one."
polarity: enables
related:
- '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
- '[[entity-recognition-direction]]'
- '[[refusal-direction]]'
- '[[self-knowledge]]'
relationships:
- type: supported_by
  target: '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
  target_id: paper:2411.14257
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction]]'
  target_id: term:entity-recognition-direction
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
---

Although the sparse autoencoders are trained on the base model, the recovered
entity-recognition directions causally affect the chat model's refusal behavior.
Ferrando et al. read this as chat finetuning repurposing a pre-existing
pretrained knowledge-awareness mechanism, and as evidence that the
known/unknown-entity signal transfers across the base to instruction/chat
training-stage shift. This is the cross-checkpoint transfer analogue relevant to
reading a humility-finetuned model's direction back to (or from) its base.
