---
aliases:
- Preventative steering cancels finetuning-induced trait drift
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:preventative-steering-cancels-trait-drift
  type: mechanism
  status: canonical
cause: "Adding the persona vector to hidden states during fine-tuning training steps ([[preventative-steering]]) to counteract the gradient's tendency to shift activations along that direction"
effect: "Trait acquisition is suppressed while domain-specific learning proceeds; MMLU accuracy is better preserved than with inference-time vector subtraction"
polarity: prevents
related:
- '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
- '[[persona-vectors]]'
- '[[preventative-steering]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2507.21509--persona-vectors-monitoring-controlling-character-traits-language]]'
  target_id: paper:2507.21509
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[preventative-steering]]'
  target_id: method:preventative-steering
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
---

By injecting the persona vector as an additive perturbation to hidden states during each gradient update, preventative steering makes the model's internal representation temporarily appear to already express the trait, reducing the gradient signal that would push it further in that direction. The persona-vectors paper (arXiv:2507.21509) shows this training-time intervention suppresses trait acquisition more effectively than subtracting the vector at inference time while preserving MMLU accuracy better. The advantage arises because training-time steering shapes the weight updates directly rather than patching activations post-hoc.
