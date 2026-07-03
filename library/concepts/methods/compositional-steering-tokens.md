---
aliases:
- steering tokens
- composition token
- <and> token
- input-space behavior steering
tags:
- kg/method
- concept
- method
kg:
  id: method:compositional-steering-tokens
  type: method
  status: canonical
area: steering
related:
- '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
- '[[activation-steering]]'
- '[[lora-dare]]'
relationships:
- type: proposed_by
  target: '[[2601.05062--compositional-steering-large-language-models-steering-tokens]]'
  target_id: paper:2601.05062
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
- type: related_to
  target: '[[lora-dare]]'
  target_id: method:lora-dare
---

Per-behavior trainable input embeddings (one token per behavior) plus a dedicated
composition token, all prepended to LLM inputs at inference time while keeping every
model weight frozen. Behaviors are composed by interleaving behavior embeddings with
the composition token (e.g., [E_x, e_bi, e_and, e_bj]). Because the method operates
in input embedding space rather than activation space or parameter space, zero-shot
composition of unseen behavior pairs is possible without any weight modification.
Training relies on [[compositional-self-distillation]] for the behavior tokens and
[[orthogonality-regularization-steering]] for the composition token.

**Why it matters here:** By externalizing behavioral control to the input space and
enabling principled composition, this method makes it possible to stack
epistemic-humility-relevant behaviors (calibrated hedging, abstention) with
task-completing behaviors without mutual representational interference.

**Lineage:** contrasts with [[activation-steering]] (hidden-state addition) and
[[lora-dare]] (parameter merging) as the input-space alternative in the
multi-behavior steering comparison.
