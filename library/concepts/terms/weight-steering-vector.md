---
aliases:
- weight steering vector
- contrastive weight behavior vector
- behavior direction in weight space
tags:
- kg/term
- concept
- term
kg:
  id: term:weight-steering-vector
  type: term
  status: canonical
area: steering
related:
- '[[2511.05408--steering-language-models-weight-arithmetic]]'
- '[[contrastive-weight-steering]]'
relationships:
- type: proposed_by
  target: '[[2511.05408--steering-language-models-weight-arithmetic]]'
  target_id: paper:2511.05408
  confidence: high
- type: required_by
  target: '[[contrastive-weight-steering]]'
  target_id: method:contrastive-weight-steering
  confidence: high
---

A weight steering vector is the parameter difference between a positive-behavior fine-tune and an opposing negative-behavior fine-tune. In the paper's notation, the pretrained-weight terms cancel, so the vector is the direct difference between the two fine-tuned parameter sets.

**Why it matters here:** The vector provides a persistent weights-level control direction, but it is applied unconditionally rather than being gated by a live internal readout.

**Lineage:** It is a contrastive form of task-vector arithmetic used by [[contrastive-weight-steering]].
