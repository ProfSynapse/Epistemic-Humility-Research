---
aliases:
- parallel layers
- running layers in parallel
tags:
- kg/method
- concept
- method
kg:
  id: method:parallel-layer-execution
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2407.09298--transformer-layers-as-painters]]'
- '[[looped-parallel-layers]]'
relationships:
- type: proposed_by
  target: '[[2407.09298--transformer-layers-as-painters]]'
  target_id: paper:2407.09298
  confidence: medium
- type: related_to
  target: '[[looped-parallel-layers]]'
  target_id: method:looped-parallel-layers
---

Parallel layer execution replaces a contiguous span of a frozen pretrained
transformer's middle layers with a single parallel step: each layer in the
span independently reads the same input state, and their outputs are averaged
(or otherwise combined) into one updated state, instead of being applied
sequentially.

**Why it matters here:** Parallel execution tests whether middle-layer
computation requires strict sequential composition or tolerates simultaneous,
order-free application; the paper finds a single parallel pass degrades
performance, motivating [[looped-parallel-layers|looped parallel
execution]] as a way to recover it.

**Lineage:** proposed in arXiv:2407.09298; the base condition that
[[looped-parallel-layers|Looped Parallel]] iterates on.
