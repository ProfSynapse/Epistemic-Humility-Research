---
aliases:
- Mine/Yours encoding
- relative player encoding
- player-relative board state
- Relative Board State Encoding (Mine/Yours)
tags:
- kg/term
- concept
- term
kg:
  id: term:relative-board-encoding
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2309.00941--emergent-linear-representations-world-models]]'
- '[[emergent-world-model]]'
- '[[linear-probe]]'
- '[[othello-gpt]]'
relationships:
- type: proposed_by
  target: '[[2309.00941--emergent-linear-representations-world-models]]'
  target_id: paper:2309.00941
  confidence: high
- type: derived_from
  target: '[[emergent-world-model]]'
  target_id: term:emergent-world-model
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[othello-gpt]]'
  target_id: model:othello-gpt
---

Relative board encoding is the finding that OthelloGPT represents board state
relative to the current player at each timestep (Mine, Yours, Empty) rather
than in absolute piece colours (Black, White, Empty). Because the active player
alternates every move, an absolute-colour encoding would require a non-linear
rotation at each step, whereas Mine/Yours is always a fixed transformation.
Linear probes trained on the Mine/Yours framing achieve approximately 99.4%
accuracy on held-out board states, compared with roughly 75% for probes trained
on Black/White labels, confirming that the model's internal geometry matches the
relative framing.

**Why it matters here:** The result illustrates how the choice of representational
frame determines whether a linear probing test succeeds or fails, a
methodological consideration that carries over to probing for uncertainty or
self-knowledge representations in language models.

**Lineage:** derives from [[emergent-world-model]]; introduced by
[[2309.00941--emergent-linear-representations-world-models]]; probed with
[[linear-probe]] on [[othello-gpt]].
