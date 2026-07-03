---
aliases:
- Non-dominant directions regulate the dominant refusal direction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:non-dominant-directions-regulate-refusal
  type: mechanism
  status: canonical
cause: "Suppression of non-dominant orthogonal components in the [[safety-residual-space]]"
effect: "Reduction in model refusal rate on harmful queries even when the [[dominant-refusal-direction]] is left intact"
polarity: decreases
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[safety-residual-space]]'
- '[[dominant-refusal-direction]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: related_to
  target: '[[safety-residual-space]]'
  target_id: term:safety-residual-space
- type: related_to
  target: '[[dominant-refusal-direction]]'
  target_id: term:dominant-refusal-direction
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
---

Although a single dominant direction accounts for the largest fraction of the safety activation shift, the full refusal mechanism involves additional orthogonal components in the safety residual space that modulate the dominant direction's effect. When these non-dominant components are ablated, refusal rates on harmful queries decline even though the dominant direction remains present (arXiv:2502.09674). This reveals a regulatory relationship in which lower-variance directions gate or amplify the principal refusal signal, so complete jailbreaking requires suppressing the full multi-dimensional cone rather than only the dominant axis.
