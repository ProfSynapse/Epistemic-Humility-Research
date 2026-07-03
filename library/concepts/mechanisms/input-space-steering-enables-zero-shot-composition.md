---
aliases:
- Input-Space Operation Enables Zero-Shot Behavior Composition
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:input-space-steering-enables-zero-shot-composition
  type: mechanism
  status: canonical
cause: "Behavior representations living in the input token embedding space rather than the activation space, with all LLM weights kept frozen during composition token learning"
effect: "Zero-shot [[compositional-generalization]] to unseen behavior pairs and counts without model weight modification or retraining of individual behavior representations"
polarity: enables
related:
- '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
- '[[compositional-steering-tokens]]'
- '[[activation-steering]]'
- '[[compositional-generalization]]'
relationships:
- type: supported_by
  target: '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
  target_id: paper:2601.05062
  confidence: high
- type: related_to
  target: '[[compositional-steering-tokens]]'
  target_id: method:compositional-steering-tokens
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
- type: related_to
  target: '[[compositional-generalization]]'
  target_id: term:compositional-generalization
---

Activation-space steering vectors must be re-estimated for every new composition because they interact non-linearly with layer weights; placing behavior representations in the input token-embedding space instead keeps them in a domain where the model's frozen attention and feedforward operations are already trained to compose tokens. This architectural choice means that a new behavior combination is simply a new token sequence, which the model handles through its pre-trained contextual reasoning without requiring weight updates (arXiv:2601.05062). The result is zero-shot compositional generalisation to behavior pairings and counts not seen during composition-token training.
