---
aliases:
- Gemma-3-1B
- Gemma 3 1B
tags:
- kg/model
- concept
- model
kg:
  id: model:gemma-3-1b
  type: model
  status: canonical
area: models
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[gemma-3-4b-it]]'
relationships:
- type: studied_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[gemma-3-4b-it]]'
  target_id: model:gemma-3-4b-it
  confidence: high
---

Gemma 3 1B is a one-billion-parameter model in Google's Gemma 3 family. The
paper evaluates post-block steering and joint adaptation on this model.

**Why it matters here:** It supplies a small-model test of whether the proposed
intervention locus generalizes across model families.

**Lineage:** It belongs to the same family as [[gemma-3-4b-it]].
