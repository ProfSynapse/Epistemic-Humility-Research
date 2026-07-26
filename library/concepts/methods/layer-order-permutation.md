---
aliases:
- reversed layer order
- random layer order
- layer reordering
tags:
- kg/method
- concept
- method
kg:
  id: method:layer-order-permutation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
relationships:
- type: proposed_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: medium
---

Layer-order permutation runs a frozen pretrained transformer's middle layers
in an order different from the one they were trained in -- either reversed
(last-to-first) or a random permutation -- while leaving the first and last
few layers in their original positions.

**Why it matters here:** Sensitivity to layer order is used to probe how much
middle-layer computation depends on trained sequential dependencies versus a
shared, order-tolerant representation space; the paper finds mathematical and
reasoning benchmarks (ARC, GSM8K) degrade more under reordering than semantic
benchmarks (HellaSwag, WinoGrande), indicating reasoning tasks rely more
heavily on preserved layer order.

**Lineage:** proposed in arXiv:2407.09298 alongside
[[parallel-layer-execution|parallel layer execution]] as a family of
order- and structure-perturbing interventions on the middle-layer block.
