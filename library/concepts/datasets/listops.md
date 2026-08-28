---
aliases:
- ListOps
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:listops
  type: dataset
  status: canonical
area: datasets
related:
- '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
- '[[gsm8k]]'
relationships:
- type: used_by
  target: '[[2603.00425--weight-updates-as-activation-shifts-principled-framework]]'
  target_id: paper:2603.00425
  confidence: high
- type: related_to
  target: '[[gsm8k]]'
  target_id: dataset:gsm8k
  confidence: low
---

ListOps is a synthetic benchmark of deeply nested list operations. The paper
uses it as a long-range dependency task in its adaptation comparison.

**Why it matters here:** ListOps exposes whether an intervention site can
control computations that depend on information propagated through attention.

**Lineage:** It is used alongside [[gsm8k]] and other reasoning benchmarks.
