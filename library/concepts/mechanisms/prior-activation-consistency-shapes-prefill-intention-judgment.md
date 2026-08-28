---
aliases:
- Cached intention representations influence prefill acceptance
- Prior concept state changes whether a forced output seems intentional
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:prior-activation-consistency-shapes-prefill-intention-judgment
  type: mechanism
  status: canonical
cause: "A concept vector matching an artificial prefill is injected into the model's activations before the forced response appears."
effect: "The model is less likely to disavow the forced word as accidental, consistent with checking it against a cached prior intention representation."
polarity: decreases
related:
- '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
- '[[introspective-awareness]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
  target_id: paper:lindsey-2025-introspection
  confidence: high
- type: related_to
  target: '[[introspective-awareness]]'
  target_id: term:introspective-awareness
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

The apology-rate effect required a concept that matched the prefilled word and an injection before the prefill. Random-concept injection and injection during the later intention question did not produce the same reduction. The effective layer was earlier than the best layer for direct injected-thought reporting.
