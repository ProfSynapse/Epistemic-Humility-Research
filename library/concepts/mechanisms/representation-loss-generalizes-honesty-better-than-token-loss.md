---
aliases:
- Activation-aligned tuning generalizes honesty better than token-only fine-tuning
- Representation tuning transfers honesty behavior to open-ended prompts
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:representation-loss-generalizes-honesty-better-than-token-loss
  type: mechanism
  status: canonical
cause: "Training directly aligns hidden activations to an honesty or dishonesty direction rather than optimizing only answer tokens."
effect: "Behavioral changes generalize to naturalistic honesty and instrumental-lying prompts more reliably than token-only fine-tuning."
polarity: increases
related:
- '[[2409.06927--representation-tuning]]'
- '[[representation-tuning]]'
- '[[supervised-finetuning]]'
relationships:
- type: supported_by
  target: '[[2409.06927--representation-tuning]]'
  target_id: paper:2409.06927
  confidence: high
- type: related_to
  target: '[[representation-tuning]]'
  target_id: method:representation-tuning
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
---

On two small open-ended evaluation sets, representation-tuned models showed significant honesty-direction effects against the base model for both raters. Token-only tuned models did not differ significantly from the base model, while perplexity on WikiText remained similar to the untuned model.
