---
aliases:
- dominant direction
- dominant safety direction
- dominant component
tags:
- kg/term
- concept
- term
kg:
  id: term:dominant-refusal-direction
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[refusal-direction]]'
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[safety-residual-space]]'
relationships:
- type: proposed_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: derived_from
  target: '[[safety-residual-space]]'
  target_id: term:safety-residual-space
- type: variation_of
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
  note: "Specific construction (first singular vector of the safety-residual space) of the generic refusal direction."
---

The dominant refusal direction is the first (largest) singular vector of the
[[safety-residual-space]], representing the axis along which safety fine-tuning
moves hidden states most strongly. Projection of a hidden state onto this
direction is sufficient to predict model refusal behavior with high accuracy
from around layer 15 onward, matching the performance of a separately trained
probe vector. Non-dominant orthogonal directions from the same decomposition
encode distinct secondary features (hypothetical narrative framing,
role-playing persona, harmful topic recognition) that modulate the magnitude
of the dominant direction's effect rather than independently driving refusal.

**Why it matters here:** If the dominant refusal direction is partially
confounded with the epistemic caution signal (the doubt-caution axis studied
here), then ablating or suppressing it to reduce over-refusal will
inadvertently damage calibrated hesitation; understanding the geometry is a
prerequisite for surgical interventions that decouple the two.

**Lineage:** derives from [[safety-residual-space]] via SVD; contrast with the
single-vector view produced by [[difference-in-means]], which the dominant
direction formally supersedes.
