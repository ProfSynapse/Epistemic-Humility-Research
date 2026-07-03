---
aliases:
- Pretraining Exposure Forms Persona Directions
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pretraining-exposure-forms-persona-directions
  type: mechanism
  status: canonical
cause: "Exposure to pretraining text under the [[next-token-prediction]] objective in early training checkpoints"
effect: "Linear [[persona-vectors|persona directions]] emerge in residual-stream activations that are usable for steering character traits, even before any alignment fine-tuning"
polarity: enables
related:
- '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
- '[[persona-vectors]]'
- '[[next-token-prediction]]'
- '[[primitives-pretraining]]'
relationships:
- type: supported_by
  target: '[[2605.13329--tracing-persona-vectors-through-llm-pretraining]]'
  target_id: paper:2605.13329
  confidence: high
- type: related_to
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
- type: related_to
  target: '[[next-token-prediction]]'
  target_id: method:next-token-prediction
---

Persona directions are not injected by alignment fine-tuning but arise from the statistical regularities of pretraining text itself. The pretraining-tracing paper (arXiv:2605.13329) extracts persona vectors at intermediate pretraining checkpoints and shows they are already usable for steering at very early checkpoints, long before alignment. This demonstrates that next-token prediction over diverse text forces the model to encode character-trait concepts as linear directions in order to predict trait-consistent continuations, and alignment stages subsequently modulate rather than create these directions.
