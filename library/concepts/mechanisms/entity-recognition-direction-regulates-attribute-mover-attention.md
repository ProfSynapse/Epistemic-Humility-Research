---
aliases:
- knowledge-awareness direction disrupts attribute-mover attention heads
- unknown-entity direction blocks entity-attribute attention
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:entity-recognition-direction-regulates-attribute-mover-attention
  type: mechanism
  status: canonical
cause: "The entity-recognition (unknown-entity) direction is active or amplified at the entity token."
effect: "It disrupts the attention of downstream heads that normally move entity attributes to the final token, suppressing attribute recall and thereby preventing hallucinated answers."
polarity: mediates
related:
- '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
- '[[entity-recognition-direction]]'
- '[[mover-head-failure-drives-hallucination]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2411.14257--do-i-know-this-entity-knowledge-awareness]]'
  target_id: paper:2411.14257
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction]]'
  target_id: term:entity-recognition-direction
  confidence: high
- type: related_to
  target: '[[mover-head-failure-drives-hallucination]]'
  target_id: mechanism:mover-head-failure-drives-hallucination
  confidence: medium
---

Ferrando et al.'s mechanistic analysis finds the entity-recognition directions
act by regulating attention: an active unknown-entity direction disrupts the
downstream attention heads that typically move entity attributes to the final
token, so the model cannot surface a (possibly fabricated) attribute. This gives
an attention-level account of how a knowledge-awareness signal translates into
the refuse-versus-hallucinate behavior, and connects the direction to
attribute-mover / mover-head accounts of hallucination.
