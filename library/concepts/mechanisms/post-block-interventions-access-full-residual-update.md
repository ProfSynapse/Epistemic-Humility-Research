---
aliases:
- Post-block steering accesses the full residual update
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:post-block-interventions-access-full-residual-update
  type: mechanism
  status: canonical
cause: "[[post-block-activation-steering]] intervenes after attention, the MLP, and the residual connection."
effect: "The learned activation update can express effects that an intervention on an isolated sublayer cannot access."
polarity: enables
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[post-block-activation-steering]]'
- '[[activation-steering]]'
relationships:
- type: supported_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[post-block-activation-steering]]'
  target_id: method:post-block-activation-steering
  confidence: high
- type: related_to
  target: '[[activation-steering]]'
  target_id: method:activation-steering
  confidence: high
---

The theoretical analysis identifies the post-block output as the most
expressive tested locus because it includes all residual-stream contributions.
The experiments show smaller performance gaps there than at pre-MLP and
post-MLP intervention sites.
