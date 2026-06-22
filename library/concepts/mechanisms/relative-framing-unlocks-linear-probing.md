---
aliases:
- Relative player framing unlocks linear probing of world models
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:relative-framing-unlocks-linear-probing
  type: mechanism
  status: canonical
cause: Framing board state relative to the current player (Mine/Yours/Empty) rather than absolute colour (Black/White/Empty)
effect: Linear probes achieve approximately 99.4% accuracy on board state classification (versus approximately 75% for absolute colour linear probes), matching non-linear probe performance
polarity: increases
related:
- '[[2309.00941--emergent-linear-representations-world-models]]'
- '[[othello-gpt]]'
- '[[emergent-world-model]]'
- '[[linear-probe]]'
- '[[relative-board-encoding]]'
relationships:
- type: supported_by
  target: '[[2309.00941--emergent-linear-representations-world-models]]'
  target_id: paper:2309.00941
  confidence: high
- type: related_to
  target: '[[othello-gpt]]'
  target_id: model:othello-gpt
- type: related_to
  target: '[[emergent-world-model]]'
  target_id: term:emergent-world-model
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
- type: related_to
  target: '[[relative-board-encoding]]'
  target_id: term:relative-board-encoding
---

[[othello-gpt]] trained solely on legal move sequences develops an internal representation of board state, but the geometry of that representation is player-relative rather than colour-absolute (arXiv:2309.00941). Linear probes using absolute Black/White/Empty labels achieve only approximately 75% accuracy, while probes using player-relative Mine/Yours/Empty labels achieve approximately 99.4% -- on par with non-linear probes using either framing. This framing-dependence reveals that the [[emergent-world-model]] encodes the board from the perspective of the player-to-move, a choice that is implicit in the training data distribution (sequence of alternating moves) rather than explicitly supervised.
