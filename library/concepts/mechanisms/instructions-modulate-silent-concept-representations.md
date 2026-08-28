---
aliases:
- Think instructions strengthen internal concept representations
- Models can regulate nonverbalized concept activation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instructions-modulate-silent-concept-representations
  type: mechanism
  status: canonical
cause: "A prompt instructs or incentivizes a model to think about an unrelated concept while reproducing a fixed sentence."
effect: "Residual-stream activations align more strongly with that concept than under suppression instructions, even when the output sentence is unchanged."
polarity: increases
related:
- '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
- '[[activation-steering]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[lindsey-2025--emergent-introspective-awareness-large-language-models]]'
  target_id: paper:lindsey-2025-introspection
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: high
---

Every tested model showed stronger target-vector alignment under think than do-not-think instructions. Opus 4 and 4.1 returned the unrelated concept representation to baseline by the final layer, which separates internal modulation from an overt impulse to emit the concept word.
